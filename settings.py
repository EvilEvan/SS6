# settings.py

# Game settings
COLORS_COLLISION_DELAY = 250
DISPLAY_MODES = ['DEFAULT', 'QBOARD']
DEFAULT_MODE = 'DEFAULT'
DISPLAY_SETTINGS_PATH = "display_settings.txt"
LEVEL_PROGRESS_PATH = "level_progress.txt"
MAX_CRACKS = 10
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FLAME_COLORS = [
    (255, 69, 0),
    (255, 215, 0),
    (0, 191, 255)
]
LASER_EFFECTS = [{
    "colors": [(255, 0, 0), (255, 128, 0)],
    "widths": [3, 5],
    "type": "flamethrower"
}]
LETTER_SPAWN_INTERVAL = 60
SEQUENCES = {
    "alphabet": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    "numbers": [str(i) for i in range(1, 11)],
    "clcase": list("abcdefghijklmnopqrstuvwxyz"),
    "shapes": ["Circle", "Square", "Triangle", "Rectangle", "Pentagon"]
}
GAME_MODES = ['alphabet', 'numbers', 'clcase', 'shapes', 'colors']
GROUP_SIZE = 5
SHAKE_DURATION_MISCLICK = 10
SHAKE_MAGNITUDE_MISCLICK = 5
GAME_OVER_CLICK_DELAY = 300
GAME_OVER_COUNTDOWN_SECONDS = 5
GAME_OVER_DELAY_FRAMES = 60  # Number of frames to wait before showing game over

FONT_SIZES = {
    "DEFAULT": {
      "regular": 24,
      "large": 48,
    },
    "QBOARD": {
      "regular": 30,
      "large": 60,
    }
}

MAX_PARTICLES = {
    "DEFAULT": 100,
    "QBOARD": 150
}
MAX_EXPLOSIONS = {
    "DEFAULT": 5,
    "QBOARD": 8
}
MAX_SWIRL_PARTICLES = {
    "DEFAULT": 30,
    "QBOARD": 50
}
MOTHER_RADIUS = {
    "DEFAULT": 90,
    "QBOARD": 120
}

DEBUG_MODE = True
SHOW_FPS = True