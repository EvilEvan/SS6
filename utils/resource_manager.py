import pygame
from Display_settings import FONT_SIZES
from settings import SEQUENCES, WHITE, BLACK, FLAME_COLORS

class ResourceManager:
    """Manages game resources like fonts based on display mode."""
    
    def __init__(self):
        self.display_mode = "DEFAULT"
        self.fonts = {}
        self.large_font = None
        self.small_font = None
        self.target_font = None
        self.title_font = None
        
        # Font caches for performance optimization
        self.center_target_cache = {}  # Cache for center target (size 900)
        self.falling_object_cache = {}  # Cache for falling objects (size 240)
        self.center_font = None  # Font for center target (size 900)
        self.falling_font = None  # Font for falling objects (size 240)
        
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
        self.target_font = pygame.font.Font(None, int(font_sizes * 8))  # Large font for targets (doubled from 4 to 8)
        self.title_font = pygame.font.Font(None, int(font_sizes * 8))   # Very large for titles
        
        # Initialize performance-critical fonts
        self.center_font = pygame.font.Font(None, 900)  # Center target font
        self.falling_font = pygame.font.Font(None, 240)  # Falling objects font
        
        # Pre-cache commonly used text surfaces
        self._initialize_font_caches()
        
        return {
            'fonts': self.fonts,
            'large_font': self.large_font,
            'small_font': self.small_font,
            'target_font': self.target_font,
            'title_font': self.title_font,
            'center_font': self.center_font,
            'falling_font': self.falling_font
        }
        
    def _initialize_font_caches(self):
        """Pre-render commonly used text surfaces for performance."""
        print(f"Initializing font caches for display mode: {self.display_mode}")
        
        # Clear existing caches
        self.center_target_cache.clear()
        self.falling_object_cache.clear()
        
        # Cache center target surfaces (size 900) for all game modes
        self._cache_center_targets()
        
        # Cache falling object surfaces (size 240) for all game modes
        self._cache_falling_objects()
        
        print(f"Font cache initialized: {len(self.center_target_cache)} center targets, {len(self.falling_object_cache)} falling objects")
        
    def _cache_center_targets(self):
        """Pre-render center target text surfaces."""
        # Colors for center targets (flame colors for text modes)
        center_colors = FLAME_COLORS + [BLACK]  # Include black for shapes mode
        
        # Cache all sequences for center targets
        for mode, sequence in SEQUENCES.items():
            if mode == "shapes":
                continue  # Shapes don't use text for center targets
                
            for item in sequence:
                for color in center_colors:
                    # Handle special cases
                    display_char = item
                    if mode == "clcase":
                        display_char = item.upper()
                    elif (mode == "alphabet" or mode == "clcase") and item == "a":
                        display_char = "α"
                    
                    cache_key = (mode, item, color)
                    if cache_key not in self.center_target_cache:
                        surface = self.center_font.render(display_char, True, color)
                        self.center_target_cache[cache_key] = surface
                        
    def _cache_falling_objects(self):
        """Pre-render falling object text surfaces."""
        # Colors for falling objects
        falling_colors = [BLACK, (150, 150, 150)]  # Target and non-target colors
        
        # Cache all sequences for falling objects
        for mode, sequence in SEQUENCES.items():
            if mode == "shapes":
                continue  # Shapes don't use text for falling objects
                
            for item in sequence:
                for color in falling_colors:
                    # Handle special cases
                    display_char = item
                    if mode == "clcase" and item == "a":
                        display_char = "α"
                    
                    cache_key = (mode, item, color)
                    if cache_key not in self.falling_object_cache:
                        surface = self.falling_font.render(display_char, True, color)
                        self.falling_object_cache[cache_key] = surface
                        
    def get_center_target_surface(self, mode, target_letter, color):
        """Get cached center target surface or render if not cached."""
        cache_key = (mode, target_letter, color)
        
        if cache_key in self.center_target_cache:
            return self.center_target_cache[cache_key]
        
        # Fallback: render on demand and cache
        display_char = target_letter
        if mode == "clcase":
            display_char = target_letter.upper()
        elif (mode == "alphabet" or mode == "clcase") and target_letter == "a":
            display_char = "α"
            
        surface = self.center_font.render(display_char, True, color)
        self.center_target_cache[cache_key] = surface
        return surface
        
    def get_falling_object_surface(self, mode, item_value, color):
        """Get cached falling object surface or render if not cached."""
        cache_key = (mode, item_value, color)
        
        if cache_key in self.falling_object_cache:
            return self.falling_object_cache[cache_key]
        
        # Fallback: render on demand and cache
        display_char = item_value
        if mode == "clcase" and item_value == "a":
            display_char = "α"
            
        surface = self.falling_font.render(display_char, True, color)
        self.falling_object_cache[cache_key] = surface
        return surface
        
    def clear_caches(self):
        """Clear all font caches to free memory."""
        self.center_target_cache.clear()
        self.falling_object_cache.clear()
        
    def get_cache_stats(self):
        """Get statistics about cache usage."""
        return {
            'center_targets': len(self.center_target_cache),
            'falling_objects': len(self.falling_object_cache),
            'total_cached_surfaces': len(self.center_target_cache) + len(self.falling_object_cache)
        } 