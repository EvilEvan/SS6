import pygame
import random
import math
from settings import (
    SEQUENCES, GROUP_SIZE, LETTER_SPAWN_INTERVAL, FLAME_COLORS,
    LEVEL_PROGRESS_PATH, WHITE, BLACK
)
from Display_settings import PERFORMANCE_SETTINGS
from universal_class import GlassShatterManager, HUDManager, MultiTouchManager, CheckpointManager, FlamethrowerManager


class ShapesLevel:
    """
    Handles the Shapes level gameplay logic.
    """
    
    def __init__(self, width, height, screen, fonts, small_font, target_font, 
                 particle_manager, glass_shatter_manager, multi_touch_manager, 
                 hud_manager, checkpoint_manager, center_piece_manager, create_explosion_func, 
                 create_flame_effect_func, apply_explosion_effect_func, create_particle_func,
                 explosions_list, lasers_list, draw_explosion_func, game_over_screen_func):
        """
        Initialize the Shapes level.
        
        Args:
            width (int): Screen width
            height (int): Screen height
            screen: Pygame screen surface
            fonts: List of fonts for different sizes
            small_font: Small font for UI text
            target_font: Large font for target display
            particle_manager: Particle system manager
            glass_shatter_manager: Glass shatter effect manager
            multi_touch_manager: Multi-touch input manager
            hud_manager: HUD display manager
            checkpoint_manager: Checkpoint screen manager
            center_piece_manager: Center piece manager for swirl particles and target display
            create_explosion_func: Function to create explosion effects
            create_flame_effect_func: Function to create flame effects
            apply_explosion_effect_func: Function to apply explosion push effects
            create_particle_func: Function to create individual particles
            explosions_list: Reference to the global explosions list
            lasers_list: Reference to the global lasers list
            draw_explosion_func: Function to draw explosion effects
            game_over_screen_func: Function to show game over screen
        """
        self.width = width
        self.height = height
        self.screen = screen
        self.fonts = fonts
        self.small_font = small_font
        self.target_font = target_font
        self.particle_manager = particle_manager
        self.glass_shatter_manager = glass_shatter_manager
        self.multi_touch_manager = multi_touch_manager
        self.hud_manager = hud_manager
        self.checkpoint_manager = checkpoint_manager
        self.center_piece_manager = center_piece_manager
        self.create_explosion = create_explosion_func
        self.create_flame_effect = create_flame_effect_func
        self.apply_explosion_effect = apply_explosion_effect_func
        self.create_particle = create_particle_func
        self.explosions = explosions_list
        self.lasers = lasers_list
        self.draw_explosion = draw_explosion_func
        self.game_over_screen = game_over_screen_func
        
        # Initialize flamethrower manager
        self.flamethrower_manager = FlamethrowerManager()
        
        # Shapes configuration
        self.sequence = SEQUENCES["shapes"]
        self.groups = [self.sequence[i:i+GROUP_SIZE] for i in range(0, len(self.sequence), GROUP_SIZE)]
        self.TOTAL_LETTERS = len(self.sequence)
        
        # Game state variables
        self.reset_level_state()
        
    def reset_level_state(self):
        """Reset all level-specific state variables."""
        self.current_group_index = 0
        self.current_group = self.groups[self.current_group_index] if self.groups else []
        self.letters_to_target = self.current_group.copy()
        self.target_letter = self.letters_to_target[0] if self.letters_to_target else None
        self.total_destroyed = 0
        self.overall_destroyed = 0
        self.running = True
        self.letters = []
        self.letters_spawned = 0
        self.letters_destroyed = 0
        self.last_checkpoint_triggered = 0
        self.checkpoint_waiting = False
        self.checkpoint_delay_frames = 0
        self.just_completed_level = False
        self.score = 0
        self.abilities = ["laser", "aoe", "charge_up"]
        self.current_ability = "laser"
        self.game_started = False
        self.last_click_time = 0
        self.player_x = self.width // 2
        self.player_y = self.height // 2
        self.player_color_index = 0
        self.click_cooldown = 0
        self.mouse_down = False
        self.mouse_press_time = 0
        self.click_count = 0
        self.letters_to_spawn = self.current_group.copy()
        self.frame_count = 0
        self.shapes_first_round_completed = False
        
        # Center piece manager will handle swirl particles
        
        # Check if shapes was completed before
        try:
            with open(LEVEL_PROGRESS_PATH, "r") as f:
                progress = f.read().strip()
                if "shapes_completed" in progress:
                    self.shapes_completed = True
        except:
            self.shapes_completed = False
        
    def run(self):
        """
        Main entry point to run the shapes level.
        
        Returns:
            bool: False to return to menu, True to restart level
        """
        self.reset_level_state()
        
        # Reset global effects that could persist between levels
        self.multi_touch_manager.reset()
        self.glass_shatter_manager.reset()
        self.flamethrower_manager.clear()
        self.center_piece_manager.reset()
        
        # Initialize background stars
        stars = []
        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            radius = random.randint(2, 4)
            stars.append([x, y, radius])
        
        # Run main game loop
        return self._main_game_loop(stars)
        
    def _main_game_loop(self, stars):
        """Main game loop for the shapes level."""
        clock = pygame.time.Clock()
        
        while self.running:
            # Handle events
            if not self._handle_events():
                return False
                
            # Spawning items
            if self.game_started:
                self._spawn_items()
            
            # Update and draw frame
            self._update_and_draw_frame(stars)
            
            # Handle checkpoint logic
            if not self._handle_checkpoint_logic():
                return False
                
            # Handle level progression
            progression_result = self._handle_level_progression()
            if progression_result is not None:
                return progression_result
            
            # Update frame counter and clock
            self.frame_count += 1
            clock.tick(50)
        
        return True
        
    def _handle_events(self):
        """Handle all pygame events."""
        for event in pygame.event.get():
            # Handle glass shatter events first
            self.glass_shatter_manager.handle_event(event)
            
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                if event.key == pygame.K_SPACE:
                    self.current_ability = self.abilities[(self.abilities.index(self.current_ability) + 1) % len(self.abilities)]
            
            # Handle mouse events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.mouse_down:
                    self.mouse_press_time = pygame.time.get_ticks()
                    self.mouse_down = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                release_time = pygame.time.get_ticks()
                self.mouse_down = False
                duration = release_time - self.mouse_press_time
                if duration <= 1000:  # Check if it's a click (not a hold)
                    self.click_count += 1
                    if not self.game_started:
                        self.game_started = True
                    else:
                        click_x, click_y = pygame.mouse.get_pos()
                        self._handle_click(click_x, click_y)
            
            # Handle touch events
            elif event.type == pygame.FINGERDOWN:
                touch_result = self.multi_touch_manager.handle_touch_down(event)
                if touch_result is None:
                    continue
                touch_id, touch_x, touch_y = touch_result
                if not self.game_started:
                    self.game_started = True
                else:
                    self._handle_click(touch_x, touch_y)
            elif event.type == pygame.FINGERUP:
                touch_result = self.multi_touch_manager.handle_touch_up(event)
                
        return True
        
    def _handle_click(self, click_x, click_y):
        """Handle click/touch on the screen."""
        hit_target = False
        
        # Process click on target
        for letter_obj in self.letters[:]:
            if letter_obj["rect"].collidepoint(click_x, click_y):
                hit_target = True
                if letter_obj["value"] == self.target_letter:
                    self.score += 10
                    # Common destruction effects
                    self.create_explosion(letter_obj["x"], letter_obj["y"])
                    self.flamethrower_manager.create_flamethrower(self.player_x, self.player_y - 80, letter_obj["x"], letter_obj["y"])
                    self.center_piece_manager.trigger_convergence(letter_obj["x"], letter_obj["y"])
                    self.apply_explosion_effect(letter_obj["x"], letter_obj["y"], 150, self.letters)
                    
                    # Add visual feedback particles
                    for i in range(20):
                        self.create_particle(
                            letter_obj["x"], letter_obj["y"],
                            random.choice(FLAME_COLORS),
                            random.randint(40, 80),
                            random.uniform(-2, 2), random.uniform(-2, 2),
                            20
                        )
                    
                    # Remove letter and update counts
                    self.letters.remove(letter_obj)
                    self.letters_destroyed += 1
                    
                    # Update target
                    if self.target_letter in self.letters_to_target:
                        self.letters_to_target.remove(self.target_letter)
                    if self.letters_to_target:
                        self.target_letter = self.letters_to_target[0]
                    
                    break
                else:
                    # Feedback for clicking wrong target
                    pass  # Could add shake effect here
        
        # If no target was hit, add a crack to the screen
        if not hit_target and self.game_started:
            self.glass_shatter_manager.handle_misclick(click_x, click_y)
            
    def _spawn_items(self):
        """Handle spawning of falling shapes."""
        if self.letters_to_spawn:
            if self.frame_count % LETTER_SPAWN_INTERVAL == 0:
                item_value = self.letters_to_spawn.pop(0)
                letter_obj = {
                    "value": item_value,
                    "x": random.randint(50, self.width - 50),
                    "y": -50,
                    "rect": pygame.Rect(0, 0, 0, 0),  # Will be updated when drawn
                    "size": 240,  # doubled from 120 to 240 for 100% increase
                    "dx": random.choice([-1, -0.5, 0.5, 1]) * 1.5,
                    "dy": random.choice([1, 1.5]) * 1.5,
                    "can_bounce": False,
                    "mass": random.uniform(40, 60)
                }
                self.letters.append(letter_obj)
                self.letters_spawned += 1
                
    def _update_and_draw_frame(self, stars):
        """Update and draw the current frame."""
        # Apply screen shake if active
        offset_x, offset_y = self.glass_shatter_manager.get_screen_shake_offset()
        
        # Update glass shatter manager
        self.glass_shatter_manager.update()
        
        # Fill background based on shatter state
        self.screen.fill(self.glass_shatter_manager.get_background_color())
        
        # Draw cracks
        self.glass_shatter_manager.draw_cracks(self.screen)
        
        # Draw background stars
        self._draw_stars(stars, offset_x, offset_y)
        
        # Draw center piece (swirl particles + target display)
        self.center_piece_manager.update_and_draw(self.screen, self.target_letter, "shapes", offset_x, offset_y)
        
        # Update and draw falling shapes
        self._update_and_draw_shapes(offset_x, offset_y)
        
        # Handle collisions between shapes with performance optimization
        collision_frequency = PERFORMANCE_SETTINGS.get(self.center_piece_manager.display_mode, PERFORMANCE_SETTINGS["DEFAULT"])["collision_check_frequency"]
        if self.frame_count % collision_frequency == 0:
            self._handle_shape_collisions()
        
        # Process flamethrower effects
        self.flamethrower_manager.update()
        self.flamethrower_manager.draw(self.screen, offset_x, offset_y)
        
        # Process legacy lasers / flame effects
        self._process_lasers(offset_x, offset_y)
        
        # Process explosions
        self._process_explosions(offset_x, offset_y)
        
        # Draw particles
        self.particle_manager.update()
        self.particle_manager.draw(self.screen, offset_x, offset_y)
        
        # Display HUD
        self.hud_manager.display_info(self.screen, self.score, self.current_ability, 
                                     self.target_letter, self.overall_destroyed + self.letters_destroyed, 
                                     self.TOTAL_LETTERS, "shapes")
        
        # Update display
        pygame.display.flip()
        
    def _draw_stars(self, stars, offset_x, offset_y):
        """Draw and update background stars."""
        for star in stars:
            x, y, radius = star
            y += 1
            pygame.draw.circle(self.screen, (200, 200, 200), (x + offset_x, y + offset_y), radius)
            if y > self.height + radius:
                y = random.randint(-50, -10)
                x = random.randint(0, self.width)
            star[1] = y
            star[0] = x
            
    # Center target drawing now handled by CenterPieceManager
            
    def _update_and_draw_shapes(self, offset_x, offset_y):
        """Update and draw falling shapes."""
        for letter_obj in self.letters[:]:
            # Update position
            letter_obj["x"] += letter_obj["dx"]
            letter_obj["y"] += letter_obj["dy"]
            
            # Bouncing logic
            if not letter_obj["can_bounce"] and letter_obj["y"] > self.height // 5:
                letter_obj["can_bounce"] = True
                
            if letter_obj["can_bounce"]:
                bounce_dampening = 0.8
                
                # Left/Right walls
                if letter_obj["x"] <= 0 + letter_obj["size"]/2:
                    letter_obj["x"] = 0 + letter_obj["size"]/2
                    letter_obj["dx"] = abs(letter_obj["dx"]) * bounce_dampening
                elif letter_obj["x"] >= self.width - letter_obj["size"]/2:
                    letter_obj["x"] = self.width - letter_obj["size"]/2
                    letter_obj["dx"] = -abs(letter_obj["dx"]) * bounce_dampening
                    
                # Top/Bottom walls
                if letter_obj["y"] <= 0 + letter_obj["size"]/2:
                    letter_obj["y"] = 0 + letter_obj["size"]/2
                    letter_obj["dy"] = abs(letter_obj["dy"]) * bounce_dampening
                elif letter_obj["y"] >= self.height - letter_obj["size"]/2:
                    letter_obj["y"] = self.height - letter_obj["size"]/2
                    letter_obj["dy"] = -abs(letter_obj["dy"]) * bounce_dampening
                    letter_obj["dx"] *= bounce_dampening
                    if letter_obj["x"] < self.width / 2:
                        letter_obj["dx"] += random.uniform(0.1, 0.3)
                    else:
                        letter_obj["dx"] -= random.uniform(0.1, 0.3)
            
            # Draw the shape
            self._draw_shape(letter_obj, offset_x, offset_y)
            
    def _draw_shape(self, letter_obj, offset_x, offset_y):
        """Draw a single shape."""
        draw_pos_x = int(letter_obj["x"] + offset_x)
        draw_pos_y = int(letter_obj["y"] + offset_y)
        value = letter_obj["value"]
        size = letter_obj["size"]
        pos = (draw_pos_x, draw_pos_y)
        color = BLACK  # Use BLACK for falling shapes (as in original)
        
        if value == "Rectangle":
            rect = pygame.Rect(pos[0] - int(size*1.5)//2, pos[1] - size//2, int(size*1.5), size)
            letter_obj["rect"] = rect
            pygame.draw.rect(self.screen, color, rect, 6)
        elif value == "Square":
            rect = pygame.Rect(pos[0]-size//2, pos[1]-size//2, size, size)
            letter_obj["rect"] = rect
            pygame.draw.rect(self.screen, color, rect, 6)
        elif value == "Circle":
            rect = pygame.Rect(pos[0]-size//2, pos[1]-size//2, size, size)
            letter_obj["rect"] = rect
            pygame.draw.circle(self.screen, color, pos, size//2, 6)
        elif value == "Triangle":
            points = [
                (pos[0], pos[1] - size//2),
                (pos[0] - size//2, pos[1] + size//2),
                (pos[0] + size//2, pos[1] + size//2)
            ]
            letter_obj["rect"] = pygame.Rect(pos[0]-size//2, pos[1]-size//2, size, size)
            pygame.draw.polygon(self.screen, color, points, 6)
        elif value == "Pentagon":
            points = []
            r_size = size // 2
            for i in range(5):
                angle = math.radians(72 * i - 90)
                points.append((pos[0] + r_size * math.cos(angle), pos[1] + r_size * math.sin(angle)))
            letter_obj["rect"] = pygame.Rect(pos[0]-size//2, pos[1]-size//2, size, size)
            pygame.draw.polygon(self.screen, color, points, 6)
            
    def _handle_shape_collisions(self):
        """Handle collisions between falling shapes."""
        for i, letter_obj1 in enumerate(self.letters):
            for j in range(i + 1, len(self.letters)):
                letter_obj2 = self.letters[j]
                dx = letter_obj2["x"] - letter_obj1["x"]
                dy = letter_obj2["y"] - letter_obj1["y"]
                distance_sq = dx*dx + dy*dy
                
                radius1 = letter_obj1["size"] / 1.8
                radius2 = letter_obj2["size"] / 1.8
                min_distance = radius1 + radius2
                min_distance_sq = min_distance * min_distance
                
                if distance_sq < min_distance_sq and distance_sq > 0:
                    distance = math.sqrt(distance_sq)
                    nx = dx / distance
                    ny = dy / distance
                    
                    # Resolve interpenetration
                    overlap = min_distance - distance
                    total_mass = letter_obj1["mass"] + letter_obj2["mass"]
                    push_factor = overlap / total_mass
                    letter_obj1["x"] -= nx * push_factor * letter_obj2["mass"]
                    letter_obj1["y"] -= ny * push_factor * letter_obj2["mass"]
                    letter_obj2["x"] += nx * push_factor * letter_obj1["mass"]
                    letter_obj2["y"] += ny * push_factor * letter_obj1["mass"]
                    
                    # Calculate collision response
                    dvx = letter_obj1["dx"] - letter_obj2["dx"]
                    dvy = letter_obj1["dy"] - letter_obj2["dy"]
                    dot_product = dvx * nx + dvy * ny
                    impulse = (2 * dot_product) / total_mass
                    bounce_factor = 0.85
                    
                    letter_obj1["dx"] -= impulse * letter_obj2["mass"] * nx * bounce_factor
                    letter_obj1["dy"] -= impulse * letter_obj2["mass"] * ny * bounce_factor
                    letter_obj2["dx"] += impulse * letter_obj1["mass"] * nx * bounce_factor
                    letter_obj2["dy"] += impulse * letter_obj1["mass"] * ny * bounce_factor
                    
    def _process_lasers(self, offset_x, offset_y):
        """Process and draw legacy laser effects (non-flamethrower)."""
        for laser in self.lasers[:]:
            if laser["duration"] > 0:
                # Only process non-flamethrower effects here
                if laser["type"] != "flamethrower":
                    pygame.draw.line(self.screen, random.choice(laser.get("colors", FLAME_COLORS)),
                                     (laser["start_pos"][0] + offset_x, laser["start_pos"][1] + offset_y),
                                     (laser["end_pos"][0] + offset_x, laser["end_pos"][1] + offset_y),
                                      random.choice(laser.get("widths", [5, 10, 15])))
                laser["duration"] -= 1
            else:
                self.lasers.remove(laser)

                    
    def _process_explosions(self, offset_x, offset_y):
        """Process and draw explosions."""
        for explosion in self.explosions[:]:
            if explosion["duration"] > 0:
                self.draw_explosion(explosion, offset_x, offset_y)
                explosion["duration"] -= 1
            else:
                self.explosions.remove(explosion)
                
    def _handle_checkpoint_logic(self):
        """Handle checkpoint display logic."""
        self.overall_destroyed = self.total_destroyed + self.letters_destroyed
        
        # If waiting for animations before showing checkpoint screen
        if self.checkpoint_waiting:
            if self.checkpoint_delay_frames <= 0 and len(self.explosions) <= 1 and len(self.lasers) <= 1 and self.flamethrower_manager.get_count() <= 1 and not self.particles_converging:
                self.checkpoint_waiting = False
                self.game_started = False
                if not self.checkpoint_manager.show_checkpoint_screen(self.screen, "shapes"):
                    self.running = False
                    return False
                else:
                    self.game_started = True
            else:
                self.checkpoint_delay_frames -= 1
                
        # Check if we hit a new checkpoint threshold
        elif (self.overall_destroyed > 0 and self.overall_destroyed % 10 == 0 and 
              self.overall_destroyed // 10 > self.last_checkpoint_triggered and 
              not self.just_completed_level):
            self.last_checkpoint_triggered = self.overall_destroyed // 10
            self.checkpoint_waiting = True
            self.checkpoint_delay_frames = 60
            
        return True
        
    def _handle_level_progression(self):
        """Handle level progression and completion logic."""
        # Check if the current group is finished
        if not self.letters and not self.letters_to_spawn and self.letters_to_target == []:
            self.total_destroyed += self.letters_destroyed
            self.current_group_index += 1
            self.just_completed_level = True
            
            # For shapes mode, make shapes rain down a second time after first round completion
            if not self.shapes_first_round_completed:
                self.shapes_first_round_completed = True
                # Reset the group index to start over
                self.current_group_index = 0
                self.current_group = self.groups[self.current_group_index]
                self.letters_to_spawn = self.current_group.copy()
                self.letters_to_target = self.current_group.copy()
                if self.letters_to_target:
                    self.target_letter = self.letters_to_target[0]
                # Reset group-specific counters
                self.letters_destroyed = 0
                self.letters_spawned = 0
                self.just_completed_level = False
                self.game_started = True
                self.last_checkpoint_triggered = self.overall_destroyed // 10
                return None  # Continue the level
                
            elif self.current_group_index < len(self.groups):
                # Start next group
                self.current_group = self.groups[self.current_group_index]
                self.letters_to_spawn = self.current_group.copy()
                self.letters_to_target = self.current_group.copy()
                if self.letters_to_target:
                    self.target_letter = self.letters_to_target[0]
                else:
                    self.running = False
                    return False
                    
                # Reset group-specific counters
                self.letters_destroyed = 0
                self.letters_spawned = 0
                self.just_completed_level = False
                self.game_started = True
                self.last_checkpoint_triggered = self.overall_destroyed // 10
                return None  # Continue the level
                
            else:
                # All groups completed
                if self.shapes_first_round_completed:
                    self.total_destroyed += self.letters_destroyed
                    # Mark shapes as completed
                    try:
                        with open(LEVEL_PROGRESS_PATH, "w") as f:
                            f.write("shapes_completed")
                    except:
                        pass
                    
                    # Show checkpoint screen after completing shapes mode
                    pygame.time.delay(500)
                    if self.checkpoint_manager.show_checkpoint_screen(self.screen, "shapes"):
                        return True  # Signal to restart the level
                    else:
                        return False  # Return to menu
                        
        return None  # Continue normal gameplay
        
    # Swirl particle methods now handled by CenterPieceManager 