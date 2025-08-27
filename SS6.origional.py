import pygame
import random
import math
from settings import (
    COLORS_COLLISION_DELAY, LEVEL_PROGRESS_PATH, WHITE, BLACK, FLAME_COLORS, LASER_EFFECTS,
    LETTER_SPAWN_INTERVAL, SEQUENCES, GAME_MODES, GROUP_SIZE
)
from Display_settings import (
    DISPLAY_MODES, DEFAULT_MODE, DISPLAY_SETTINGS_PATH,
    FONT_SIZES, MAX_PARTICLES as PARTICLES_SETTINGS,
    MAX_EXPLOSIONS as EXPLOSIONS_SETTINGS,
    MAX_SWIRL_PARTICLES as SWIRL_SETTINGS,
    MOTHER_RADIUS, detect_display_type, load_display_mode, save_display_mode,
    PERFORMANCE_SETTINGS
)
from universal_class import GlassShatterManager, HUDManager, CheckpointManager, FlamethrowerManager, CenterPieceManager
from welcome_screen import welcome_screen, level_menu, draw_neon_button
from levels import ColorsLevel, ShapesLevel, AlphabetLevel, NumbersLevel, CLCaseLevel

pygame.init()

# Allow only the necessary events (including multi-touch)
pygame.event.set_allowed([
    pygame.FINGERDOWN,
    pygame.FINGERUP,
    pygame.FINGERMOTION,
    pygame.QUIT,
    pygame.KEYDOWN,
    pygame.MOUSEBUTTONDOWN,
    pygame.MOUSEBUTTONUP,
])

# Get the screen size and initialize display in fullscreen
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Super Student")

# Initialize with default mode first
DISPLAY_MODE = DEFAULT_MODE

# Load display mode from settings or auto-detect
DISPLAY_MODE = load_display_mode()

# Import ResourceManager
from utils.resource_manager import ResourceManager
from utils.particle_system import ParticleManager
from utils.level_resource_manager import LevelResourceManager
from universal_class import MultiTouchManager

# Initialize particle manager globally
particle_manager = None
multi_touch_manager = None
hud_manager = None
checkpoint_manager = None
flamethrower_manager = None
center_piece_manager = None

def init_resources():
    """
    Initialize game resources based on the current display mode using ResourceManager.
    """
    global font_sizes, fonts, large_font, small_font, TARGET_FONT, TITLE_FONT
    global MAX_PARTICLES, MAX_EXPLOSIONS, MAX_SWIRL_PARTICLES, mother_radius
    global particle_manager, glass_shatter_manager, multi_touch_manager, hud_manager, checkpoint_manager, flamethrower_manager, center_piece_manager
    
    # Get resource manager singleton
    resource_manager = ResourceManager()
    
    # Set display mode in the resource manager
    resource_manager.set_display_mode(DISPLAY_MODE)
    
    # Initialize mode-specific settings from Display_settings.py
    MAX_PARTICLES = PARTICLES_SETTINGS[DISPLAY_MODE]
    MAX_EXPLOSIONS = EXPLOSIONS_SETTINGS[DISPLAY_MODE]
    MAX_SWIRL_PARTICLES = SWIRL_SETTINGS[DISPLAY_MODE]
    mother_radius = MOTHER_RADIUS[DISPLAY_MODE]
    
    # Initialize font sizes from Display_settings
    font_sizes = FONT_SIZES[DISPLAY_MODE]["regular"]
    
    # Get core resources
    resources = resource_manager.initialize_game_resources()
    
    # Assign resources to global variables for backward compatibility
    fonts = resources['fonts']
    large_font = resources['large_font']
    small_font = resources['small_font']
    TARGET_FONT = resources['target_font']
    TITLE_FONT = resources['title_font']
    
    # Initialize particle manager with display mode specific settings
    particle_manager = ParticleManager(max_particles=MAX_PARTICLES)
    particle_manager.set_culling_distance(WIDTH)  # Set culling distance based on screen size
    
    # Initialize glass shatter manager
    glass_shatter_manager = GlassShatterManager(WIDTH, HEIGHT, particle_manager)
    
    # Initialize multi-touch manager
    multi_touch_manager = MultiTouchManager(WIDTH, HEIGHT)
    
    # Initialize HUD manager
    hud_manager = HUDManager(WIDTH, HEIGHT, small_font, glass_shatter_manager)
    
    # Initialize checkpoint manager
    checkpoint_manager = CheckpointManager(WIDTH, HEIGHT, fonts, small_font)
    
    # Initialize flamethrower manager
    flamethrower_manager = FlamethrowerManager()
    
    # Initialize center piece manager
    center_piece_manager = CenterPieceManager(WIDTH, HEIGHT, DISPLAY_MODE, particle_manager, MAX_SWIRL_PARTICLES, resource_manager)
    
    # Save display mode preference
    save_display_mode(DISPLAY_MODE)
    
    print(f"Resources initialized for display mode: {DISPLAY_MODE}")
    
    return resource_manager

# Initialize resources with current mode
resource_manager = init_resources()

# OPTIMIZATION: Global particle system limits to prevent lag
PARTICLE_CULLING_DISTANCE = WIDTH  # Distance at which to cull offscreen particles
# Particle pool for object reuse
particle_pool = []
for _ in range(100):  # Pre-create some particles to reuse
    particle_pool.append({
        "x": 0, "y": 0, "color": (0,0,0), "size": 0, 
        "dx": 0, "dy": 0, "duration": 0, "start_duration": 0,
        "active": False
    })

# Global variables for effects and touches.
particles = []

# Declare explosions and lasers in global scope so they are available to all functions
explosions = []
lasers = []

# Glass shatter manager - will be initialized after screen setup
glass_shatter_manager = None

# Add this near the other global variables at the top
player_color_transition = 0
player_current_color = FLAME_COLORS[0]
player_next_color = FLAME_COLORS[1]

# Add global variables for charge-up effect
charging_ability = False
charge_timer = 0
charge_particles = []
ability_target = None

# Add at the top of the file with other global variables
swirl_particles = []
particles_converging = False
convergence_target = None
convergence_timer = 0

###############################################################################
#                              SCREEN FUNCTIONS                               #
###############################################################################





###############################################################################
#                          GAME LOGIC & EFFECTS                               #
###############################################################################

def cleanup_global_resources():
    """Thoroughly clean up all global resources to prevent level bleeding."""
    global particles, explosions, lasers, charging_ability, charge_timer, charge_particles
    global ability_target, convergence_target, convergence_timer, swirl_particles
    global particles_converging, shake_duration, shake_magnitude
    
    # Log resource counts before cleanup
    print(f"Cleanup: explosions={len(explosions)}, particles={len(particles)}, lasers={len(lasers)}, charge_particles={len(charge_particles)}")
    
    # Clear all global effect lists
    particles.clear()
    explosions.clear()
    lasers.clear()
    charge_particles.clear()
    swirl_particles.clear()
    
    # Reset all global state variables
    charging_ability = False
    charge_timer = 0
    ability_target = None
    convergence_target = None
    convergence_timer = 0
    particles_converging = False
    shake_duration = 0
    shake_magnitude = 0
    
    # Clean up managers if they exist
    if multi_touch_manager:
        multi_touch_manager.reset()
    if glass_shatter_manager:
        glass_shatter_manager.reset()
    if flamethrower_manager:
        flamethrower_manager.clear()
    if center_piece_manager:
        center_piece_manager.reset()
    if particle_manager:
        particle_manager.particles.clear()
    
    print("Global resources cleaned up successfully")

def monitor_resource_usage():
    """Monitor and report current resource usage for debugging."""
    global particles, explosions, lasers, charge_particles
    
    stats = {
        "explosions": len(explosions),
        "particles": len(particles),
        "lasers": len(lasers),
        "charge_particles": len(charge_particles),
        "particle_manager_particles": len(particle_manager.particles) if particle_manager else 0
    }
    
    print(f"Resource Usage: {stats}")
    return stats

def game_loop(mode):
    global shake_duration, shake_magnitude, particles, explosions, lasers, charging_ability, charge_timer, charge_particles, ability_target, convergence_target, convergence_timer, mother_radius, color_idx, color_sequence, next_color_index, target_dots_left, glass_shatter_manager, multi_touch_manager, flamethrower_manager, center_piece_manager
    
    # CRITICAL: Clean up all global resources before starting new level
    cleanup_global_resources()
    
    # Reset level-specific variables
    mother_radius = 90 # Default radius for mother dot in Colors level
    color_sequence = []
    color_idx = 0
    next_color_index = 0
    # Don't initialize target_dots_left here since it's handled in the colors level code
    
    print(f"Starting game loop for mode: {mode}")
    
    # Initialize player trail particles
    particles = []
    
    # Try to read from a persistent settings file to check if shapes was completed
    try:
        with open(LEVEL_PROGRESS_PATH, "r") as f:
            progress = f.read().strip()
            if "shapes_completed" in progress:
                shapes_completed = True
    except:
        # If file doesn't exist or can't be read, assume shapes not completed
        shapes_completed = False
        


    # Create sequence based on selected mode
    sequence = SEQUENCES.get(mode, SEQUENCES["alphabet"])  # Default to alphabet if mode not found
    
    # Split into groups of GROUP_SIZE
    groups = [sequence[i:i+GROUP_SIZE] for i in range(0, len(sequence), GROUP_SIZE)]

    # Initialize game variables
    current_group_index = 0
    if not groups and mode != "colors": # Handle case where sequence is empty or too short
        print("Error: No groups generated for the selected mode.")
        return False # Or handle appropriately

    current_group = groups[current_group_index] if mode != "colors" else []
    # For consistency, use target_letter to represent the target even in shapes mode.
    letters_to_target = current_group.copy()
    if not letters_to_target and mode != "colors":
        print("Error: Current group is empty.")
        return False # Or handle appropriately
    target_letter = letters_to_target[0] if mode != "colors" else None
    TOTAL_LETTERS = len(sequence)
    total_destroyed = 0 # Tracks overall destroyed across all groups
    overall_destroyed = 0
    running = True

    clock = pygame.time.Clock()

    # Restore number of background stars
    stars = []
    for _ in range(100):  # Restore to 100
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        radius = random.randint(2, 4)
        stars.append([x, y, radius])

    # Initialize per-round (group) variables outside the main loop
    letters = []           # items (letters or numbers) on screen
    letters_spawned = 0    # count spawned items in current group
    letters_destroyed = 0  # count destroyed in current group
    last_checkpoint_triggered = 0  # New variable to track checkpoints
    checkpoint_waiting = False  # Flag to track if we're waiting to show a checkpoint screen
    checkpoint_delay_frames = 0  # Counter for checkpoint animation delay
    just_completed_level = False  # Flag to prevent checkpoint triggering right after level completion
    score = 0
    abilities = ["laser", "aoe", "charge_up"]
    current_ability = "laser"
    # explosions = [] # Already reset globally
    # lasers = [] # Already reset globally

    game_started = False
    last_click_time = 0
    player_x = WIDTH // 2
    player_y = HEIGHT // 2
    player_color_index = 0
    click_cooldown = 0
    mouse_down = False
    mouse_press_time = 0
    click_count = 0

    letters_to_spawn = current_group.copy()
    frame_count = 0

    # --- COLORS LEVEL SPECIAL LOGIC ---
    if mode == "colors":
        # Create and run the colors level
        colors_level = ColorsLevel(
            WIDTH, HEIGHT, screen, small_font, particle_manager,
            glass_shatter_manager, multi_touch_manager, hud_manager,
            mother_radius, create_explosion, checkpoint_manager.show_checkpoint_screen, game_over_screen,
            explosions, draw_explosion
        )
        return colors_level.run()
    
    # --- SHAPES LEVEL SPECIAL LOGIC ---
    if mode == "shapes":
        # Create and run the shapes level
        shapes_level = ShapesLevel(
            WIDTH, HEIGHT, screen, fonts, small_font, TARGET_FONT,
            particle_manager, glass_shatter_manager, multi_touch_manager,
            hud_manager, checkpoint_manager, center_piece_manager, create_explosion, create_flame_effect,
            apply_explosion_effect, create_particle,
            explosions, lasers, draw_explosion, game_over_screen
        )
        return shapes_level.run()
    
    # --- ALPHABET LEVEL SPECIAL LOGIC ---
    if mode == "alphabet":
        # Create and run the alphabet level
        alphabet_level = AlphabetLevel(
            WIDTH, HEIGHT, screen, fonts, small_font, TARGET_FONT,
            particle_manager, glass_shatter_manager, multi_touch_manager,
            hud_manager, checkpoint_manager, center_piece_manager, 
            flamethrower_manager, resource_manager, create_explosion, create_flame_effect,
            apply_explosion_effect, create_particle,
            explosions, lasers, draw_explosion, game_over_screen
        )
        return alphabet_level.run()

    # --- NUMBERS LEVEL SPECIAL LOGIC ---
    if mode == "numbers":
        # Create and run the numbers level
        numbers_level = NumbersLevel(
            WIDTH, HEIGHT, screen, fonts, small_font, TARGET_FONT,
            particle_manager, glass_shatter_manager, multi_touch_manager,
            hud_manager, checkpoint_manager, center_piece_manager, 
            flamethrower_manager, resource_manager, create_explosion, create_flame_effect,
            apply_explosion_effect, create_particle,
            explosions, lasers, draw_explosion, game_over_screen
        )
        return numbers_level.run()

    # --- C/L CASE LEVEL SPECIAL LOGIC ---
    if mode == "clcase":
        # Create and run the C/L case level
        clcase_level = CLCaseLevel(
            WIDTH, HEIGHT, screen, fonts, small_font, TARGET_FONT,
            particle_manager, glass_shatter_manager, multi_touch_manager,
            hud_manager, checkpoint_manager, center_piece_manager, 
            flamethrower_manager, resource_manager, create_explosion, create_flame_effect,
            apply_explosion_effect, create_particle,
            explosions, lasers, draw_explosion, game_over_screen
        )
        return clcase_level.run()

    # --- ERROR HANDLER ---
    # All game modes should be handled by dedicated level classes above.
    # If we reach this point, there's an unrecognized mode.
    print(f"Error: Unrecognized game mode '{mode}'. All modes should be handled by dedicated level classes.")
    return False  # Return to menu


def create_aoe(x, y, letters, target_letter):
    """Handles Area of Effect ability (placeholder/unused currently)."""
    # This function seems unused based on the event loop logic.
    # If intended, it would need integration into the event handling.
    global letters_destroyed # Needs access to modify this counter
    create_explosion(x, y, max_radius=350, duration=40) # Bigger AOE explosion
    destroyed_count_in_aoe = 0
    for letter_obj in letters[:]:
        distance = math.hypot(letter_obj["x"] - x, letter_obj["y"] - y)
        if distance < 200: # AOE radius
             # Optional: Check if it's the target letter or destroy any letter?
             # if letter_obj["value"] == target_letter:
                create_explosion(letter_obj["x"], letter_obj["y"], duration=20) # Smaller explosions for hit targets
                # Add particles, etc.
                letters.remove(letter_obj)
                destroyed_count_in_aoe += 1

    letters_destroyed += destroyed_count_in_aoe # Update the counter for the current group





def well_done_screen(score):
    """Screen shown after completing all targets in a mode."""
    flash = True
    flash_count = 0
    running = True
    clock = pygame.time.Clock()
    while running:
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()
            # Force click to continue
            if event.type == pygame.MOUSEBUTTONDOWN:
                running = False
                return True  # Return True to indicate we should go back to level menu

        # Display "Well Done!" message
        well_done_font = fonts[2] # Use one of the preloaded larger fonts
        well_done_text = well_done_font.render("Well Done!", True, WHITE)
        well_done_rect = well_done_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(well_done_text, well_done_rect)

        # Display final score
        score_text = small_font.render(f"Final Score: {score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
        screen.blit(score_text, score_rect)


        # Flashing "Click for Next Mission" text
        next_player_color = random.choice(FLAME_COLORS) if flash else BLACK
        next_player_text = small_font.render("Click for Next Mission", True, next_player_color)
        next_player_rect = next_player_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
        screen.blit(next_player_text, next_player_rect)

        pygame.display.flip()
        flash_count += 1
        if flash_count % 30 == 0: # Flash every half second
            flash = not flash
        clock.tick(60)
    return False # Should not be reached if click is required

def apply_explosion_effect(x, y, explosion_radius, letters):
    """Pushes nearby letters away from an explosion center."""
    for letter in letters:
        dx = letter["x"] - x
        dy = letter["y"] - y
        dist_sq = dx*dx + dy*dy
        if dist_sq < explosion_radius * explosion_radius and dist_sq > 0:
            dist = math.sqrt(dist_sq)
            # Force is stronger closer to the center
            force = (1 - (dist / explosion_radius)) * 15 # Adjust force multiplier as needed
            # Apply force directly to velocity
            letter["dx"] += (dx / dist) * force
            letter["dy"] += (dy / dist) * force
            # Ensure the item can bounce after being pushed
            letter["can_bounce"] = True




def create_player_trail(x, y):
    """Creates trail particles behind the (currently static) player position."""
    # This might be less useful if the player doesn't move, but kept for potential future use.
    for _ in range(1): # Reduce particle count for static player
        create_particle(
            x + random.uniform(-10, 10),  # Spawn around center
            y + random.uniform(-10, 10),
            random.choice(FLAME_COLORS),
            random.randint(2, 4),
            random.uniform(-0.2, 0.2),  # Slow drift
            random.uniform(-0.2, 0.2),
            20  # Shorter duration
        )

# Restore charge particle count for charge-up effect
def start_charge_up_effect(player_x, player_y, target_x, target_y):
    global charging_ability, charge_timer, charge_particles, ability_target
    charging_ability = True
    charge_timer = 45
    ability_target = (target_x, target_y)
    charge_particles = []
    
    # PERFORMANCE: Reduce particle count for QBoard
    particle_count = 75 if DISPLAY_MODE == "QBOARD" else 150
    
    for _ in range(particle_count):
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            x, y = random.uniform(0, WIDTH), random.uniform(-100, -20)
        elif side == 'bottom':
            x, y = random.uniform(0, WIDTH), random.uniform(HEIGHT + 20, HEIGHT + 100)
        elif side == 'left':
            x, y = random.uniform(-100, -20), random.uniform(0, HEIGHT)
        else: # right
            x, y = random.uniform(WIDTH + 20, WIDTH + 100), random.uniform(0, HEIGHT)

        charge_particles.append({
            "type": "materializing",
            "x": x, "y": y,
            "target_x": player_x, # Target is the player center (orb)
            "target_y": player_y - 80, # Target orb position
            "color": random.choice(FLAME_COLORS),
            "size": random.uniform(1, 3), "max_size": random.uniform(4, 8), # Slightly larger max
            "speed": random.uniform(1.0, 3.0), # Start with some speed
            "opacity": 0, "max_opacity": random.randint(180, 255),
            "materialize_time": random.randint(10, 25), # Faster materialization
            "delay": random.randint(0, 15), # Shorter stagger
            "acceleration": random.uniform(0.1, 0.4), # Higher acceleration
            "wobble_angle": random.uniform(0, 2 * math.pi),
            "wobble_speed": random.uniform(0.1, 0.3),
            "wobble_amount": random.uniform(1.0, 3.0), # Slightly more wobble
            "trail": random.random() < 0.5 # More trails
        })

# Legacy functions - now handled by CenterPieceManager
def get_particle_from_pool():
    """Legacy function that now uses the particle manager."""
    return particle_manager.get_particle()

def release_particle(particle):
    """Legacy function that now uses the particle manager."""
    particle_manager.release_particle(particle)

def create_particle(x, y, color, size, dx, dy, duration):
    """Legacy function that now uses the particle manager."""
    return particle_manager.create_particle(x, y, color, size, dx, dy, duration)

def create_explosion(x, y, color=None, max_radius=270, duration=30):
    """Adds an explosion effect to the list, with a limit for performance."""
    global shake_duration, explosions
    
    # Limit number of explosions for performance
    if len(explosions) >= MAX_EXPLOSIONS:
        # If we've reached the limit, replace the oldest explosion
        oldest_explosion = min(explosions, key=lambda exp: exp["duration"])
        explosions.remove(oldest_explosion)
    
    if color is None:
        color = random.choice(FLAME_COLORS)
        
    explosions.append({
        "x": x,
        "y": y,
        "radius": 10, # Start small
        "color": color,
        "max_radius": max_radius,
        "duration": duration,
        "start_duration": duration # Store initial duration for fading
    })
    
    shake_duration = max(shake_duration, 10) # Trigger screen shake, don't override longer shakes



def draw_explosion(explosion, offset_x=0, offset_y=0):
    """Draws a single explosion frame, expanding and fading."""
    # Expand radius towards max_radius
    explosion["radius"] += (explosion["max_radius"] - explosion["radius"]) * 0.1 # Smoother expansion
    # Calculate alpha based on remaining duration
    alpha = max(0, int(255 * (explosion["duration"] / explosion["start_duration"])))
    color = (*explosion["color"][:3], alpha) # Add alpha to color
    radius = int(explosion["radius"])
    # Apply shake offset
    draw_x = int(explosion["x"] + offset_x)
    draw_y = int(explosion["y"] + offset_y)

    # Draw using SRCALPHA surface for transparency
    if radius > 0:
        explosion_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(explosion_surf, color, (radius, radius), radius)
        screen.blit(explosion_surf, (draw_x - radius, draw_y - radius))

def create_flame_effect(start_x, start_y, end_x, end_y):
    """Creates a laser/flame visual effect between two points."""
    global flamethrower_manager
    # Use flamethrower manager for all levels except colors
    if flamethrower_manager:
        flamethrower_manager.create_flamethrower(start_x, start_y, end_x, end_y, duration=10)



def game_over_screen():
    """Screen shown when player breaks the screen completely."""
    # This function is now a placeholder and should be implemented
    # to provide a user-friendly message and allow the player to restart the game
    print("Game over screen is not implemented yet.")
    return False  # Placeholder return, actual implementation needed

if __name__ == "__main__":
    DISPLAY_MODE = welcome_screen(WIDTH, HEIGHT, screen, small_font, init_resources)
    while True:
        mode = level_menu(WIDTH, HEIGHT, screen, small_font)
        if mode is None:
            break
        
        # CRITICAL: Force global cleanup before starting any level
        print(f"\n=== Starting Level: {mode} ===")
        cleanup_global_resources()
        
        try:
            # Run the game loop and check its return value
            restart_level = game_loop(mode)
            
            # If game_loop returns True, restart the level for shapes level or colors level
            while restart_level and (mode == "shapes" or mode == "colors"):
                print(f"\n=== Restarting Level: {mode} ===")
                cleanup_global_resources()  # Clean up before restart
                restart_level = game_loop(mode)
        
        except Exception as e:
            print(f"Error during level execution: {e}")
            cleanup_global_resources()  # Clean up on error
        
        finally:
            # CRITICAL: Always clean up after level ends
            print(f"\n=== Cleaning up after Level: {mode} ===")
            cleanup_global_resources()
            
    # Final cleanup on exit
    print("\n=== Final Cleanup ===")
    cleanup_global_resources()