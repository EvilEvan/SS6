import pygame
import random
import math
from settings import (
    COLORS_COLLISION_DELAY, WHITE, BLACK, FLAME_COLORS,
    LEVEL_PROGRESS_PATH
)
from universal_class import GlassShatterManager, HUDManager, MultiTouchManager
from collections import defaultdict  # NEW: for sparse spatial grid


class ColorsLevel:
    """
    Handles the Colors level gameplay logic with performance optimizations.
    """
    
    def __init__(self, width, height, screen, small_font, particle_manager, 
                 glass_shatter_manager, multi_touch_manager, hud_manager, 
                 mother_radius, create_explosion_func, checkpoint_screen_func, game_over_screen_func,
                 explosions_list, draw_explosion_func):
        """
        Initialize the Colors level.
        
        Args:
            width (int): Screen width
            height (int): Screen height
            screen: Pygame screen surface
            small_font: Font for UI text
            particle_manager: Particle system manager
            glass_shatter_manager: Glass shatter effect manager
            multi_touch_manager: Multi-touch input manager
            hud_manager: HUD display manager
            mother_radius (int): Radius of the mother dot
            create_explosion_func: Function to create explosion effects
            checkpoint_screen_func: Function to show checkpoint screen
            game_over_screen_func: Function to show game over screen
            explosions_list: Reference to the global explosions list
            draw_explosion_func: Function to draw explosion effects
        """
        self.width = width
        self.height = height
        self.screen = screen
        self.small_font = small_font
        self.particle_manager = particle_manager
        self.glass_shatter_manager = glass_shatter_manager
        self.multi_touch_manager = multi_touch_manager
        self.hud_manager = hud_manager
        self.mother_radius = mother_radius
        self.create_explosion = create_explosion_func
        self.checkpoint_screen = checkpoint_screen_func
        self.game_over_screen = game_over_screen_func
        self.explosions = explosions_list
        self.draw_explosion = draw_explosion_func
          # Colors configuration
        self.COLORS_LIST = [
            (0, 0, 255),    # Blue
            (255, 0, 0),    # Red
            (0, 200, 0),    # Green
            (255, 255, 0),  # Yellow
            (128, 0, 255),  # Purple
        ]
        self.color_names = ["Blue", "Red", "Green", "Yellow", "Purple"]
        
        # PERFORMANCE OPTIMIZATION: Spatial grid for collision detection
        self.grid_size = 120  # Grid cell size for spatial partitioning
        self.grid_cols = (width // self.grid_size) + 1
        self.grid_rows = (height // self.grid_size) + 1
          # VISUAL ENHANCEMENT: Shimmer and depth effects
        self.frame_counter = 0
        self.shimmer_seeds = {}  # Per-dot shimmer seed for consistency
        # NEW: cache for pre-rendered circle surfaces
        self.surface_cache = {}
        
        # Game state variables
        self.reset_level_state()
        
    def reset_level_state(self):
        """Reset all level-specific state variables."""
        self.used_colors = []
        self.color_idx = 0
        self.mother_color = None
        self.mother_color_name = ""
        self.current_color_dots_destroyed = 0
        self.dots_per_color = 2
        self.total_dots_destroyed = 0
        self.checkpoint_trigger = 10
        self.target_dots_left = 10
        self.dots = []
        self.dots_active = False
        self.overall_destroyed = 0
        self.dots_before_checkpoint = 0
        self.collision_enabled = False
        self.collision_delay_counter = 0
        self.collision_delay_frames = COLORS_COLLISION_DELAY
        self.score = 0
        self.running = True
        self.frame_counter = 0
        self.shimmer_seeds = {}
        
    def _create_spatial_grid(self):
        """Create sparse spatial grid (dict) for optimized collision detection."""
        grid = defaultdict(list)  # key -> list of dot indices
        for i, dot in enumerate(self.dots):
            if not dot["alive"]:
                continue
            grid_x = min(max(int(dot["x"] // self.grid_size), 0), self.grid_cols - 1)
            grid_y = min(max(int(dot["y"] // self.grid_size), 0), self.grid_rows - 1)
            grid[(grid_x, grid_y)].append(i)
        return grid
        
    def _get_grid_neighbors(self, x, y):
        """Get neighboring grid cells for collision detection."""
        grid_x = min(int(x // self.grid_size), self.grid_cols - 1)
        grid_y = min(int(y // self.grid_size), self.grid_rows - 1)
        
        neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = grid_x + dx, grid_y + dy
                if 0 <= nx < self.grid_cols and 0 <= ny < self.grid_rows:
                    neighbors.append((nx, ny))
        return neighbors
        
    def _calculate_dot_shading(self, base_color, radius, is_target=False):
        """Calculate depth shading for dots with gradient effect."""
        # Create gradient from lighter center to darker edge
        center_color = tuple(min(255, int(c * 1.3)) for c in base_color)
        edge_color = tuple(max(0, int(c * 0.7)) for c in base_color)
        
        # Add glow effect for target dots
        if is_target:
            glow_intensity = 0.2 + 0.1 * math.sin(self.frame_counter * 0.1)
            center_color = tuple(min(255, int(c * (1.0 + glow_intensity))) for c in center_color)
            
        return center_color, edge_color
        
    def _get_shimmer_effect(self, dot_id):
        """Get shimmer effect values for a specific dot."""
        if dot_id not in self.shimmer_seeds:
            self.shimmer_seeds[dot_id] = random.random() * 6.28  # Random phase
            
        seed = self.shimmer_seeds[dot_id]
        shimmer = math.sin(self.frame_counter * 0.05 + seed) * 0.1 + 1.0
        alpha_shimmer = math.sin(self.frame_counter * 0.08 + seed) * 15 + 240
        
        return shimmer, max(200, min(255, int(alpha_shimmer)))

    # NEW helper -----------------------------------------------------------
    def _get_circle_surface(self, color, radius):
        """Return cached filled-circle surface for given color & radius."""
        key = (color, radius)
        surf = self.surface_cache.get(key)
        if surf is None:
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (radius, radius), radius)
            self.surface_cache[key] = surf
        return surf
        
    def run(self):
        """
        Main entry point to run the colors level.
        
        Returns:
            bool: False to return to menu, True to restart level
        """
        self.reset_level_state()
        
        # Initialize random starting color
        self.color_idx = random.randint(0, len(self.COLORS_LIST) - 1)
        self.used_colors.append(self.color_idx)
        self.mother_color = self.COLORS_LIST[self.color_idx]
        self.mother_color_name = self.color_names[self.color_idx]
        
        # Show mother dot vibration animation
        if not self._show_mother_dot_vibration():
            return False
            
        # Wait for click to start dispersion
        if not self._wait_for_dispersion_start():
            return False
            
        # Show dispersion animation and initialize dots
        self._show_dispersion_animation()
        
        # Run main game loop
        return self._main_game_loop()
        
    def _show_mother_dot_vibration(self):
        """Show the mother dot vibration animation."""
        center = (self.width // 2, self.height // 2)
        vibration_frames = 30
        clock = pygame.time.Clock()
        
        for vib in range(vibration_frames):
            # Handle events to allow quitting
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False
                    
            self.screen.fill(BLACK)
            vib_x = center[0] + random.randint(-6, 6)
            vib_y = center[1] + random.randint(-6, 6)
            pygame.draw.circle(self.screen, self.mother_color, (vib_x, vib_y), self.mother_radius)
            
            # Draw label
            label = self.small_font.render("Remember this color!", True, WHITE)
            label_rect = label.get_rect(center=(self.width // 2, self.height // 2 + self.mother_radius + 60))
            self.screen.blit(label, label_rect)
            
            pygame.display.flip()
            clock.tick(50)
            
        return True
        
    def _wait_for_dispersion_start(self):
        """Wait for player click to start dispersion."""
        center = (self.width // 2, self.height // 2)
        clock = pygame.time.Clock()
        waiting_for_dispersion = True
        
        while waiting_for_dispersion:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    waiting_for_dispersion = False
                    
            # Draw the mother dot and prompt
            self.screen.fill(BLACK)
            pygame.draw.circle(self.screen, self.mother_color, center, self.mother_radius)
            
            label = self.small_font.render("Remember this color!", True, WHITE)
            label_rect = label.get_rect(center=(self.width // 2, self.height // 2 + self.mother_radius + 60))
            self.screen.blit(label, label_rect)
            
            prompt = self.small_font.render("Click to start!", True, (255, 255, 0))
            prompt_rect = prompt.get_rect(center=(self.width // 2, self.height // 2 + self.mother_radius + 120))
            self.screen.blit(prompt, prompt_rect)
            
            pygame.display.flip()
            clock.tick(50)
            
        return True
        
    def _show_dispersion_animation(self):
        """Show the mother dot dispersion animation and create initial dots."""
        center = (self.width // 2, self.height // 2)
        disperse_frames = 30
        clock = pygame.time.Clock()
          # Create dispersion particles
        disperse_particles = []
        for i in range(85):  # Reduced from 100 to 85 (15 fewer dots)
            angle = random.uniform(0, 2 * math.pi)
            disperse_particles.append({
                "angle": angle,
                "radius": 0,
                "speed": random.uniform(12, 18),
                "color": self.mother_color if i < 17 else None,  # Reduced from 25 to 17 target dots
            })
              # Assign distractor colors
        distractor_colors = [c for idx, c in enumerate(self.COLORS_LIST) if idx != self.color_idx]
        num_distractor_colors = len(distractor_colors)
        total_distractor_dots = 68  # Reduced from 75 to 68
        dots_per_color = total_distractor_dots // num_distractor_colors
        extra = total_distractor_dots % num_distractor_colors
        idx = 17  # Updated from 25 to 17
        
        for color_idx, color in enumerate(distractor_colors):
            count = dots_per_color + (1 if color_idx < extra else 0)
            for _ in range(count):
                if idx < 85:  # Updated from 100 to 85
                    disperse_particles[idx]["color"] = color
                    idx += 1
                    
        # Initialize bouncing dots
        self.dots = []
        initial_positions = []
        
        for i, p in enumerate(disperse_particles):
            x = int(center[0] + math.cos(p["angle"]) * p["radius"])
            y = int(center[1] + math.sin(p["angle"]) * p["radius"])
            x += random.randint(-20, 20)
            y += random.randint(-20, 20)
            x = max(48, min(self.width - 48, x))
            y = max(48, min(self.height - 48, y))
            initial_positions.append((x, y))
            
        # Create dots with positions
        for i, (x, y) in enumerate(initial_positions):
            dx = random.uniform(-6, 6)
            dy = random.uniform(-6, 6)
            color = disperse_particles[i]["color"]
            
            self.dots.append({
                "x": x, "y": y,
                "dx": dx, "dy": dy,
                "color": color,
                "radius": 48,
                "target": True if color == self.mother_color else False,
                "alive": True,
            })
            
        self.dots_active = True
        
        # Show dispersion animation
        for t in range(disperse_frames):
            self.screen.fill(BLACK)
            for p in disperse_particles:
                p["radius"] += p["speed"]
                x = int(center[0] + math.cos(p["angle"]) * p["radius"])
                y = int(center[1] + math.sin(p["angle"]) * p["radius"])
                pygame.draw.circle(self.screen, p["color"], (x, y), 48)
                
            pygame.display.flip()
            clock.tick(50)
            
    def _main_game_loop(self):
        """Main game loop for the colors level."""
        clock = pygame.time.Clock()
        
        # Background stars
        stars = []
        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            radius = random.randint(2, 4)
            stars.append([x, y, radius])
            
        while self.running:
            # Handle events
            if not self._handle_events():
                return False
                
            # Update dots physics
            self._update_dots()
            
            # Update collision delay counter
            if not self.collision_enabled:
                self.collision_delay_counter += 1
                if self.collision_delay_counter >= self.collision_delay_frames:
                    self.collision_enabled = True
                    self.collision_delay_counter = 0
                    self._create_collision_enabled_effect()
                    
            # Check for collisions between dots
            if self.collision_enabled:
                self._handle_dot_collisions()
                
            # Draw everything
            self._draw_frame(stars)
            
            # Handle end condition (target_dots_left <= 0)
            if self.target_dots_left <= 0:
                self._generate_new_dots()
                
            pygame.display.flip()
            clock.tick(50)
            
        return False
        
    def _handle_events(self):
        """Handle pygame events for the colors level."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
                return False
                
            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                if not self._handle_click(mx, my):
                    self.glass_shatter_manager.handle_misclick(mx, my)
                    
            # Handle touch events
            elif event.type == pygame.FINGERDOWN:
                touch_result = self.multi_touch_manager.handle_touch_down(event)
                if touch_result is None:
                    continue
                touch_id, touch_x, touch_y = touch_result
                if not self._handle_click(touch_x, touch_y):
                    self.glass_shatter_manager.handle_misclick(touch_x, touch_y)
                    
            elif event.type == pygame.FINGERUP:
                self.multi_touch_manager.handle_touch_up(event)
                
        return True
        
    def _handle_click(self, x, y):
        """
        Handle a click/touch at the given coordinates.
        
        Returns:
            bool: True if a target was hit, False otherwise
        """
        hit_target = False
        radius_cache = {}
        for dot in self.dots:
            if not dot["alive"]:
                continue
            r_sq = radius_cache.get(dot["radius"])
            if r_sq is None:
                r_sq = dot["radius"] ** 2
                radius_cache[dot["radius"]] = r_sq
            dx = x - dot["x"]
            dy = y - dot["y"]
            if dx * dx + dy * dy <= r_sq:
                hit_target = True
                if dot["target"]:
                    self._destroy_target_dot(dot)
                break
        return hit_target
        
    def _destroy_target_dot(self, dot):
        """Handle destruction of a target dot."""
        dot["alive"] = False
        self.target_dots_left -= 1
        self.score += 10
        self.overall_destroyed += 1
        self.current_color_dots_destroyed += 1
        self.total_dots_destroyed += 1
        
        # Create explosion effect
        self.create_explosion(dot["x"], dot["y"], color=dot["color"], max_radius=60, duration=15)
          # Check if we need to switch the target color
        if self.current_color_dots_destroyed >= 2:
            self._switch_target_color()
            
        # Check for checkpoint trigger
        if self.total_dots_destroyed % self.checkpoint_trigger == 0:
            self._handle_checkpoint()
            
    def _switch_target_color(self):
        """Switch to a new target color with optimized performance."""
        # Get the next color from unused colors first
        available_colors = [i for i in range(len(self.COLORS_LIST)) if i not in self.used_colors]
        
        # If all colors have been used, reset the used_colors tracking
        if not available_colors:
            self.used_colors = [self.color_idx]
            available_colors = [i for i in range(len(self.COLORS_LIST)) if i not in self.used_colors]
              # Select a random color from available colors
        self.color_idx = random.choice(available_colors)
        self.used_colors.append(self.color_idx)
        
        self.mother_color = self.COLORS_LIST[self.color_idx]
        self.mother_color_name = self.color_names[self.color_idx]
        self.current_color_dots_destroyed = 0
        
        # PERFORMANCE OPTIMIZATION: Batch update target status and count in single loop
        target_count = 0
        for d in self.dots:
            if d["alive"]:
                is_target = (d["color"] == self.mother_color)
                d["target"] = is_target
                if is_target:
                    target_count += 1
                    
        self.target_dots_left = target_count
        
    def _handle_checkpoint(self):
        """Handle checkpoint screen display."""
        # Store the current number of dots left for restoration after checkpoint
        self.dots_before_checkpoint = self.target_dots_left
        
        # Show checkpoint screen
        checkpoint_result = self.checkpoint_screen(self.screen, "colors")
        
        if not checkpoint_result:
            self.running = False
            return
              # If Continue was selected, restore the saved dot count
        self.target_dots_left = self.dots_before_checkpoint
        
    def _update_dots(self):
        """Update dot positions and handle bouncing."""
        for dot in self.dots:
            if not dot["alive"]:
                continue
                
            dot["x"] += dot["dx"]
            dot["y"] += dot["dy"]
            
            # Bounce off walls
            if dot["x"] - dot["radius"] < 0:
                dot["x"] = dot["radius"]
                dot["dx"] *= -1
            if dot["x"] + dot["radius"] > self.width:
                dot["x"] = self.width - dot["radius"]
                dot["dx"] *= -1
            if dot["y"] - dot["radius"] < 0:
                dot["y"] = dot["radius"]
                dot["dy"] *= -1
            if dot["y"] + dot["radius"] > self.height:
                dot["y"] = self.height - dot["radius"]
                dot["dy"] *= -1
                
    def _handle_dot_collisions(self):
        """Handle collisions between dots using sparse spatial grid."""
        if len(self.dots) < 2:
            return
        grid = self._create_spatial_grid()
        checked_pairs = set()
        for (gx, gy), cell_dots in grid.items():
            # Iterate over this cell and neighbouring cells
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    ng = (gx + dx, gy + dy)
                    if ng not in grid:
                        continue
                    neighbor_dots = grid[ng]
                    for i in cell_dots:
                        for j in neighbor_dots:
                            if i >= j:
                                continue
                            pair = (i, j)
                            if pair in checked_pairs:
                                continue
                            checked_pairs.add(pair)
                            dot1 = self.dots[i]
                            dot2 = self.dots[j]
                            if not (dot1["alive"] and dot2["alive"]):
                                continue
                            dx_ = dot1["x"] - dot2["x"]
                            dy_ = dot1["y"] - dot2["y"]
                            dist_sq = dx_ * dx_ + dy_ * dy_
                            max_dist = dot1["radius"] + dot2["radius"]
                            if dist_sq < max_dist * max_dist and dist_sq > 0:
                                self._resolve_collision(dot1, dot2, dx_, dy_, math.sqrt(dist_sq))

    def _resolve_collision(self, dot1, dot2, dx, dy, distance):
        """Resolve collision between two dots."""
        # Normalize direction vector
        if distance > 0:
            nx = dx / distance
            ny = dy / distance
        else:
            nx, ny = 1, 0
            
        # Calculate relative velocity
        dvx = dot1["dx"] - dot2["dx"]
        dvy = dot1["dy"] - dot2["dy"]
        
        # Calculate velocity component along the normal
        velocity_along_normal = dvx * nx + dvy * ny
        
        # Only separate if moving toward each other
        if velocity_along_normal < 0:
            # Separate dots to prevent sticking
            overlap = (dot1["radius"] + dot2["radius"]) - distance
            dot1["x"] += overlap/2 * nx
            dot1["y"] += overlap/2 * ny
            dot2["x"] -= overlap/2 * nx
            dot2["y"] -= overlap/2 * ny
            
            # Swap velocities and reduce speed by 20%
            temp_dx = dot1["dx"]
            temp_dy = dot1["dy"]
            
            dot1["dx"] = dot2["dx"] * 0.8
            dot1["dy"] = dot2["dy"] * 0.8
            
            dot2["dx"] = temp_dx * 0.8
            dot2["dy"] = temp_dy * 0.8
            
            # Create small particle effect at collision point
            collision_x = (dot1["x"] + dot2["x"]) / 2
            collision_y = (dot1["y"] + dot2["y"]) / 2
            for _ in range(3):
                self.particle_manager.create_particle(
                    collision_x, 
                    collision_y,
                    random.choice([dot1["color"], dot2["color"]]),
                    random.randint(5, 10),
                    random.uniform(-2, 2), 
                    random.uniform(-2, 2),
                    10
                )
                
    def _create_collision_enabled_effect(self):
        """Create visual effect when collisions are enabled."""
        for dot in self.dots:
            if dot["alive"]:
                self.particle_manager.create_particle(
                    dot["x"], dot["y"],
                    dot["color"],
                    dot["radius"] * 1.5,
                    0, 0,
                    15
                )
                
    def _draw_frame(self, stars):
        """Draw a single frame of the colors level with visual enhancements."""
        self.frame_counter += 1
        
        # Update glass shatter manager
        self.glass_shatter_manager.update()
        
        # Apply screen shake if active
        offset_x, offset_y = self.glass_shatter_manager.get_screen_shake_offset()
        
        # Fill background based on shatter state
        self.screen.fill(self.glass_shatter_manager.get_background_color())
        
        # Draw cracks
        self.glass_shatter_manager.draw_cracks(self.screen)
        
        # Draw background stars
        for star in stars:
            x, y, radius = star
            y += 1
            pygame.draw.circle(self.screen, (200, 200, 200), (x + offset_x, y + offset_y), radius)
            if y > self.height + radius:
                y = random.randint(-50, -10)
                x = random.randint(0, self.width)
            star[1] = y
            star[0] = x
            
        # VISUAL ENHANCEMENT: Draw dots with depth shading and shimmer effects
        for dot in self.dots:
            if dot["alive"]:
                dot_id = dot.get("id", id(dot))  # Use ID or fallback to object ID
                
                # Get shimmer effect
                shimmer_scale, shimmer_alpha = self._get_shimmer_effect(dot_id)
                
                # Calculate shaded colors
                center_color, edge_color = self._calculate_dot_shading(dot["color"], dot["radius"], dot["target"])
                
                # Apply shimmer to radius
                shimmer_radius = int(dot["radius"] * shimmer_scale)
                
                draw_x = int(dot["x"] + offset_x)
                draw_y = int(dot["y"] + offset_y)
                
                # Draw depth gradient (multiple circles for smooth gradient)
                for i in range(3):
                    gradient_radius = shimmer_radius - (i * shimmer_radius // 4)
                    if gradient_radius > 0:
                        # Interpolate between center and edge color
                        blend_factor = i / 3.0
                        blended_color = tuple(
                            int(center_color[j] * (1 - blend_factor) + edge_color[j] * blend_factor)
                            for j in range(3)
                        )
                        
                        # Create surface with alpha for shimmer effect
                        if i == 0:  # Outermost circle gets shimmer alpha
                            # Use cached surface and adjust alpha on the fly
                            dot_surface = self._get_circle_surface(blended_color, gradient_radius).copy()
                            dot_surface.set_alpha(shimmer_alpha)
                            self.screen.blit(dot_surface, (draw_x - gradient_radius, draw_y - gradient_radius))
                        else:
                            pygame.draw.circle(self.screen, blended_color, 
                                             (draw_x, draw_y), gradient_radius)
                                             
                # Add extra glow for target dots
                if dot["target"]:
                    glow_radius = shimmer_radius + 8
                    glow_intensity = int(50 + 30 * math.sin(self.frame_counter * 0.15))
                    glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (*dot["color"], glow_intensity), 
                                     (glow_radius, glow_radius), glow_radius)
                    self.screen.blit(glow_surface, (draw_x - glow_radius, draw_y - glow_radius))
                                  
        # Draw explosions with offsets
        for explosion in self.explosions[:]:
            if explosion["duration"] > 0:
                self.draw_explosion(explosion, offset_x, offset_y)
                explosion["duration"] -= 1
            else:
                self.explosions.remove(explosion)
        
        # Display HUD info
        self.hud_manager.display_info(
            self.screen, self.score, "color", self.mother_color_name, 
            self.overall_destroyed, 10, "colors", 
            target_dots_left=self.target_dots_left, 
            current_color_dots_destroyed=self.current_color_dots_destroyed
        )
        
        # Show sample target dot reference at top right
        self.hud_manager.display_sample_target(self.screen, self.mother_color, 48)
          # Display collision status
        self.hud_manager.display_collision_status(
            self.screen, self.collision_enabled, 
            self.collision_delay_counter, self.collision_delay_frames
        )        
    def _generate_new_dots(self):
        """Generate new dots when target_dots_left reaches 0 with optimized placement."""
        new_dots_count = 10
        self.target_dots_left = new_dots_count
          # Select next color from unused colors first
        available_colors = [i for i in range(len(self.COLORS_LIST)) if i not in self.used_colors]
        
        if not available_colors:
            self.used_colors = [self.color_idx]
            available_colors = [i for i in range(len(self.COLORS_LIST)) if i not in self.used_colors]
            
        self.color_idx = random.choice(available_colors)
        self.used_colors.append(self.color_idx)
        self.mother_color = self.COLORS_LIST[self.color_idx]
        self.mother_color_name = self.color_names[self.color_idx]
        
        # Reset collision
        self.collision_enabled = False
        self.collision_delay_counter = 0
        
        # Remove dead dots
        self.dots = [d for d in self.dots if d["alive"]]
        
        # PERFORMANCE OPTIMIZATION: Use grid-based placement algorithm
        new_dots_needed = min(85 - len(self.dots), 42)  # Reduced from 100 to 85, and from 50 to 42
        existing_target_dots = sum(1 for d in self.dots if d["color"] == self.mother_color)
        target_dots_needed = max(0, new_dots_count - existing_target_dots)
        
        # Create occupancy grid for faster collision detection during placement
        occupancy_grid = self._create_occupancy_grid()
        
        # Create new dots with optimized placement
        dots_created = 0
        for i in range(new_dots_needed):
            if dots_created >= new_dots_needed:
                break
                
            # PERFORMANCE OPTIMIZATION: Grid-based placement
            position = self._find_valid_position_optimized(occupancy_grid)
            if position is None:
                continue
                
            x, y = position
            dx = random.uniform(-6, 6)
            dy = random.uniform(-6, 6)
            
            # Determine if this dot is a target or distractor
            is_target = False
            if i < target_dots_needed:
                color = self.mother_color
                is_target = True
            else:
                distractor_colors = [c for idx, c in enumerate(self.COLORS_LIST) if idx != self.color_idx]
                color = random.choice(distractor_colors)
                
            dot_id = len(self.dots)
            self.dots.append({
                "x": x, "y": y,
                "dx": dx, "dy": dy,
                "color": color,
                "radius": 48,
                "target": is_target,
                "alive": True,
                "id": dot_id  # Add unique ID for shimmer tracking
            })
            
            # Mark position as occupied in grid
            grid_x = min(int(x // self.grid_size), self.grid_cols - 1)
            grid_y = min(int(y // self.grid_size), self.grid_rows - 1)
            occupancy_grid[grid_y][grid_x] = True
            dots_created += 1
            
        # PERFORMANCE OPTIMIZATION: Single pass target update
        target_count = 0
        for d in self.dots:
            is_target = (d["color"] == self.mother_color)
            d["target"] = is_target
            if is_target and d["alive"]:
                target_count += 1
                
        self.target_dots_left = target_count
        
    def _create_occupancy_grid(self):
        """Create occupancy grid for optimized dot placement."""
        occupancy_grid = [[False for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        
        for dot in self.dots:
            if dot["alive"]:
                grid_x = min(int(dot["x"] // self.grid_size), self.grid_cols - 1)
                grid_y = min(int(dot["y"] // self.grid_size), self.grid_rows - 1)
                occupancy_grid[grid_y][grid_x] = True
                
        return occupancy_grid
        
    def _find_valid_position_optimized(self, occupancy_grid):
        """Find valid position using grid-based approach for better performance."""
        max_attempts = 15
        
        for _ in range(max_attempts):
            grid_x = random.randint(1, self.grid_cols - 2)
            grid_y = random.randint(1, self.grid_rows - 2)
            
            # Check if this grid cell and immediate neighbors are free
            if not occupancy_grid[grid_y][grid_x]:
                x = random.randint(grid_x * self.grid_size + 60, (grid_x + 1) * self.grid_size - 60)
                y = random.randint(grid_y * self.grid_size + 60, (grid_y + 1) * self.grid_size - 60)
                
                x = max(100, min(self.width - 100, x))
                y = max(100, min(self.height - 100, y))
                
                return (x, y)
                
        # Fallback to random position if grid method fails
        return (random.randint(100, self.width - 100), random.randint(100, self.height - 100)) 