import pygame
import random
import math
from settings import (
    LETTER_SPAWN_INTERVAL, WHITE, BLACK, FLAME_COLORS,
    LEVEL_PROGRESS_PATH, SEQUENCES, GROUP_SIZE
)
from universal_class import (
    GlassShatterManager, HUDManager, MultiTouchManager, 
    CheckpointManager, FlamethrowerManager, CenterPieceManager
)


class NumbersLevel:
    """
    Handles the Numbers (123) level gameplay logic.
    Sequential number targeting through numbers 1-10.
    """
    
    def __init__(self, width, height, screen, fonts, small_font, target_font, 
                 particle_manager, glass_shatter_manager, multi_touch_manager, 
                 hud_manager, checkpoint_manager, center_piece_manager, 
                 flamethrower_manager, resource_manager, create_explosion_func, 
                 create_flame_effect_func, apply_explosion_effect_func, 
                 create_particle_func, explosions_list, lasers_list, 
                 draw_explosion_func, game_over_screen_func):
        """
        Initialize the Numbers level.
        
        Args:
            width (int): Screen width
            height (int): Screen height
            screen: Pygame screen surface
            fonts: List of pygame font objects
            small_font: Small font for UI text
            target_font: Font for target numbers
            particle_manager: Particle system manager
            glass_shatter_manager: Glass shatter effect manager
            multi_touch_manager: Multi-touch input manager
            hud_manager: HUD display manager
            checkpoint_manager: Checkpoint screen manager
            center_piece_manager: Center piece swirl manager
            flamethrower_manager: Flamethrower effect manager
            resource_manager: Resource caching manager
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
        self.flamethrower_manager = flamethrower_manager
        self.resource_manager = resource_manager
        self.create_explosion = create_explosion_func
        self.create_flame_effect = create_flame_effect_func
        self.apply_explosion_effect = apply_explosion_effect_func
        self.create_particle = create_particle_func
        self.explosions = explosions_list
        self.lasers = lasers_list
        self.draw_explosion = draw_explosion_func
        self.game_over_screen = game_over_screen_func
        
        # Numbers configuration
        self.sequence = SEQUENCES["numbers"]
        self.groups = [self.sequence[i:i+GROUP_SIZE] for i in range(0, len(self.sequence), GROUP_SIZE)]
        self.TOTAL_NUMBERS = len(self.sequence)
        
        # Game state variables
        self.reset_level_state()
        
    def reset_level_state(self):
        """Reset all level-specific state variables."""
        # Group progression variables
        self.current_group_index = 0
        self.current_group = self.groups[self.current_group_index] if self.groups else []
        self.numbers_to_target = self.current_group.copy()
        self.target_number = self.numbers_to_target[0] if self.numbers_to_target else None
        
        # Counters and tracking
        self.total_destroyed = 0
        self.overall_destroyed = 0
        self.numbers_spawned = 0
        self.numbers_destroyed = 0
        self.last_checkpoint_triggered = 0
        self.score = 0
        
        # Game state
        self.running = True
        self.game_started = False
        self.numbers = []
        self.numbers_to_spawn = self.current_group.copy()
        self.frame_count = 0
        
        # Checkpoint state
        self.checkpoint_waiting = False
        self.checkpoint_delay_frames = 0
        self.just_completed_level = False
        
        # Input state
        self.last_click_time = 0
        self.player_x = self.width // 2
        self.player_y = self.height // 2
        self.player_color_index = 0
        self.click_cooldown = 0
        self.mouse_down = False
        self.mouse_press_time = 0
        self.click_count = 0
        
        # Abilities (maintained for compatibility)
        self.abilities = ["laser", "aoe", "charge_up"]
        self.current_ability = "laser"
        
    def run(self):
        """
        Main entry point to run the numbers level.
        
        Returns:
            bool: False to return to menu, True to restart level
        """
        self.reset_level_state()
        
        # Initialize background stars
        stars = []
        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            radius = random.randint(2, 4)
            stars.append([x, y, radius])
            
        # Main game loop
        clock = pygame.time.Clock()
        
        while self.running:
            # Handle events
            if not self._handle_events():
                return False
                
            # Spawn numbers
            if self.game_started:
                self._spawn_numbers()
                
            # Update physics and collisions
            self._update_numbers()
            
            # Handle checkpoint logic
            self._handle_checkpoint_logic()
            
            # Handle level progression
            progression_result = self._handle_level_progression()
            if progression_result is not None:
                return progression_result
                
            # Draw frame
            self._draw_frame(stars)
            
            # Update frame counter and display
            self.frame_count += 1
            pygame.display.flip()
            clock.tick(50)
            
        return False
        
    def _handle_events(self):
        """Handle all pygame events."""
        for event in pygame.event.get():
            # Handle glass shatter events first
            self.glass_shatter_manager.handle_event(event)
            
            if event.type == pygame.QUIT:
                self.running = False
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Exit the game completely instead of just returning to level menu
                    pygame.quit()
                    exit()
                if event.key == pygame.K_SPACE:
                    self.current_ability = self.abilities[(self.abilities.index(self.current_ability) + 1) % len(self.abilities)]
                    
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.mouse_down:
                    self.mouse_press_time = pygame.time.get_ticks()
                    self.mouse_down = True
                    
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
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
                        
            elif event.type == pygame.FINGERDOWN:
                touch_result = self.multi_touch_manager.handle_touch_down(event)
                if touch_result is None:
                    continue  # Touch was ignored due to cooldown
                touch_id, touch_x, touch_y = touch_result
                if not self.game_started:
                    self.game_started = True
                else:
                    self._handle_click(touch_x, touch_y)
                    
            elif event.type == pygame.FINGERUP:
                touch_result = self.multi_touch_manager.handle_touch_up(event)
                if touch_result is not None:
                    touch_id, last_x, last_y = touch_result
                    
        return True
        
    def _handle_click(self, click_x, click_y):
        """Handle click/touch on screen."""
        # Flag to track if click hit a target
        hit_target = False
        
        # Process Click on Target
        for number_obj in self.numbers[:]:
            if number_obj["rect"].collidepoint(click_x, click_y):
                hit_target = True  # Marked as hit
                if number_obj["value"] == self.target_number:
                    self.score += 10
                    # Common destruction effects
                    self.create_explosion(number_obj["x"], number_obj["y"])
                    self.create_flame_effect(self.player_x, self.player_y - 80, number_obj["x"], number_obj["y"])
                    self.center_piece_manager.trigger_convergence(number_obj["x"], number_obj["y"])
                    self.apply_explosion_effect(number_obj["x"], number_obj["y"], 150, self.numbers)

                    # Add visual feedback particles
                    for i in range(20):
                        self.create_particle(
                            number_obj["x"], number_obj["y"],
                            random.choice(FLAME_COLORS),
                            random.randint(40, 80),
                            random.uniform(-2, 2), random.uniform(-2, 2),
                            20
                        )

                    # Remove number and update counts
                    self.numbers.remove(number_obj)
                    self.numbers_destroyed += 1

                    # Update target
                    if self.target_number in self.numbers_to_target:
                        self.numbers_to_target.remove(self.target_number)
                    if self.numbers_to_target:
                        self.target_number = self.numbers_to_target[0]

                    break  # Exit loop after processing one hit
                else:
                    # Add feedback for clicking wrong target (shake will be handled by misclick if needed)
                    pass
        
        # If no target was hit, add a crack to the screen
        if not hit_target and self.game_started:
            self.glass_shatter_manager.handle_misclick(click_x, click_y)
            
    def _spawn_numbers(self):
        """Spawn numbers at regular intervals."""
        if self.numbers_to_spawn:
            if self.frame_count % LETTER_SPAWN_INTERVAL == 0:
                number_value = self.numbers_to_spawn.pop(0)
                number_obj = {
                    "value": number_value,
                    "x": random.randint(50, self.width - 50),
                    "y": -50,                    "rect": pygame.Rect(0, 0, 0, 0),  # Will be updated when drawn
                    "size": 240,  # Fixed size
                    "dx": random.choice([-1, -0.5, 0.5, 1]) * 1.5,  # Horizontal drift
                    "dy": random.choice([1, 1.5]) * 1.5 * 1.2,  # 20% faster fall speed
                    "can_bounce": False,  # Start without bouncing
                    "mass": random.uniform(40, 60)  # Mass for collisions
                }
                self.numbers.append(number_obj)
                self.numbers_spawned += 1
                
    def _update_numbers(self):
        """Update physics and collisions for all numbers."""
        # Update positions and bouncing
        for number_obj in self.numbers[:]:
            number_obj["x"] += number_obj["dx"]
            number_obj["y"] += number_obj["dy"]

            # Bouncing Logic
            if not number_obj["can_bounce"] and number_obj["y"] > self.height // 5:
                number_obj["can_bounce"] = True

            if number_obj["can_bounce"]:
                bounce_dampening = 0.8

                # Left/Right Walls
                if number_obj["x"] <= 0 + number_obj.get("size", 50)/2:
                    number_obj["x"] = 0 + number_obj.get("size", 50)/2
                    number_obj["dx"] = abs(number_obj["dx"]) * bounce_dampening
                elif number_obj["x"] >= self.width - number_obj.get("size", 50)/2:
                    number_obj["x"] = self.width - number_obj.get("size", 50)/2
                    number_obj["dx"] = -abs(number_obj["dx"]) * bounce_dampening

                # Top/Bottom Walls
                if number_obj["y"] <= 0 + number_obj.get("size", 50)/2:
                    number_obj["y"] = 0 + number_obj.get("size", 50)/2
                    number_obj["dy"] = abs(number_obj["dy"]) * bounce_dampening
                elif number_obj["y"] >= self.height - number_obj.get("size", 50)/2:
                    number_obj["y"] = self.height - number_obj.get("size", 50)/2
                    number_obj["dy"] = -abs(number_obj["dy"]) * bounce_dampening
                    # Push horizontally away from edge on bottom bounce
                    number_obj["dx"] *= bounce_dampening
                    if number_obj["x"] < self.width / 2:
                        number_obj["dx"] += random.uniform(0.1, 0.3)
                    else:
                        number_obj["dx"] -= random.uniform(0.1, 0.3)
                        
        # Handle collisions between numbers
        self._handle_number_collisions()
        
    def _handle_number_collisions(self):
        """Handle collisions between falling numbers."""
        # PERFORMANCE: Reduce collision check frequency
        from Display_settings import PERFORMANCE_SETTINGS
        collision_frequency = PERFORMANCE_SETTINGS.get(self.center_piece_manager.display_mode, PERFORMANCE_SETTINGS["DEFAULT"])["collision_check_frequency"]
        if self.frame_count % collision_frequency == 0:
            for i, number_obj1 in enumerate(self.numbers):
                for j in range(i + 1, len(self.numbers)):
                    number_obj2 = self.numbers[j]
                    dx = number_obj2["x"] - number_obj1["x"]
                    dy = number_obj2["y"] - number_obj1["y"]
                    distance_sq = dx*dx + dy*dy

                    # Collision radius calculation
                    radius1 = number_obj1.get("size", self.target_font.get_height()) / 1.8
                    radius2 = number_obj2.get("size", self.target_font.get_height()) / 1.8
                    min_distance = radius1 + radius2
                    min_distance_sq = min_distance * min_distance

                    if distance_sq < min_distance_sq and distance_sq > 0:
                        distance = math.sqrt(distance_sq)
                        # Normalize collision vector
                        nx = dx / distance
                        ny = dy / distance

                        # Resolve interpenetration
                        overlap = min_distance - distance
                        total_mass = number_obj1["mass"] + number_obj2["mass"]
                        push_factor = overlap / total_mass
                        number_obj1["x"] -= nx * push_factor * number_obj2["mass"]
                        number_obj1["y"] -= ny * push_factor * number_obj2["mass"]
                        number_obj2["x"] += nx * push_factor * number_obj1["mass"]
                        number_obj2["y"] += ny * push_factor * number_obj1["mass"]

                        # Calculate collision response
                        dvx = number_obj1["dx"] - number_obj2["dx"]
                        dvy = number_obj1["dy"] - number_obj2["dy"]
                        dot_product = dvx * nx + dvy * ny
                        impulse = (2 * dot_product) / total_mass
                        bounce_factor = 0.85

                        # Apply impulse
                        number_obj1["dx"] -= impulse * number_obj2["mass"] * nx * bounce_factor
                        number_obj1["dy"] -= impulse * number_obj2["mass"] * ny * bounce_factor
                        number_obj2["dx"] += impulse * number_obj1["mass"] * nx * bounce_factor
                        number_obj2["dy"] += impulse * number_obj1["mass"] * ny * bounce_factor
                        
    def _handle_checkpoint_logic(self):
        """Handle checkpoint display logic."""
        self.overall_destroyed = self.total_destroyed + self.numbers_destroyed

        # If waiting for animations before showing checkpoint screen
        if self.checkpoint_waiting:
            # Only show checkpoint after delay AND when animations are mostly complete
            if (self.checkpoint_delay_frames <= 0 and 
                len(self.explosions) <= 1 and 
                len(self.lasers) <= 1 and 
                self.flamethrower_manager.get_count() <= 1 and 
                not self.center_piece_manager.particles_converging):
                self.checkpoint_waiting = False
                self.game_started = False  # Pause the game
                if not self.checkpoint_manager.show_checkpoint_screen(self.screen, "numbers"):
                    self.running = False  # Exit game loop to return to menu
                else:
                    self.game_started = True  # Resume the current level
            else:
                self.checkpoint_delay_frames -= 1

        # Check if we hit a new checkpoint threshold
        elif (self.overall_destroyed > 0 and 
              self.overall_destroyed % 10 == 0 and 
              self.overall_destroyed // 10 > self.last_checkpoint_triggered and 
              not self.just_completed_level):
            self.last_checkpoint_triggered = self.overall_destroyed // 10
            self.checkpoint_waiting = True
            self.checkpoint_delay_frames = 60  # Wait ~1 second for animations
            
    def _handle_level_progression(self):
        """Handle level progression and completion."""
        # Check if the current group is finished
        if not self.numbers and not self.numbers_to_spawn and self.numbers_to_target == []:
            self.total_destroyed += self.numbers_destroyed
            self.current_group_index += 1
            self.just_completed_level = True

            if self.current_group_index < len(self.groups):
                # Start Next Group
                self.current_group = self.groups[self.current_group_index]
                self.numbers_to_spawn = self.current_group.copy()
                self.numbers_to_target = self.current_group.copy()
                if self.numbers_to_target:
                    self.target_number = self.numbers_to_target[0]
                else:
                    print(f"Warning: Group {self.current_group_index} is empty.")
                    self.running = False
                    return False

                # Reset group-specific counters
                self.numbers_destroyed = 0
                self.numbers_spawned = 0
                self.just_completed_level = False
                self.game_started = True
                self.last_checkpoint_triggered = self.overall_destroyed // 10

            else:
                # All Groups Completed (Level Finished)
                pygame.time.delay(500)  # Brief delay
                if not self.checkpoint_manager.show_checkpoint_screen(self.screen, "numbers"):
                    self.running = False  # Exit game loop to return to menu
                else:
                    self.running = False  # Return to menu since level is complete
                
                return False  # Exit the loop immediately
                
        return None
        
    def _draw_frame(self, stars):
        """Draw the complete game frame."""
        # Apply screen shake if active
        offset_x, offset_y = self.glass_shatter_manager.get_screen_shake_offset()

        # Update glass shatter manager
        self.glass_shatter_manager.update()
        
        # Fill background based on shatter state
        self.screen.fill(self.glass_shatter_manager.get_background_color())

        # Draw cracks
        self.glass_shatter_manager.draw_cracks(self.screen)

        # Draw background elements (stars)
        self._draw_stars(stars, offset_x, offset_y)

        # Draw center piece (swirl particles + target display)
        self.center_piece_manager.update_and_draw(self.screen, self.target_number, "numbers", offset_x, offset_y)

        # Update and draw falling numbers
        self._update_and_draw_numbers(offset_x, offset_y)

        # Process flamethrower effects
        self.flamethrower_manager.update()
        self.flamethrower_manager.draw(self.screen, offset_x, offset_y)
        
        # Process legacy lasers
        self._process_lasers(offset_x, offset_y)

        # Process explosions
        self._process_explosions(offset_x, offset_y)

        # Draw general particles
        self.particle_manager.update()
        self.particle_manager.draw(self.screen, offset_x, offset_y)
        
        # Display HUD info
        self.hud_manager.display_info(self.screen, self.score, self.current_ability, 
                                     self.target_number, self.overall_destroyed, 
                                     self.TOTAL_NUMBERS, "numbers")
                                     
    def _draw_stars(self, stars, offset_x, offset_y):
        """Draw and update background stars."""
        for star in stars:
            x, y, radius = star
            y += 1  # Slower star movement speed
            pygame.draw.circle(self.screen, (200, 200, 200), 
                             (x + offset_x, y + offset_y), radius)
            if y > self.height + radius:  # Reset when fully off screen
                y = random.randint(-50, -10)
                x = random.randint(0, self.width)
            star[1] = y
            star[0] = x
            
    def _update_and_draw_numbers(self, offset_x, offset_y):
        """Update and draw falling numbers."""
        for number_obj in self.numbers[:]:
            # Draw the number
            draw_pos_x = int(number_obj["x"] + offset_x)
            draw_pos_y = int(number_obj["y"] + offset_y)

            # Use gray for non-target numbers, black for the target number
            text_color = BLACK if number_obj["value"] == self.target_number else (150, 150, 150)
            
            # Use cached font surface if available
            try:
                cached_surface = self.resource_manager.get_falling_object_surface("numbers", number_obj["value"], text_color)
                text_rect = cached_surface.get_rect(center=(draw_pos_x, draw_pos_y))
                number_obj["rect"] = text_rect
                self.screen.blit(cached_surface, text_rect)
            except:
                # Fallback: Original rendering method
                text_surface = self.target_font.render(number_obj["value"], True, text_color)
                text_rect = text_surface.get_rect(center=(draw_pos_x, draw_pos_y))
                number_obj["rect"] = text_rect
                self.screen.blit(text_surface, text_rect)
                
    def _process_lasers(self, offset_x, offset_y):
        """Process legacy laser effects."""
        for laser in self.lasers[:]:
            if laser["duration"] > 0:
                if laser["type"] != "flamethrower":
                    pygame.draw.line(self.screen, random.choice(laser.get("colors", FLAME_COLORS)),
                                   (laser["start_pos"][0] + offset_x, laser["start_pos"][1] + offset_y),
                                   (laser["end_pos"][0] + offset_x, laser["end_pos"][1] + offset_y),
                                    random.choice(laser.get("widths", [5, 10, 15])))
                laser["duration"] -= 1
            else:
                self.lasers.remove(laser)
                
    def _process_explosions(self, offset_x, offset_y):
        """Process explosion effects."""
        for explosion in self.explosions[:]:
            if explosion["duration"] > 0:
                self.draw_explosion(explosion, offset_x, offset_y)
                explosion["duration"] -= 1
            else:
                self.explosions.remove(explosion) 