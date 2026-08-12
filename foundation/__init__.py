"""PartnersHub AI foundation package."""

from .bootstrap import register_foundation
from .domain_routes import bp as domain_bp
from .p2_quote_bridge import bp as quote_bridge_bp
from .p3_provider_routes import bp as provider_bp
from .rm_routes import bp as rm_bp
from .p5_routes import bp as p5_bp
from .p6_routes import bp as p6_bp
from .p7_routes import bp as p7_bp
from .p8_routes import bp as p8_bp
from .p9_routes import bp as p9_bp
from .p10_routes import bp as p10_bp
from .p11_routes import bp as p11_bp


def register_p1_domains(app): app.register_blueprint(domain_bp); return app
def register_p2_quote_bridge(app): app.register_blueprint(quote_bridge_bp); return app
def register_p3_providers(app): app.register_blueprint(provider_bp); return app
def register_p4_rm_command_center(app): app.register_blueprint(rm_bp); return app
def register_p5_rm_planner(app): app.register_blueprint(p5_bp); return app
def register_p6_agent_inbox(app): app.register_blueprint(p6_bp); return app
def register_p7_rm_target_marketing(app): app.register_blueprint(p7_bp); return app
def register_p8_messaging(app): app.register_blueprint(p8_bp); return app
def register_p9_document_intelligence(app): app.register_blueprint(p9_bp); return app
def register_p10_followup_renewal(app): app.register_blueprint(p10_bp); return app
def register_p11_automation_bi(app): app.register_blueprint(p11_bp); return app

__all__ = ["register_foundation","register_p1_domains","register_p2_quote_bridge","register_p3_providers","register_p4_rm_command_center","register_p5_rm_planner","register_p6_agent_inbox","register_p7_rm_target_marketing","register_p8_messaging","register_p9_document_intelligence","register_p10_followup_renewal","register_p11_automation_bi"]
