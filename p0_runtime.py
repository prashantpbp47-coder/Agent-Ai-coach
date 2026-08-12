"""Non-destructive runtime wrapper for the existing Priya AI Flask app."""

from app import app as legacy_app
from foundation import register_foundation

# Preserve every existing route and behavior; only add P0 routes/extensions.
app = register_foundation(legacy_app)
