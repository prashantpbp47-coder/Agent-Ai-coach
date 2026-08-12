"""Non-destructive runtime wrapper for the existing Priya AI Flask app."""

from app import app as legacy_app
from foundation import (
    register_foundation,
    register_p1_domains,
    register_p2_quote_bridge,
    register_p3_providers,
    register_p4_rm_command_center,
    register_p5_rm_planner,
    register_p6_agent_inbox,
    register_p7_rm_target_marketing,
    register_p8_messaging,
    register_p9_document_intelligence,
    register_p10_followup_renewal,
    register_p11_automation_bi,
)

# Preserve legacy routes and add the authenticated P0-P11 platform APIs.
app = register_foundation(legacy_app)
app = register_p1_domains(app)
app = register_p2_quote_bridge(app)
app = register_p3_providers(app)
app = register_p4_rm_command_center(app)
app = register_p5_rm_planner(app)
app = register_p6_agent_inbox(app)
app = register_p7_rm_target_marketing(app)
app = register_p8_messaging(app)
app = register_p9_document_intelligence(app)
app = register_p10_followup_renewal(app)
app = register_p11_automation_bi(app)


@app.get('/r/<slug>')
def public_referral(slug):
    from foundation.p5_routes import public_referral as handler
    return handler(slug)
