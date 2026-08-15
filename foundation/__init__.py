"""PartnersHub AI foundation package."""

from .bootstrap import register_foundation
from .domain_routes import bp as domain_bp


def register_p1_domains(app):
    app.register_blueprint(domain_bp)
    return app


__all__ = ["register_foundation", "register_p1_domains"]
