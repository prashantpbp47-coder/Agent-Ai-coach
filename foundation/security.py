import os
from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt
from flask import g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from .db import db
from .models import Permission, Role, User

JWT_ALGORITHM = "HS256"


def jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be set and at least 32 characters")
    return secret


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def issue_token(user: User, expires_hours: int = 12) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": user.id, "iat": now, "exp": now + timedelta(hours=expires_hours), "type": "access"}
    return jwt.encode(payload, jwt_secret(), algorithm=JWT_ALGORITHM)


def current_user() -> User | None:
    return getattr(g, "current_user", None)


def load_user_from_token() -> User | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(auth[7:].strip(), jwt_secret(), algorithms=[JWT_ALGORITHM])
        user = db.session.get(User, payload.get("sub"))
        if user and user.is_active:
            g.current_user = user
            return user
    except (jwt.PyJWTError, RuntimeError):
        return None
    return None


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not load_user_from_token():
            return jsonify({"error": "authentication_required"}), 401
        return fn(*args, **kwargs)
    return wrapper


def user_has_role(user: User, role_name: str) -> bool:
    return any(role.name == role_name for role in user.roles)


def user_has_permission(user: User, permission_code: str) -> bool:
    return any(permission_code == permission.code for role in user.roles for permission in role.permissions)


def require_permission(permission_code: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = load_user_from_token()
            if not user:
                return jsonify({"error": "authentication_required"}), 401
            if not user_has_permission(user, permission_code) and not user_has_role(user, "ADMIN"):
                return jsonify({"error": "forbidden", "required_permission": permission_code}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = load_user_from_token()
            if not user:
                return jsonify({"error": "authentication_required"}), 401
            if not any(user_has_role(user, role) for role in roles):
                return jsonify({"error": "forbidden", "required_roles": list(roles)}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def seed_rbac():
    """Idempotently seed the platform roles and baseline permissions."""
    role_names = {
        "AGENT": "Insurance partner/agent",
        "RM": "Relationship manager",
        "MASTER_AGENT": "Master agent / team lead",
        "ADMIN": "Platform administrator",
    }
    permissions = [
        ("agents:read", "Read agent records"), ("agents:write", "Create/update agent records"),
        ("customers:read", "Read customer records"), ("customers:write", "Create/update customer records"),
        ("leads:read", "Read leads"), ("leads:write", "Create/update leads"),
        ("quotes:read", "Read quotes"), ("quotes:write", "Create/update quotes"),
        ("policies:read", "Read policies"), ("policies:write", "Create/update policies"),
        ("renewals:read", "Read renewals"), ("renewals:write", "Create/update renewals"),
        ("reports:read", "Read reports"), ("admin:manage", "Manage platform configuration"),
    ]
    role_map = {}
    for name, description in role_names.items():
        role = db.session.execute(db.select(Role).filter_by(name=name)).scalar_one_or_none()
        if not role:
            role = Role(name=name, description=description)
            db.session.add(role)
        role_map[name] = role
    permission_map = {}
    for code, description in permissions:
        permission = db.session.execute(db.select(Permission).filter_by(code=code)).scalar_one_or_none()
        if not permission:
            permission = Permission(code=code, description=description)
            db.session.add(permission)
        permission_map[code] = permission
    db.session.flush()
    role_permissions = {
        "AGENT": {"agents:read", "customers:read", "customers:write", "leads:read", "leads:write", "quotes:read", "quotes:write", "policies:read", "renewals:read"},
        "RM": set(permission_map),
        "MASTER_AGENT": set(permission_map) - {"admin:manage"},
        "ADMIN": set(permission_map),
    }
    for role_name, codes in role_permissions.items():
        role_map[role_name].permissions = [permission_map[c] for c in codes]
    db.session.commit()
