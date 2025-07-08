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

from .glass_shatter import GlassShatterManager  # noqa: F401
from .multi_touch import MultiTouchManager  # noqa: F401
from .hud import HUDManager  # noqa: F401
from .checkpoint import CheckpointManager  # noqa: F401
from .flamethrower import FlamethrowerManager  # noqa: F401
from .center_piece import CenterPieceManager  # noqa: F401
# Remaining legacy exports can be dropped once all managers are migrated.

__all__ = [
    "GlassShatterManager",
    "HUDManager",
    "MultiTouchManager",
    "CheckpointManager",
    "FlamethrowerManager",
    "CenterPieceManager",
]