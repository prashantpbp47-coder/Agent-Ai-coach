"""Non-destructive runtime wrapper for the existing Priya AI Flask app."""

from app import app as legacy_app
from foundation import (
    register_foundation,
    register_p1_domains,
    register_p2_quote_bridge,
    register_p3_providers,
    register_p4_rm_command_center,
)

# Preserve legacy routes and add the authenticated P0-P4 platform APIs.
app = register_foundation(legacy_app)
app = register_p1_domains(app)
app = register_p2_quote_bridge(app)
app = register_p3_providers(app)
app = register_p4_rm_command_center(app)
