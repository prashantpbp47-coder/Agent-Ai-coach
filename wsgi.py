"""Production WSGI entrypoint preserving the existing p0_runtime application."""
from werkzeug.middleware.proxy_fix import ProxyFix

from p0_runtime import app as _app

# Trust one reverse proxy hop (NGINX/Hostinger) so request scheme/host data
# is correct behind HTTPS without modifying p0_runtime.py itself.
_app.wsgi_app = ProxyFix(_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app = _app
