"""Core.managers subpackage.

Eventually each manager will reside in its own module/file inside this
folder. For now we just re-export the classes from *universal_class* so
that new-style imports work:

    from super_student.core.managers import GlassShatterManager
"""

from __future__ import annotations

from universal_class import (
    GlassShatterManager,
    HUDManager,
    MultiTouchManager,
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