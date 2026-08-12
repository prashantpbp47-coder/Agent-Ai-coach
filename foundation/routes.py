import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import AuditLog, Role, User
from .security import hash_password, issue_token, require_auth, require_role, seed_rbac, verify_password

bp = Blueprint("p0_foundation", __name__, url_prefix="/api/p0")


@bp.get("/health")
def foundation_health():
    try:
        db.session.execute(select(1))
        return jsonify({"status": "ok", "database": "reachable", "foundation": "p0"})
    except Exception as exc:
        return jsonify({"status": "degraded", "database": "unreachable", "error": str(exc)}), 503


@bp.post("/auth/bootstrap")
def bootstrap_admin():
    """Create the first ADMIN exactly once using a deployment-only bootstrap secret."""
    expected = os.getenv("P0_BOOTSTRAP_TOKEN", "")
    supplied = request.headers.get("X-P0-Bootstrap-Token", "")
    if not expected or supplied != expected:
        return jsonify({"error": "invalid_bootstrap_token"}), 403

    if db.session.execute(select(User.id)).first():
        return jsonify({"error": "bootstrap_already_completed"}), 409

    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    full_name = str(data.get("full_name", "")).strip()
    phone = str(data.get("phone", "")).strip() or None

    if not email or not password or len(password) < 12 or not full_name:
        return jsonify({"error": "email, full_name and password>=12 are required"}), 400

    seed_rbac()
    admin_role = db.session.execute(select(Role).filter_by(name="ADMIN")).scalar_one()
    user = User(email=email, password_hash=hash_password(password), full_name=full_name, phone=phone, roles=[admin_role])
    db.session.add(user)
    db.session.flush()
    db.session.add(AuditLog(action="auth.bootstrap_admin", user_id=user.id, request_id=str(uuid.uuid4())))
    db.session.commit()
    return jsonify({"created": True, "user_id": user.id}), 201


@bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    user = db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none()

    if not user or not user.is_active or not verify_password(user.password_hash, password):
        return jsonify({"error": "invalid_credentials"}), 401

    user.last_login_at = datetime.now(timezone.utc)
    db.session.add(AuditLog(action="auth.login", user_id=user.id, ip_address=request.remote_addr, request_id=str(uuid.uuid4())))
    db.session.commit()
    return jsonify({"access_token": issue_token(user), "token_type": "Bearer", "expires_in_hours": 12})


@bp.get("/auth/me")
@require_auth
def me():
    from .security import current_user
    user = current_user()
    return jsonify({
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "roles": [role.name for role in user.roles],
        "permissions": sorted({p.code for role in user.roles for p in role.permissions}),
    })


@bp.get("/admin/rbac")
@require_role("ADMIN")
def rbac_status():
    roles = db.session.execute(select(Role).order_by(Role.name)).scalars().all()
    return jsonify({
        "roles": [
            {"name": role.name, "permissions": sorted(p.code for p in role.permissions)}
            for role in roles
        ]
    })
