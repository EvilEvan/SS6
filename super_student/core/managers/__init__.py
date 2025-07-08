"""Core.managers subpackage.

Eventually each manager will reside in its own module/file inside this
folder. For now we just re-export the classes from *universal_class* so
that new-style imports work:

    from super_student.core.managers import GlassShatterManager
"""

from __future__ import annotations

# Re-import MultiTouchManager from the local module which now owns the
# implementation.  The remaining managers are still provided by the
# legacy *universal_class* file until they are migrated.

from .multi_touch import MultiTouchManager  # noqa: F401
from .glass_shatter import GlassShatterManager  # noqa: F401
from universal_class import (
    HUDManager,
    CheckpointManager,
    FlamethrowerManager,
    CenterPieceManager,
)

__all__ = [
    "GlassShatterManager",
    "HUDManager",
    "MultiTouchManager",
    "CheckpointManager",
    "FlamethrowerManager",
    "CenterPieceManager",
]