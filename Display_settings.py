# Display_settings.py
"""
Display settings and functionality for Super Student game.
Handles display mode detection, configuration, and UI components.
"""

import pygame
import random
import math

# Display mode constants
DISPLAY_MODES = ['DEFAULT', 'QBOARD']
DEFAULT_MODE = 'DEFAULT'
DISPLAY_SETTINGS_PATH = "display_settings.txt"

# Display-specific font sizes
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

# Display-specific particle and effect limits
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
    "QBOARD": 15
}

MOTHER_RADIUS = {
    "DEFAULT": 90,
    "QBOARD": 120
}

# Performance optimization settings for QBoard
PERFORMANCE_SETTINGS = {
    "DEFAULT": {
        "collision_check_frequency": 1,  # Check collisions every frame
        "particle_glow_effects": True,
        "charge_up_particles": 150,
        "swirl_particle_regeneration": 0.1,
        "explosion_particles_per_hit": 3
    },
    "QBOARD": {
        "collision_check_frequency": 2,  # Check collisions every 2 frames
        "particle_glow_effects": False,  # Disable glow effects
        "charge_up_particles": 75,       # Reduce charge-up particles
        "swirl_particle_regeneration": 0.05,  # Reduce regeneration frequency
        "explosion_particles_per_hit": 2     # Fewer explosion particles
    }
}

# Debug settings
DEBUG_MODE = True
SHOW_FPS = True

def detect_display_type():
    """
    Function to determine initial display mode based on screen size.
    
    Returns:
        str: "QBOARD" for large displays, "DEFAULT" for standard displays
    """
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h
    
    # If screen is larger than typical desktop monitors, assume it's a QBoard
    if screen_w >= 1920 and screen_h >= 1080:
        if screen_w > 2560 or screen_h > 1440:  # Larger than QHD is likely QBoard
            return "QBOARD"
    
    # Default to smaller format for typical monitors/laptops
    return "DEFAULT"

def load_display_mode():
    """
    Load the display mode from settings file or auto-detect.
    
    Returns:
        str: The display mode to use
    """
    # Try to load previous display mode setting
    try:
        with open(DISPLAY_SETTINGS_PATH, "r") as f:
            loaded_mode = f.read().strip()
            if loaded_mode in DISPLAY_MODES:
                return loaded_mode
    except:
        pass  # If file doesn't exist or can't be read, use auto-detection
    
    # If file doesn't exist or can't be read, use auto-detection
    return detect_display_type()

def save_display_mode(mode):
    """
    Save the display mode to settings file.
    
    Args:
        mode (str): Display mode to save
    """
    try:
        with open(DISPLAY_SETTINGS_PATH, "w") as f:
            f.write(mode)
    except:
        pass  # If can't write, silently continue

def draw_neon_button(screen, rect, base_color):
    """
    Draws a button with a neon glow effect.
    
    Args:
        screen: Pygame surface to draw on
        rect: Button rectangle
        base_color: RGB color tuple for the neon effect
    """
    # Fill the button with a dark background
    pygame.draw.rect(screen, (20, 20, 20), rect)
    # Draw a neon glow border by drawing multiple expanding outlines
    for i in range(1, 6):
        neon_rect = pygame.Rect(rect.x - i, rect.y - i, rect.width + 2*i, rect.height + 2*i)
        pygame.draw.rect(screen, base_color, neon_rect, 1)
    # Draw a solid border
    pygame.draw.rect(screen, base_color, rect, 2)

class DisplayModeSelector:
    """
    Handles the display mode selection UI and logic.
    """
    
    def __init__(self, WIDTH, HEIGHT, screen, small_font, flame_colors):
        """
        Initialize the display mode selector.
        
        Args:
            WIDTH (int): Screen width
            HEIGHT (int): Screen height
            screen: Pygame screen surface
            small_font: Pygame font for text rendering
            flame_colors: List of flame colors for effects
        """
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.screen = screen
        self.small_font = small_font
        self.flame_colors = flame_colors
        
        # Calculate scaling factor based on current screen size
        base_height = 1080  # Base design height
        self.scale_factor = HEIGHT / base_height
        
        # Apply scaling to UI elements
        self.title_offset = int(50 * self.scale_factor)
        self.button_width = int(200 * self.scale_factor)
        self.button_height = int(60 * self.scale_factor)
        self.button_spacing = int(20 * self.scale_factor)
        self.button_y_pos = int(200 * self.scale_factor)
        self.instruction_y_pos = int(150 * self.scale_factor)
        
        # Create buttons for display size options
        self.default_button = pygame.Rect(
            (WIDTH // 2 - self.button_width - self.button_spacing, HEIGHT // 2 + self.button_y_pos), 
            (self.button_width, self.button_height)
        )
        self.qboard_button = pygame.Rect(
            (WIDTH // 2 + self.button_spacing, HEIGHT // 2 + self.button_y_pos), 
            (self.button_width, self.button_height)
        )
        
        # Initialize particles for visual effects
        self.particles = self._create_particles()
        
        # Color transition state
        self.color_transition = 0.0
        self.color_transition_speed = 0.01
        self.current_color = random.choice(flame_colors)
        self.next_color = random.choice(flame_colors)
        
        # Title floating effect
        self.title_offset_y = 0
        self.title_float_speed = 0.002
        self.title_float_direction = 1
        
        # Get the auto-detected display type
        self.detected_display = detect_display_type()
        
        # Create fonts
        collab_font_size = int(100 * self.scale_factor)
        self.collab_font = pygame.font.Font(None, collab_font_size)
        
        title_font_size = int(320 * self.scale_factor)
        self.title_font = pygame.font.Font(None, title_font_size)
        
        # Cache for title rendering to improve performance
        self.title_cache = {}
        self.last_title_color = None
        
        # Pre-render static text surfaces
        self.instruction_surface = self.small_font.render("Choose Display Size:", True, (255, 255, 255))
        self.default_surface = self.small_font.render("Default", True, (255, 255, 255))
        self.qboard_surface = self.small_font.render("QBoard", True, (255, 255, 255))
    
    def _create_particles(self):
        """Create dynamic gravitational particles that orbit around the title."""
        particle_colors = [
            (255, 0, 128),   # Bright pink
            (0, 255, 128),   # Bright green
            (128, 0, 255),   # Bright purple
            (255, 128, 0),   # Bright orange
            (0, 128, 255)    # Bright blue
        ]
        
        # Adjust particle count based on display mode for performance
        display_mode = load_display_mode()
        particle_count = 60 if display_mode == "QBOARD" else 120  # Reduced for QBoard
        
        particles = []
        for _ in range(particle_count):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(200, max(self.WIDTH, self.HEIGHT) * 0.4)
            x = self.WIDTH // 2 + math.cos(angle) * distance
            y = self.HEIGHT // 2 + math.sin(angle) * distance
            size = random.randint(int(9 * self.scale_factor), int(15 * self.scale_factor))
            particles.append({
                "x": x,
                "y": y,
                "color": random.choice(particle_colors),
                "size": size,
                "orig_size": size,
                "angle": angle,
                "orbit_speed": random.uniform(0.0005, 0.002),
                "orbit_distance": distance,
                "pulse_speed": random.uniform(0.02, 0.06),
                "pulse_factor": random.random()
            })
        
        return particles
    
    def update_particles(self, delta_time):
        """Update particle positions and effects."""
        for particle in self.particles:
            # Orbital movement
            particle["angle"] += particle["orbit_speed"] * delta_time * 60
            particle["x"] = self.WIDTH // 2 + math.cos(particle["angle"]) * particle["orbit_distance"]
            particle["y"] = self.HEIGHT // 2 + math.sin(particle["angle"]) * particle["orbit_distance"]
            
            # Pulsing effect
            particle["pulse_factor"] += particle["pulse_speed"] * delta_time * 60
            if particle["pulse_factor"] > 1.0:
                particle["pulse_factor"] = 0.0
            pulse = 0.7 + 0.3 * math.sin(particle["pulse_factor"] * math.pi * 2)
            particle["size"] = particle["orig_size"] * pulse
    
    def update_color_transition(self, delta_time):
        """Update title color transition."""
        self.color_transition += self.color_transition_speed * delta_time * 60
        if self.color_transition >= 1.0:
            self.color_transition = 0.0
            self.current_color = self.next_color
            self.next_color = random.choice([c for c in self.flame_colors if c != self.current_color])
    
    def update_title_float(self, delta_time):
        """Update title floating effect."""
        self.title_offset_y += self.title_float_direction * self.title_float_speed * delta_time * 60
        if abs(self.title_offset_y) > 10:
            self.title_float_direction *= -1
    
    def get_title_color(self):
        """Get the current interpolated title color."""
        r = int(self.current_color[0] * (1 - self.color_transition) + self.next_color[0] * self.color_transition)
        g = int(self.current_color[1] * (1 - self.color_transition) + self.next_color[1] * self.color_transition)
        b = int(self.current_color[2] * (1 - self.color_transition) + self.next_color[2] * self.color_transition)
        return (r, g, b)
    
    def handle_click(self, mx, my):
        """
        Handle mouse click on buttons.
        
        Args:
            mx (int): Mouse x position
            my (int): Mouse y position
            
        Returns:
            str or None: Selected display mode or None if no button clicked
        """
        if self.default_button.collidepoint(mx, my):
            return "DEFAULT"
        elif self.qboard_button.collidepoint(mx, my):
            return "QBOARD"
        return None
    
    def get_hover_states(self, mx, my):
        """
        Get hover states for buttons.
        
        Args:
            mx (int): Mouse x position
            my (int): Mouse y position
            
        Returns:
            tuple: (default_hover, qboard_hover)
        """
        default_hover = self.default_button.collidepoint(mx, my)
        qboard_hover = self.qboard_button.collidepoint(mx, my)
        return default_hover, qboard_hover
    
    def draw_particles(self):
        """Draw orbiting particles."""
        for particle in self.particles:
            pygame.draw.circle(self.screen, particle["color"],
                             (int(particle["x"]), int(particle["y"])),
                             int(particle["size"]))
    
    def draw_title(self, title_color):
        """Draw the main title with 3D effects (optimized with caching)."""
        title_text = "Super Student"
        title_rect_center = (self.WIDTH // 2, self.HEIGHT // 2 - self.title_offset + self.title_offset_y)
        
        # Check if we need to re-render (color changed significantly)
        color_key = (title_color[0] // 10, title_color[1] // 10, title_color[2] // 10)  # Quantize color
        
        if color_key not in self.title_cache or self.last_title_color != color_key:
            # Clear old cache if it gets too large
            if len(self.title_cache) > 10:
                self.title_cache.clear()
            
            r, g, b = title_color
            
            # Pre-render all title variations
            shadow_color = (20, 20, 20)
            highlight_color = (min(r+80, 255), min(g+80, 255), min(b+80, 255))
            shadow_color_3d = (max(r-90, 0), max(g-90, 0), max(b-90, 0))
            mid_color = (max(r-40, 0), max(g-40, 0), max(b-40, 0))
            glow_colors = [(r//2, g//2, b//2), (r//3, g//3, b//3)]
            
            self.title_cache[color_key] = {
                'shadow': self.title_font.render(title_text, True, shadow_color),
                'highlight': self.title_font.render(title_text, True, highlight_color),
                'mid_tone': self.title_font.render(title_text, True, mid_color),
                'inner_shadow': self.title_font.render(title_text, True, shadow_color_3d),
                'main': self.title_font.render(title_text, True, title_color),
                'glow1': self.title_font.render(title_text, True, glow_colors[0]),
                'glow2': self.title_font.render(title_text, True, glow_colors[1])
            }
            self.last_title_color = color_key
        
        # Use cached surfaces
        cached_title = self.title_cache[color_key]
        
        # Draw shadow
        shadow_rect = cached_title['shadow'].get_rect(center=(title_rect_center[0] + 1, title_rect_center[1] + 1))
        self.screen.blit(cached_title['shadow'], shadow_rect)
        
        # Add dynamic glow (simplified - only 2 glow layers instead of 8)
        glow_rect = cached_title['glow1'].get_rect(center=(title_rect_center[0] - 1, title_rect_center[1] - 1))
        self.screen.blit(cached_title['glow1'], glow_rect)
        glow_rect = cached_title['glow1'].get_rect(center=(title_rect_center[0] + 1, title_rect_center[1] + 1))
        self.screen.blit(cached_title['glow1'], glow_rect)
        
        # Create the 3D effect with highlight and shadow
        highlight_rect = cached_title['highlight'].get_rect(center=(title_rect_center[0] - 4, title_rect_center[1] - 4))
        self.screen.blit(cached_title['highlight'], highlight_rect)
        
        mid_rect = cached_title['mid_tone'].get_rect(center=(title_rect_center[0] + 2, title_rect_center[1] + 2))
        self.screen.blit(cached_title['mid_tone'], mid_rect)
        
        inner_shadow_rect = cached_title['inner_shadow'].get_rect(center=(title_rect_center[0] + 4, title_rect_center[1] + 4))
        self.screen.blit(cached_title['inner_shadow'], inner_shadow_rect)
        
        title_rect = cached_title['main'].get_rect(center=title_rect_center)
        self.screen.blit(cached_title['main'], title_rect)
    
    def draw_instructions(self):
        """Draw instruction text (optimized with pre-rendered surface)."""
        display_rect = self.instruction_surface.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + self.instruction_y_pos))
        self.screen.blit(self.instruction_surface, display_rect)
    
    def draw_buttons(self, default_hover, qboard_hover):
        """Draw display mode selection buttons (optimized with pre-rendered surfaces)."""
        # Draw default button with hover effect
        pygame.draw.rect(self.screen, (20, 20, 20), self.default_button)
        glow_intensity = 6 if default_hover else 5
        for i in range(1, glow_intensity):
            multiplier = 1.5 if default_hover else 1.0
            alpha_factor = (1 - i/glow_intensity) * multiplier
            glow_color = (0, min(int(200 + 55 * default_hover * alpha_factor), 255), 255)
            default_rect = pygame.Rect(self.default_button.x - i, self.default_button.y - i, 
                                     self.default_button.width + 2*i, self.default_button.height + 2*i)
            pygame.draw.rect(self.screen, glow_color, default_rect, 1)
        border_width = 3 if default_hover else 2
        pygame.draw.rect(self.screen, (0, 200, 255), self.default_button, border_width)
        default_text_rect = self.default_surface.get_rect(center=self.default_button.center)
        self.screen.blit(self.default_surface, default_text_rect)
        
        # Draw QBoard button with hover effect
        pygame.draw.rect(self.screen, (20, 20, 20), self.qboard_button)
        glow_intensity = 6 if qboard_hover else 5
        for i in range(1, glow_intensity):
            multiplier = 1.5 if qboard_hover else 1.0
            alpha_factor = (1 - i/glow_intensity) * multiplier
            glow_color = (min(int(255 * multiplier * alpha_factor), 255), 0, min(int(150 * multiplier * alpha_factor), 255))
            qboard_rect = pygame.Rect(self.qboard_button.x - i, self.qboard_button.y - i, 
                                    self.qboard_button.width + 2*i, self.qboard_button.height + 2*i)
            pygame.draw.rect(self.screen, glow_color, qboard_rect, 1)
        border_width = 3 if qboard_hover else 2
        pygame.draw.rect(self.screen, (255, 0, 150), self.qboard_button, border_width)
        qboard_text_rect = self.qboard_surface.get_rect(center=self.qboard_button.center)
        self.screen.blit(self.qboard_surface, qboard_text_rect)
    
    def draw_auto_detected_indicator(self, current_time, default_hover, qboard_hover):
        """Draw auto-detected mode indicator."""
        auto_text_color = (200, 200, 200)
        if self.detected_display == "DEFAULT" and default_hover:
            pulse = 0.5 + 0.5 * math.sin(current_time * 0.005)
            auto_text_color = (0, int(200 + 55 * pulse), 255)
        elif self.detected_display == "QBOARD" and qboard_hover:
            pulse = 0.5 + 0.5 * math.sin(current_time * 0.005)
            auto_text_color = (255, 0, int(150 * pulse))
        
        auto_text = self.small_font.render(f"Auto-detected: {self.detected_display}", True, auto_text_color)
        auto_rect = auto_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + self.button_y_pos + self.button_height + 30))
        self.screen.blit(auto_text, auto_rect)
    
    def draw_collaboration_text(self, current_time):
        """Draw collaboration text with pulsing effect."""
        # Pulsing SANGSOM text effect
        pulse_factor = 0.5 + 0.5 * math.sin(current_time * 0.002)
        bright_yellow = (255, 255, 0)
        lite_yellow = (255, 255, 150)
        sangsom_color = tuple(int(bright_yellow[i] * (1 - pulse_factor) + lite_yellow[i] * pulse_factor) for i in range(3))
        
        collab_text1 = self.collab_font.render("In collaboration with ", True, (255, 255, 255))
        collab_text2 = self.collab_font.render("SANGSOM", True, sangsom_color)
        collab_text3 = self.collab_font.render(" Kindergarten", True, (255, 255, 255))
        
        collab_rect1 = collab_text1.get_rect()
        collab_rect1.right = self.WIDTH // 2 - collab_text2.get_width() // 2
        collab_rect1.centery = self.HEIGHT // 2 + int(350 * self.scale_factor)
        
        collab_rect2 = collab_text2.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + int(350 * self.scale_factor)))
        
        collab_rect3 = collab_text3.get_rect()
        collab_rect3.left = collab_rect2.right
        collab_rect3.centery = self.HEIGHT // 2 + int(350 * self.scale_factor)
        
        self.screen.blit(collab_text1, collab_rect1)
        self.screen.blit(collab_text2, collab_rect2)
        self.screen.blit(collab_text3, collab_rect3)
    
    def draw_creator_text(self, current_time):
        """Draw creator text with floating effect."""
        creator_float = 2 * math.sin(current_time * 0.001)
        creator_text = self.small_font.render("Created by Teacher Evan and Teacher Lee", True, (255, 255, 255))
        creator_rect = creator_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 40 + creator_float))
        self.screen.blit(creator_text, creator_rect)
    
    def draw_fps(self, clock):
        """Draw FPS counter if debug mode is enabled."""
        if DEBUG_MODE and SHOW_FPS:
            fps = int(clock.get_fps())
            fps_text = self.small_font.render(f"FPS: {fps}", True, (255, 255, 255))
            self.screen.blit(fps_text, (10, 10)) 