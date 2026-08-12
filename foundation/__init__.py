"""PartnersHub AI foundation package."""

from .bootstrap import register_foundation
from .domain_routes import bp as domain_bp
from .p2_quote_bridge import bp as quote_bridge_bp
from .p3_provider_routes import bp as provider_bp
from .rm_routes import bp as rm_bp
from .p5_routes import bp as p5_bp


def register_p1_domains(app):
    app.register_blueprint(domain_bp)
    return app


def register_p2_quote_bridge(app):
    app.register_blueprint(quote_bridge_bp)
    return app


def register_p3_providers(app):
    app.register_blueprint(provider_bp)
    return app


def register_p4_rm_command_center(app):
    app.register_blueprint(rm_bp)
    return app


def register_p5_rm_planner(app):
    app.register_blueprint(p5_bp)
    return app


__all__ = [
    "register_foundation",
    "register_p1_domains",
    "register_p2_quote_bridge",
    "register_p3_providers",
    "register_p4_rm_command_center",
    "register_p5_rm_planner",
]
