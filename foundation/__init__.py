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
from .p12_routes import bp as p12_bp
from .p13_routes import bp as p13_bp
from .p14_routes import bp as p14_bp
from .p15_routes import bp as p15_bp
from .p16_routes import bp as p16_bp
from .p17_routes import bp as p17_bp
from .p18_routes import bp as p18_bp
from .p19_knowledge import p19_bp
from .p20_routes import bp as p20_bp


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
def register_p12_clay_prospect_intelligence(app): app.register_blueprint(p12_bp); return app
def register_p13_bi_reconciliation(app): app.register_blueprint(p13_bp); return app
def register_p14_adaptive_targets(app): app.register_blueprint(p14_bp); return app
def register_p15_priya_ai(app): app.register_blueprint(p15_bp); return app
def register_p16_ai_provider(app): app.register_blueprint(p16_bp); return app
def register_p17_priya_messaging(app): app.register_blueprint(p17_bp); return app
def register_p18_campaign_automation(app): app.register_blueprint(p18_bp); return app
def register_p19_knowledge(app): return __import__("foundation.p19_knowledge", fromlist=["register_p19_knowledge"]).register_p19_knowledge(app)
def register_p20_whatsapp(app): app.register_blueprint(p20_bp); return app

__all__ = ["register_foundation","register_p1_domains","register_p2_quote_bridge","register_p3_providers","register_p4_rm_command_center","register_p5_rm_planner","register_p6_agent_inbox","register_p7_rm_target_marketing","register_p8_messaging","register_p9_document_intelligence","register_p10_followup_renewal","register_p11_automation_bi","register_p12_clay_prospect_intelligence","register_p13_bi_reconciliation","register_p14_adaptive_targets","register_p15_priya_ai","register_p16_ai_provider","register_p17_priya_messaging","register_p18_campaign_automation","register_p19_knowledge","register_p20_whatsapp"]
