import pygame
from settings import FONT_SIZES

class ResourceManager:
    """Manages game resources like fonts based on display mode."""
    
    def __init__(self):
        self.display_mode = "DEFAULT"
        self.fonts = {}
        self.large_font = None
        self.small_font = None
        self.target_font = None
        self.title_font = None
        
    def set_display_mode(self, mode):
        """Set the current display mode."""
        self.display_mode = mode
        
    def initialize_game_resources(self):
        """Initialize fonts and other resources based on display mode."""
        # Get font sizes for current display mode
        font_sizes = FONT_SIZES[self.display_mode]["regular"]
        large_font_size = FONT_SIZES[self.display_mode]["large"]
        
        # Initialize fonts
        self.fonts = [
            pygame.font.Font(None, font_sizes),
            pygame.font.Font(None, int(font_sizes * 1.5)),
            pygame.font.Font(None, int(font_sizes * 2)),
            pygame.font.Font(None, int(font_sizes * 2.5)),
            pygame.font.Font(None, int(font_sizes * 3))
        ]
        
        self.large_font = pygame.font.Font(None, large_font_size)
        self.small_font = pygame.font.Font(None, font_sizes)
        self.target_font = pygame.font.Font(None, int(font_sizes * 4))  # Large font for targets
        self.title_font = pygame.font.Font(None, int(font_sizes * 8))   # Very large for titles
        
        return {
            'fonts': self.fonts,
            'large_font': self.large_font,
            'small_font': self.small_font,
            'target_font': self.target_font,
            'title_font': self.title_font
        } 