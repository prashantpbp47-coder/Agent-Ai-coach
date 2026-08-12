"""PartnersHub AI foundation package."""

from .bootstrap import register_foundation
from .domain_routes import bp as domain_bp
from .p2_quote_bridge import bp as quote_bridge_bp


def register_p1_domains(app):
    app.register_blueprint(domain_bp)
    return app


def register_p2_quote_bridge(app):
    app.register_blueprint(quote_bridge_bp)
    return app


__all__ = ["register_foundation", "register_p1_domains", "register_p2_quote_bridge"]
