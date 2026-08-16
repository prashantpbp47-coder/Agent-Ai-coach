"""P8 compatibility module.

P8 schema changes are implemented by the explicit Alembic migration
0004_p8_messaging_delivery. This module is intentionally empty so the
migration environment can import the historical P8 model slot without
inventing duplicate SQLAlchemy models.
"""
