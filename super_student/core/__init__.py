"""Core engine subpackage.

Contains low-level, game-agnostic helpers and managers.
During the transition most implementations live in *universal_class* ‑ they
are re-exported here to allow the new import path to work immediately.
"""

from __future__ import annotations

# Re-export managers for the transition phase.
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