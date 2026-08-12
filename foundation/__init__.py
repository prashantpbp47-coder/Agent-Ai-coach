"""PartnersHub AI P0 foundation package.

This package is intentionally isolated from the existing Priya AI application so
that the current production behavior remains intact while the platform gains a
persistent data/auth foundation incrementally.
"""

from .bootstrap import register_foundation

__all__ = ["register_foundation"]
