"""Multi-touch input manager.

Moved from the legacy *universal_class.py* file to its own module.
"""

from __future__ import annotations

import pygame


class MultiTouchManager:
    """Manage multi-touch events, coordinate conversion and cooldowns."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.active_touches: dict[int, tuple[float, float]] = {}
        self._touch_cooldown: dict[int, int] = {}
        self._cooldown_duration = 50  # milliseconds

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Clear all stored touches and cooldowns."""
        self.active_touches.clear()
        self._touch_cooldown.clear()

    def handle_touch_down(self, event):
        """Convert a `pygame.FINGERDOWN` event into screen coordinates.

        Returns `(touch_id, x, y)` or `None` if the event is suppressed by
        the cooldown logic.
        """
        touch_id = event.finger_id
        touch_x = event.x * self.width
        touch_y = event.y * self.height

        current_time = pygame.time.get_ticks()
        if touch_id in self._touch_cooldown and (
            current_time - self._touch_cooldown[touch_id] < self._cooldown_duration
        ):
            return None

        self._touch_cooldown[touch_id] = current_time
        self.active_touches[touch_id] = (touch_x, touch_y)
        return touch_id, touch_x, touch_y

    def handle_touch_up(self, event):
        """Handle a `pygame.FINGERUP` event."""
        touch_id = event.finger_id
        if touch_id in self.active_touches:
            last_pos = self.active_touches.pop(touch_id)
            return touch_id, last_pos[0], last_pos[1]
        return None

    def handle_touch_motion(self, event):
        """Handle a `pygame.FINGERMOTION` event."""
        touch_id = event.finger_id
        if touch_id in self.active_touches:
            touch_x = event.x * self.width
            touch_y = event.y * self.height
            self.active_touches[touch_id] = (touch_x, touch_y)
            return touch_id, touch_x, touch_y
        return None

    # ------------------------------------------------------------------
    # Utility getters
    # ------------------------------------------------------------------
    def get_active_touches(self):
        """Return a *copy* of the active touches dict."""
        return self.active_touches.copy()

    def get_touch_count(self) -> int:
        return len(self.active_touches)

    def is_touch_active(self, touch_id: int) -> bool:
        return touch_id in self.active_touches

    def clear_touch(self, touch_id: int) -> None:
        """Force-remove a touch (cleanup)."""
        self.active_touches.pop(touch_id, None)
        self._touch_cooldown.pop(touch_id, None)