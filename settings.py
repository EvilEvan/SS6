# settings.py

# Game settings
COLORS_COLLISION_DELAY = 250
LEVEL_PROGRESS_PATH = "level_progress.txt"
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