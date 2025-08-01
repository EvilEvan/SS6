"""Core engine subpackage.

Contains low-level, game-agnostic helpers and managers.
During the transition most implementations live in *universal_class* ‑ they
are re-exported here to allow the new import path to work immediately.
"""

from __future__ import annotations

# Re-export managers for the transition phase.
from .managers.multi_touch import MultiTouchManager  # noqa: F401
from .managers.glass_shatter import GlassShatterManager  # noqa: F401
from .managers.hud import HUDManager  # noqa: F401
from .managers.checkpoint import CheckpointManager  # noqa: F401
from .managers.flamethrower import FlamethrowerManager  # noqa: F401
from .managers.center_piece import CenterPieceManager  # noqa: F401

__all__ = [
    "GlassShatterManager",
    "HUDManager",
    "MultiTouchManager",
    "CheckpointManager",
    "FlamethrowerManager",
    "CenterPieceManager",
]