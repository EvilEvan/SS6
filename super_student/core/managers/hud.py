"""Heads-up display manager.

Thin wrapper around the legacy implementation while the refactor is in
progress.
"""

from __future__ import annotations

from universal_class import HUDManager as _LegacyHUDManager

class HUDManager(_LegacyHUDManager):
    """Alias class living in the new package namespace."""

    pass