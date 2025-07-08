"""Glass shatter effect manager.

Implementation migrated from the legacy *universal_class.py* file.  The code
is re-exported here to allow gradual refactor without breaking existing
behaviour.
"""

from __future__ import annotations

from universal_class import GlassShatterManager as _LegacyGlassShatterManager


class GlassShatterManager(_LegacyGlassShatterManager):
    """Alias for the legacy implementation placed in its new home."""

    # Inherit everything from the legacy class unchanged.
    pass