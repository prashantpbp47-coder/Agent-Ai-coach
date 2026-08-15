"""Non-destructive runtime wrapper for the existing Priya AI Flask app."""

from app import app as legacy_app
from foundation import register_foundation, register_p1_domains

# Preserve legacy routes and add the authenticated P0/P1 platform APIs.
app = register_foundation(legacy_app)
app = register_p1_domains(app)
