"""Production WSGI entrypoint preserving the existing p0_runtime application."""
from __future__ import annotations

import os
from urllib.parse import urlparse

from werkzeug.middleware.proxy_fix import ProxyFix

import app as legacy_module
from p0_runtime import app as _app


def _require(value: str, name: str) -> str:
    if not value:
        raise RuntimeError(f"{name} is required in production")
    return value


if os.getenv("FLASK_ENV", "production").lower() == "production":
    _require(os.getenv("SECRET_KEY", ""), "SECRET_KEY")
    _require(os.getenv("JWT_SECRET_KEY", ""), "JWT_SECRET_KEY")

    # Remove source-code fallback credentials from the production runtime.
    legacy_module.TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    legacy_module.TWILIO_API_KEY = os.getenv("TWILIO_API_KEY", "")
    legacy_module.TWILIO_API_SECRET = os.getenv("TWILIO_API_SECRET", "")
    legacy_module.TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
    legacy_module.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    legacy_module.INTERAKT_KEY = os.getenv("INTERAKT_API_KEY", "")
    legacy_module.PRASHANT_NUMBER = os.getenv("PRASHANT_NUMBER", "")
    legacy_module.PRASHANT_WA = os.getenv("PRASHANT_WHATSAPP", "")
    legacy_module.UPLOAD_PASSWORD = os.getenv("UPLOAD_PASSWORD", "")

    base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if base_url:
        parsed = urlparse(base_url)
        legacy_module.get_host = lambda: parsed.netloc

# Trust one reverse proxy hop (NGINX/Hostinger) so request scheme/host data
# is correct behind HTTPS without modifying p0_runtime.py itself.
_app.wsgi_app = ProxyFix(_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)


@_app.after_request
def production_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    if os.getenv("FLASK_ENV", "production").lower() == "production":
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    return response


app = _app
