# History Log

**Model: Claude Sonnet 4 | Date: 2025-01-27 | Logic:**  
- Separated multi-touch functionality from main game file and created new `MultiTouchManager` class in `universal_class.py`.
- Added comprehensive touch event handling with cooldown prevention, coordinate conversion, and touch tracking.
- Updated `SS6.origional.py` to use the new `MultiTouchManager` instead of direct touch handling.
- Removed global `active_touches` variable and replaced with centralized touch management.
- Added touch spam prevention with configurable cooldown duration.
- Reason: Improves code organization, prevents duplicate touch events, and provides reusable multi-touch functionality across the application.

1. Enforced uppercase centre display ("A") in C/L Case mode.  
2. Kept Greek small alpha "α" only when in standard alphabet mode.  
3. Updated falling‑item rendering and HUD target text for consistency.  
4. Clarified prompt rule to explicitly state centre must remain uppercase.  
5. Added summary of changes and reasons for each update.  
6. Fixed rectangle display in shapes mode by applying a 1.5:1 aspect ratio so it no longer renders as a square. #Creator review - Status: Failed
---
History.mdc

gpto4 mini
1. Replaced unsupported 'ɑ' with Greek alpha 'α' in centre, falling items, and HUD.
2. Added explicit rule: centre display remains uppercase (e.g., 'A') for C/L Case.
3. Clarified prompt wording to include "centre must be uppercase" to avoid ambiguity.
4. Reason: enforce design intent and prevent misinterpretation of capitalization rules.

Neglected notes
---

**Model: gpt-4o | Date: 2024-06-12 | Logic:**  
- Rectangle in "shapes" mode now displays as a border-only rectangle with a 1.5:1 aspect ratio (not a square).  
- All shapes in "shapes" mode are now drawn as outlines (no color fill), both for the center target and falling items.  
- Reason: Ensures visual distinction between rectangle and square, and matches prompt requirement for border-only display.

**Model: gpt-4o | Date: 2024-06-12 | Logic:**  
- Fixed UnboundLocalError for `shake_magnitude` in `game_loop` by declaring it as global.  
- Reason: Ensures the function uses the intended global variable for screen shake magnitude.

**Model: gpt-4o | Date: 2024-06-13 | Logic:**  
- Added "Colors" level: introduces a central "Mother Dot" of random color (Blue, Red, Green, Yellow, Purple, Black) that vibrates, then disperses into 100 bouncing dots (25 targets, 75 distractors).
- Only dots matching the Mother Dot color can be clicked and destroyed; distractors are unaffected by clicks.
- Level ends when all 25 target dots are destroyed.
- Reason: Implements a color-matching challenge with animated transitions and clear visual feedback, as per prompt requirements.

**Model: gpt-4o | Date: 2024-06-13 | Logic:**  
- Fixed UnboundLocalError in "colors" mode by removing local assignment of `WIDTH, HEIGHT` (which shadowed the global variables). Now all drawing and logic use the global screen dimensions, preventing runtime errors and ensuring consistent behavior across all modes.

**Model: gpt-4o | Date: 2024-06-13 | Logic:**  
- Fixed UnboundLocalError for `overall_destroyed` in "colors" mode by initializing and incrementing `overall_destroyed` as target dots are destroyed, and passing it to `display_info`. This ensures the HUD and progress tracking work without runtime errors.

**Model: gpt-4o | Date: 2024-06-13 | Logic:**  
- Clarified and fixed repeated UnboundLocalError for `overall_destroyed` in "colors" mode.  
- Context: The main game loop after the "colors" block still called `display_info` with `overall_destroyed`, which is not defined in that scope for "colors" mode.  
- Fix: Now, `display_info` is only called in the main loop if not in "colors" mode, since "colors" mode handles its own HUD and progress display. This prevents undefined variable errors and avoids double HUD rendering.

**Model: gpt-4o | Date: 2025-04-21 | Logic:**  
- Fixed UnboundLocalError for `overall_destroyed` in the main game loop after "colors" mode.  
- Context: The main game loop called `display_info` with `overall_destroyed`, which was not defined in "colors" mode, causing a runtime error.  
- Fix: Now, `display_info` is only called in the main loop if not in "colors" mode, since "colors" mode handles its own HUD and progress display. This prevents undefined variable errors and avoids double HUD rendering.

**Model: gpt-4o | Date: 2025-04-21 | Logic:**  
- Fixed repeated UnboundLocalError for `overall_destroyed` in the main game loop after "colors" mode.  
- Context: The main game loop called `display_info` with `overall_destroyed`, which was not defined in "colors" mode, causing a runtime error.  
- Fix: Now, `display_info` is only called in the main loop if not in "colors" mode, since "colors" mode handles its own HUD and progress display. This prevents undefined variable errors and avoids double HUD rendering.

**Model: gpt-4o | Date: 2025-04-21 | Logic:**  
- In "colors" level, the mother dot now disperses only after a user click (not automatically).
- Dispersed dots are now 10% larger (radius increased from 22 to 24).
- Victory is achieved by clicking 10 target dots (was 25).
- Performance improvements: reduced number of background, swirl, checkpoint, and charge particles; capped frame rate at 50 FPS for all modes.
- Reason: Implements prompt requirements for color level interactivity and size, and addresses lag by reducing particle counts and frame rate for smoother gameplay on large screens.

**Model: gpt-4o | Date: 2025-04-21 | Logic:**  
- Reverted swirl, explosion, and welcome screen particle counts to previous higher values for visual appeal.
- Reason: Performance issues were not critical on the welcome page, and restoring particle counts improves the game's visual experience as originally intended.

**Model: gpt-4o | Date: 2025-04-21 | Logic:**  
- Reduced the number of gravitational particles on the Welcome screen for improved performance on large displays.
- Restored original (higher) particle and explosion counts for all gameplay levels to maintain visual appeal.
- Reason: Ensures smooth startup and menu experience while keeping gameplay visually rich as intended for the QBOARD device.

**Model: gpt-4o | Date: 2025-04-21 | Logic:**  
- Changed the welcome screen from an animated/motion display to a static "image only" version.
- The welcome screen now renders all visuals (title, particles, etc.) once and displays that as a static image until the user clicks.
- Reason: Reduces graphics load and improves performance on large displays, while preserving the intended visual style.

**Model: gpt-4o | Date: 2025-04-21 | Logic:**  
- Changed the background color in the "colors" level from white to black for all phases (mother dot, dispersion, bouncing dots, HUD).
- Removed black from the list of possible target colors in the "colors" level (so "Black" is never the mother dot).
- Ensured all HUD and prompt text remains visible on a black background (using white/yellow as needed).
- Reason: Black background is gentler on the eyes and improves visual comfort for players on large displays.

**Model: gpt-4o | Date: 2025-04-22 | Logic:**  
- Fixed IndexError in the "colors" level disperse animation when assigning distractor dot colors.
- Cause: After removing "Black" from COLORS_LIST, the code still tried to assign 5 groups of distractor dots, but only 4 distractor colors remained, causing an out-of-range error.
- Fix: Now, the code dynamically distributes the 75 distractor dots as evenly as possible among the available distractor colors, preventing out-of-range errors regardless of the number of distractor colors.
- Reason: Ensures robust color assignment and prevents crashes if the number of distractor colors changes.

**Model: gpt-4o | Date: 2025-04-22 | Logic:**  
- Removed all non-colors-level text from the "colors" level screens. Any removed text is replaced with a black string for easy identification and future editing.
- Only HUD and prompts directly related to the colors level remain visible.
- Reason: Ensures clarity and focus for the colors level, and makes it easy to spot and edit any remaining or future non-relevant text.

**Model: gpt-4o | Date: 2025-04-22 | Logic:**  
- Fixed AttributeError: module 'pygame' has no attribute 'Clock' by replacing all `pygame.Clock()` with `pygame.time.Clock()`.
- Cause: The `Clock` class is in the `pygame.time` submodule, not directly under `pygame`.
- Reason: Ensures correct usage of the Pygame API and prevents runtime errors on all platforms.

# Notes

- Centre‑display logic now prioritizes `mode == "clcase"` before any alpha substitution.  
- Greek alpha mapping applies exclusively to alphabet mode to avoid symbol fallbacks.  
- HUD and falling items follow same substitution rules for clarity.  
- Rectangle now uses a 1.5:1 aspect ratio to visually distinguish it from the square; tweak the multiplier as needed for your design.
