import pygame
import random
import math
from settings import (
    COLORS_COLLISION_DELAY, LEVEL_PROGRESS_PATH, WHITE, BLACK, FLAME_COLORS, LASER_EFFECTS,
    LETTER_SPAWN_INTERVAL, SEQUENCES, GAME_MODES, GROUP_SIZE,
    SHAKE_DURATION_MISCLICK, SHAKE_MAGNITUDE_MISCLICK
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
from levels import ColorsLevel, ShapesLevel, AlphabetLevel, NumbersLevel

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
shake_duration = 0
shake_magnitude = 10

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

def game_loop(mode):
    global shake_duration, shake_magnitude, particles, explosions, lasers, charging_ability, charge_timer, charge_particles, ability_target, convergence_target, convergence_timer, mother_radius, color_idx, color_sequence, next_color_index, target_dots_left, glass_shatter_manager, multi_touch_manager, flamethrower_manager, center_piece_manager
    
    # Reset global effects that could persist between levels
    shake_duration = 0
    shake_magnitude = 0
    particles = []
    explosions = []
    lasers = []
    multi_touch_manager.reset()  # Clear any lingering active touches
    glass_shatter_manager.reset()  # Reset glass shatter state
    flamethrower_manager.clear()  # Clear any lingering flamethrower effects
    center_piece_manager.reset()  # Reset center piece state
    mother_radius = 90 # Default radius for mother dot in Colors level
    color_sequence = []
    color_idx = 0
    next_color_index = 0
    # Don't initialize target_dots_left here since it's handled in the colors level code
    convergence_timer = 0
    charge_timer = 0
    convergence_target = None
    charging_ability = False
    charge_particles = []
    ability_target = None
    
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

    # --- Main Game Loop ---
    while running:

        # -------------------- Event Handling --------------------
        for event in pygame.event.get():
            # Handle glass shatter events first
            glass_shatter_manager.handle_event(event)
            
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Exit the game completely instead of just returning to level menu
                    pygame.quit()
                    exit()
                if event.key == pygame.K_SPACE:
                    current_ability = abilities[(abilities.index(current_ability) + 1) % len(abilities)]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not mouse_down:
                    mouse_press_time = pygame.time.get_ticks()
                    mouse_down = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                release_time = pygame.time.get_ticks()
                mouse_down = False
                duration = release_time - mouse_press_time
                if duration <= 1000: # Check if it's a click (not a hold)
                    click_count += 1
                    if not game_started:
                        game_started = True
                    else:
                        click_x, click_y = pygame.mouse.get_pos()
                        current_time = release_time
                        # Double click check (less relevant now, but kept logic)
                        # if current_time - last_click_time < 250:
                        #     # Potentially re-target logic (removed for simplicity)
                        #     last_click_time = 0
                        # else:
                        last_click_time = current_time
                        
                        # Flag to track if click hit a target
                        hit_target = False
                        
                        # --- Process Click on Target ---
                        for letter_obj in letters[:]:
                            if letter_obj["rect"].collidepoint(click_x, click_y):
                                hit_target = True  # Marked as hit
                                if letter_obj["value"] == target_letter:
                                    score += 10
                                    # Common destruction effects
                                    create_explosion(letter_obj["x"], letter_obj["y"])
                                    create_flame_effect(player_x, player_y - 80, letter_obj["x"], letter_obj["y"])
                                    center_piece_manager.trigger_convergence(letter_obj["x"], letter_obj["y"])
                                    apply_explosion_effect(letter_obj["x"], letter_obj["y"], 150, letters) # Apply push effect

                                    # Add visual feedback particles
                                    for i in range(20):
                                        create_particle(
                                            letter_obj["x"], letter_obj["y"],
                                            random.choice(FLAME_COLORS),
                                            random.randint(40, 80),
                                            random.uniform(-2, 2), random.uniform(-2, 2),
                                            20
                                        )

                                    # Remove letter and update counts
                                    letters.remove(letter_obj)
                                    letters_destroyed += 1

                                    # Update target
                                    if target_letter in letters_to_target:
                                        letters_to_target.remove(target_letter)
                                    if letters_to_target:
                                        target_letter = letters_to_target[0]
                                    else:
                                        # Handle case where group is finished but not yet detected by main loop logic
                                        pass # Will be handled below

                                    # Ability specific actions (if needed, e.g., charge up)
                                    # if current_ability == "charge_up":
                                    #     start_charge_up_effect(player_x, player_y, letter_obj["x"], letter_obj["y"])

                                    break # Exit loop after processing one hit
                                else:
                                    # Optional: Add feedback for clicking wrong target (e.g., small shake, sound)
                                    shake_duration = 5
                                    shake_magnitude = 3
                
                        # If no target was hit, add a crack to the screen
                        if not hit_target and game_started:
                            glass_shatter_manager.handle_misclick(click_x, click_y)

            elif event.type == pygame.FINGERDOWN:
                touch_result = multi_touch_manager.handle_touch_down(event)
                if touch_result is None:
                    continue  # Touch was ignored due to cooldown
                touch_id, touch_x, touch_y = touch_result
                if not game_started:
                    game_started = True
                else:
                    # Flag to track if touch hit a target
                    hit_target = False
                    
                    # --- Process Touch on Target ---
                    for letter_obj in letters[:]:
                        if letter_obj["rect"].collidepoint(touch_x, touch_y):
                            hit_target = True  # Marked as hit
                            if letter_obj["value"] == target_letter:
                                score += 10
                                # Common destruction effects
                                create_explosion(letter_obj["x"], letter_obj["y"])
                                create_flame_effect(player_x, player_y - 80, letter_obj["x"], letter_obj["y"])
                                center_piece_manager.trigger_convergence(letter_obj["x"], letter_obj["y"])
                                apply_explosion_effect(letter_obj["x"], letter_obj["y"], 150, letters) # Apply push effect

                                # Add visual feedback particles
                                for i in range(20):
                                    create_particle(
                                        letter_obj["x"], letter_obj["y"],
                                        random.choice(FLAME_COLORS),
                                        random.randint(40, 80),
                                        random.uniform(-2, 2), random.uniform(-2, 2),
                                        20
                                    )

                                # Remove letter and update counts
                                letters.remove(letter_obj)
                                letters_destroyed += 1

                                # Update target
                                if target_letter in letters_to_target:
                                    letters_to_target.remove(target_letter)
                                if letters_to_target:
                                    target_letter = letters_to_target[0]
                                else:
                                    # Handle case where group is finished but not yet detected by main loop logic
                                    pass # Will be handled below

                                # Ability specific actions (if needed)
                                # if current_ability == "charge_up":
                                #     start_charge_up_effect(player_x, player_y, letter_obj["x"], letter_obj["y"])

                                break # Exit loop after processing one hit
                            else:
                                # Optional: Feedback for wrong target touch
                                shake_duration = 5
                                shake_magnitude = 3
            
                    # If no target was hit, add a crack to the screen
                    if not hit_target and game_started:
                        glass_shatter_manager.handle_misclick(touch_x, touch_y)

            elif event.type == pygame.FINGERUP:
                touch_result = multi_touch_manager.handle_touch_up(event)
                if touch_result is not None:
                    touch_id, last_x, last_y = touch_result

        # Mouse hold check (less relevant now)
        # if mouse_down:
        #     current_time = pygame.time.get_ticks()
        #     if current_time - mouse_press_time > 1000:
        #         mouse_down = False

        # ------------------- Spawning Items -------------------
        if game_started:
            if letters_to_spawn:
                if frame_count % LETTER_SPAWN_INTERVAL == 0:
                    # Use a generic key "value" for both letters/numbers and shapes.
                    item_value = letters_to_spawn.pop(0)
                    letter_obj = {
                        "value": item_value,
                        "x": random.randint(50, WIDTH - 50),
                        "y": -50,
                        "rect": pygame.Rect(0, 0, 0, 0), # Will be updated when drawn
                        "size": 240,  # fixed size (doubled from 120 to 240 for 100% increase)
                        "dx": random.choice([-1, -0.5, 0.5, 1]) * 1.5, # Slightly faster horizontal drift
                        "dy": random.choice([1, 1.5]) * 1.5, # Slightly faster fall speed
                        "can_bounce": False, # Start without bouncing
                        "mass": random.uniform(40, 60) # Give items mass for collisions
                    }
                    letters.append(letter_obj)
                    letters_spawned += 1

        # ------------------- Drawing and Updating -------------------
        # Apply screen shake if active
        offset_x, offset_y = glass_shatter_manager.get_screen_shake_offset()

        # Update glass shatter manager
        glass_shatter_manager.update()
        
        # Fill background based on shatter state
        screen.fill(glass_shatter_manager.get_background_color())

        # Draw cracks
        glass_shatter_manager.draw_cracks(screen)

        # --- Draw Background Elements (Stars) ---
        for star in stars:
            x, y, radius = star
            y += 1 # Slower star movement speed
            pygame.draw.circle(screen, (200, 200, 200), (x + offset_x, y + offset_y), radius)
            if y > HEIGHT + radius: # Reset when fully off screen
                y = random.randint(-50, -10)
                x = random.randint(0, WIDTH)
            star[1] = y
            star[0] = x

        # --- Draw Center Piece (Swirl Particles + Target Display) ---
        center_piece_manager.update_and_draw(screen, target_letter, mode, offset_x, offset_y)

        # --- Update and Draw Falling Items (Letters/Numbers/Shapes) ---
        for letter_obj in letters[:]:
            letter_obj["x"] += letter_obj["dx"]
            letter_obj["y"] += letter_obj["dy"]

            # --- Bouncing Logic ---
            # Allow bouncing only after falling a certain distance
            if not letter_obj["can_bounce"] and letter_obj["y"] > HEIGHT // 5:
                 letter_obj["can_bounce"] = True

            # If bouncing is enabled, check screen edges
            if letter_obj["can_bounce"]:
                bounce_dampening = 0.8 # Reduce speed slightly on bounce

                # Left/Right Walls
                if letter_obj["x"] <= 0 + letter_obj.get("size", 50)/2: # Approx radius check
                    letter_obj["x"] = 0 + letter_obj.get("size", 50)/2
                    letter_obj["dx"] = abs(letter_obj["dx"]) * bounce_dampening
                elif letter_obj["x"] >= WIDTH - letter_obj.get("size", 50)/2:
                    letter_obj["x"] = WIDTH - letter_obj.get("size", 50)/2
                    letter_obj["dx"] = -abs(letter_obj["dx"]) * bounce_dampening

                # Top/Bottom Walls (less likely to hit top unless pushed)
                if letter_obj["y"] <= 0 + letter_obj.get("size", 50)/2:
                    letter_obj["y"] = 0 + letter_obj.get("size", 50)/2
                    letter_obj["dy"] = abs(letter_obj["dy"]) * bounce_dampening
                elif letter_obj["y"] >= HEIGHT - letter_obj.get("size", 50)/2:
                    letter_obj["y"] = HEIGHT - letter_obj.get("size", 50)/2
                    letter_obj["dy"] = -abs(letter_obj["dy"]) * bounce_dampening
                    # Also slightly push horizontally away from edge on bottom bounce
                    letter_obj["dx"] *= bounce_dampening
                    if letter_obj["x"] < WIDTH / 2:
                        letter_obj["dx"] += random.uniform(0.1, 0.3)
                    else:
                        letter_obj["dx"] -= random.uniform(0.1, 0.3)

            # --- Draw the Item (Shape or Text) ---
            draw_pos_x = int(letter_obj["x"] + offset_x)
            draw_pos_y = int(letter_obj["y"] + offset_y)

            # Draw text for Alphabet, Numbers, C/L Case using cached fonts for performance
            display_value = letter_obj["value"]

            if mode == "clcase" and letter_obj["value"] == "a":
                display_value = "α"

            # Use gray for non-target letters, black for the target letter
            text_color = BLACK if letter_obj["value"] == target_letter else (150, 150, 150)
            
            # PERFORMANCE OPTIMIZATION: Use cached font surface if available
            try:
                cached_surface = resource_manager.get_falling_object_surface(mode, letter_obj["value"], text_color)
                text_rect = cached_surface.get_rect(center=(draw_pos_x, draw_pos_y))
                letter_obj["rect"] = text_rect
                screen.blit(cached_surface, text_rect)
            except:
                # Fallback: Original rendering method
                text_surface = TARGET_FONT.render(display_value, True, text_color)
                text_rect = text_surface.get_rect(center=(draw_pos_x, draw_pos_y))
                letter_obj["rect"] = text_rect
                screen.blit(text_surface, text_rect)


        # --- Simple Collision Detection Between Items ---
        # PERFORMANCE: Reduce collision check frequency for QBoard
        collision_frequency = PERFORMANCE_SETTINGS[DISPLAY_MODE]["collision_check_frequency"]
        if frame_count % collision_frequency == 0:
            for i, letter_obj1 in enumerate(letters):
                for j in range(i + 1, len(letters)):
                    letter_obj2 = letters[j]
                    dx = letter_obj2["x"] - letter_obj1["x"]
                    dy = letter_obj2["y"] - letter_obj1["y"]
                    distance_sq = dx*dx + dy*dy # Use squared distance for efficiency

                    # Approximate collision radius based on font/shape size
                    # Use a slightly larger radius for text to account for varying widths
                    radius1 = letter_obj1.get("size", TARGET_FONT.get_height()) / 1.8 # Approx radius
                    radius2 = letter_obj2.get("size", TARGET_FONT.get_height()) / 1.8
                    min_distance = radius1 + radius2
                    min_distance_sq = min_distance * min_distance

                    if distance_sq < min_distance_sq and distance_sq > 0: # Check for overlap
                        distance = math.sqrt(distance_sq)
                        # Normalize collision vector
                        nx = dx / distance
                        ny = dy / distance

                        # Resolve interpenetration (push apart)
                        overlap = min_distance - distance
                        total_mass = letter_obj1["mass"] + letter_obj2["mass"]
                        # Push apart proportional to the *other* object's mass
                        push_factor = overlap / total_mass
                        letter_obj1["x"] -= nx * push_factor * letter_obj2["mass"]
                        letter_obj1["y"] -= ny * push_factor * letter_obj2["mass"]
                        letter_obj2["x"] += nx * push_factor * letter_obj1["mass"]
                        letter_obj2["y"] += ny * push_factor * letter_obj1["mass"]

                        # Calculate collision response (bounce) - Elastic collision formula component
                        # Relative velocity
                        dvx = letter_obj1["dx"] - letter_obj2["dx"]
                        dvy = letter_obj1["dy"] - letter_obj2["dy"]
                        # Dot product of relative velocity and collision normal
                        dot_product = dvx * nx + dvy * ny
                        # Impulse magnitude
                        impulse = (2 * dot_product) / total_mass
                        bounce_factor = 0.85 # Slightly less than perfectly elastic

                        # Apply impulse scaled by mass and bounce factor
                        letter_obj1["dx"] -= impulse * letter_obj2["mass"] * nx * bounce_factor
                        letter_obj1["dy"] -= impulse * letter_obj2["mass"] * ny * bounce_factor
                        letter_obj2["dx"] += impulse * letter_obj1["mass"] * nx * bounce_factor
                        letter_obj2["dy"] += impulse * letter_obj1["mass"] * ny * bounce_factor


        # --- Process Flamethrower Effects ---
        flamethrower_manager.update()
        flamethrower_manager.draw(screen, offset_x, offset_y)
        
        # --- Process Legacy Lasers (if any remain) ---
        for laser in lasers[:]:
            if laser["duration"] > 0:
                # Legacy laser handling (non-flamethrower effects)
                if laser["type"] != "flamethrower":
                    pygame.draw.line(screen, random.choice(laser.get("colors", FLAME_COLORS)),
                                     (laser["start_pos"][0] + offset_x, laser["start_pos"][1] + offset_y),
                                     (laser["end_pos"][0] + offset_x, laser["end_pos"][1] + offset_y),
                                      random.choice(laser.get("widths", [5, 10, 15])))
                laser["duration"] -= 1
            else:
                lasers.remove(laser)

        # --- Process Explosions ---
        for explosion in explosions[:]:
            if explosion["duration"] > 0:
                draw_explosion(explosion, offset_x, offset_y) # Pass shake offset
                explosion["duration"] -= 1
            else:
                explosions.remove(explosion)

        # --- Process Charge-Up Ability Effect ---
        if charging_ability:
            charge_timer -= 1

            # Draw a dark overlay for a dramatic effect
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))  # Semi-transparent black
            screen.blit(overlay, (0, 0)) # No shake offset for overlay

            # Process materializing/accelerating particles
            for particle in charge_particles[:]:
                # Handle initial delay
                if particle["delay"] > 0:
                    particle["delay"] -= 1
                    continue

                # Materialization phase
                if particle["type"] == "materializing":
                    if particle["materialize_time"] > 0:
                        particle["materialize_time"] -= 1
                        ratio = 1 - (particle["materialize_time"] / 15) # 0 to 1
                        particle["opacity"] = int(particle["max_opacity"] * ratio)
                        particle["size"] = particle["max_size"] * ratio

                        # Wobble effect
                        wobble_x = math.cos(particle["wobble_angle"]) * particle["wobble_amount"]
                        wobble_y = math.sin(particle["wobble_angle"]) * particle["wobble_amount"]
                        particle["wobble_angle"] += particle["wobble_speed"]

                        # Draw materializing particle (apply shake offset here)
                        particle_surface = pygame.Surface((particle["size"]*2, particle["size"]*2), pygame.SRCALPHA)
                        pygame.draw.circle(particle_surface,
                                          (*particle["color"], particle["opacity"]),
                                          (particle["size"], particle["size"]),
                                          particle["size"])
                        screen.blit(particle_surface,
                                   (int(particle["x"] + wobble_x - particle["size"] + offset_x),
                                    int(particle["y"] + wobble_y - particle["size"] + offset_y)))
                        continue
                    else:
                        particle["type"] = "accelerating" # Transition to next phase

                # Acceleration phase
                if particle["type"] == "accelerating":
                    dx = particle["target_x"] - particle["x"]
                    dy = particle["target_y"] - particle["y"]
                    distance = math.hypot(dx, dy)

                    if distance > 5: # Move until close
                        # Accelerate based on distance
                        particle["speed"] += particle["acceleration"] * (1 + (400 - min(400, distance)) / 1000)
                        norm_dx = dx / distance
                        norm_dy = dy / distance
                        particle["x"] += norm_dx * particle["speed"]
                        particle["y"] += norm_dy * particle["speed"]

                        # Leave trail particles (add to main particle list)
                        if particle["trail"] and random.random() < 0.4:
                            create_particle(
                                particle["x"], particle["y"],
                                particle["color"], particle["size"] / 2,
                                -norm_dx * 0.5, -norm_dy * 0.5,
                                50  # Shorter trail duration
                            )

                        # Draw particle with glow (apply shake offset)
                        draw_x = int(particle["x"] + offset_x)
                        draw_y = int(particle["y"] + offset_y)
                        glow_size = particle["size"] * 1.5
                        glow_surface = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surface, (*particle["color"], 70), (glow_size, glow_size), glow_size)
                        screen.blit(glow_surface, (int(draw_x - glow_size), int(draw_y - glow_size)))

                        particle_surface = pygame.Surface((particle["size"]*2, particle["size"]*2), pygame.SRCALPHA)
                        pygame.draw.circle(particle_surface, (*particle["color"], particle["opacity"]), (particle["size"], particle["size"]), particle["size"])
                        screen.blit(particle_surface, (int(draw_x - particle["size"]), int(draw_y - particle["size"])))
                    else:
                        # Particle reached target - remove and create small flash
                        for _ in range(3):
                            particles.append({
                                "x": particle["target_x"], "y": particle["target_y"],
                                "color": particle["color"], "size": random.uniform(12, 24),
                                "dx": random.uniform(-2, 2), "dy": random.uniform(-2, 2),
                                "duration": 20
                            })
                        charge_particles.remove(particle)


            # Draw energy orb forming at player position (apply shake offset)
            orb_x = player_x + offset_x
            orb_y = player_y - 80 + offset_y # Offset slightly above center
            energy_radius = 20 + (30 - charge_timer) * 1.5  # Grows as timer decreases
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 15  # Pulsing effect

            for i in range(3): # Draw multiple layers for orb
                factor = 1 - (i * 0.25)
                color = FLAME_COLORS[int((pygame.time.get_ticks() * 0.01 + i*2) % len(FLAME_COLORS))]
                radius = (energy_radius + pulse) * factor
                alpha = int(200 * factor)

                glow_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA) # Correct surface size
                pygame.draw.circle(glow_surface, (*color, alpha), (radius, radius), radius)
                screen.blit(glow_surface, (int(orb_x - radius), int(orb_y - radius)))

            # Bright inner core
            pygame.draw.circle(screen, (255, 255, 255), (int(orb_x), int(orb_y)), int(energy_radius/3))

            # If charge complete, fire the ability
            if charge_timer <= 0:
                charging_ability = False
                if ability_target: # Ensure target exists
                    # Trigger effects at the target location
                    create_explosion(ability_target[0], ability_target[1])
                    create_flame_effect(player_x, player_y - 80, ability_target[0], ability_target[1]) # Originates from player center

                    # Create massive explosion particles at target
                    for _ in range(40):
                        particles.append({
                            "x": ability_target[0], "y": ability_target[1],
                            "color": random.choice(FLAME_COLORS),
                            "size": random.randint(40, 80),
                            "dx": random.uniform(-4, 4), "dy": random.uniform(-4, 4),
                            "duration": 100 # Longer duration for big explosion
                        })
                    ability_target = None # Reset target after firing


        # --- Draw General Particles ---
        # Use the particle manager instead of manually updating particles
        particle_manager.update()
        particle_manager.draw(screen, offset_x, offset_y)
        
        # --- Display HUD Info ---
        if mode != "colors":
            hud_manager.display_info(screen, score, current_ability, target_letter, overall_destroyed + letters_destroyed, TOTAL_LETTERS, mode)
            
        # --- Update Display ---
        pygame.display.flip()
        clock.tick(50)  # PERFORMANCE: Lower FPS for all main game loops
        frame_count += 1


        # --- Checkpoint Logic ---
        overall_destroyed = total_destroyed + letters_destroyed

        # If waiting for animations before showing checkpoint screen
        if checkpoint_waiting:
            # Only show checkpoint after delay AND when animations are mostly complete
            if checkpoint_delay_frames <= 0 and len(explosions) <= 1 and len(lasers) <= 1 and flamethrower_manager.get_count() <= 1 and not particles_converging:
                checkpoint_waiting = False
                game_started = False  # Pause the game
                if not checkpoint_manager.show_checkpoint_screen(screen, mode): # If checkpoint returns False (chose Menu)
                    running = False # Exit game loop to return to menu
                    break
                else:
                    # If continue was pressed
                    if mode == "colors" and shapes_completed:
                        running = False  # Signal to restart colors level
                        break
                    elif mode == "shapes":
                        return True  # Signal to restart shapes level
                    else:
                        game_started = True  # Resume the current level
            else:
                checkpoint_delay_frames -= 1

        # Check if we hit a new checkpoint threshold (and not just completed a level)
        elif overall_destroyed > 0 and overall_destroyed % 10 == 0 and overall_destroyed // 10 > last_checkpoint_triggered and not just_completed_level:
            last_checkpoint_triggered = overall_destroyed // 10
            checkpoint_waiting = True
            checkpoint_delay_frames = 60  # Wait ~1 second (60 frames) for animations


        # --- Level Progression Logic ---
        # Check if the current group is finished (no letters left on screen AND no more to spawn)
        if not letters and not letters_to_spawn and letters_to_target == []: # Ensure targets are also cleared
            total_destroyed += letters_destroyed # Add destroyed from this group to total
            current_group_index += 1
            just_completed_level = True # Set flag to prevent immediate checkpoint

            if current_group_index < len(groups):
                # --- Start Next Group ---
                current_group = groups[current_group_index]
                letters_to_spawn = current_group.copy()
                letters_to_target = current_group.copy()
                if letters_to_target:
                     target_letter = letters_to_target[0]
                else:
                     print(f"Warning: Group {current_group_index} is empty.")
                     # Handle this case - maybe skip group or end game?
                     running = False # End game for now if a group is empty
                     break

                # Reset group-specific counters
                letters_destroyed = 0
                letters_spawned = 0
                # Reset effects? Maybe not necessary unless they persist wrongly
                # explosions = []
                # lasers = []
                # particles = [] # Might clear too many effects?
                just_completed_level = False # Reset flag for the new level
                game_started = True # Ensure game continues if paused by checkpoint logic bug
                last_checkpoint_triggered = overall_destroyed // 10 # Update checkpoint trigger base

            else:
                # --- All Groups Completed (Level Finished) ---
                # Show checkpoint screen for all completed levels
                pygame.time.delay(500)  # Brief delay like in colors level
                if not checkpoint_manager.show_checkpoint_screen(screen, mode):  # If checkpoint returns False (chose Menu)
                    running = False  # Exit game loop to return to menu
                else:
                    # If continue was pressed, return to menu since level is complete
                    running = False
                
                # Exit the loop immediately to prevent counter issues
                break



    # --- End of Main Game Loop ---
    # Return True if we exited to go back to the menu (e.g., from checkpoint or well_done)
    # Return False if we exited via ESC or Quit event
    return True if running == False else False # A bit confusing, revise this return logic if needed


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
        
        # Run the game loop and check its return value
        restart_level = game_loop(mode)
        
        # If game_loop returns True, restart the level for shapes level or colors level
        while restart_level and (mode == "shapes" or mode == "colors"):
            restart_level = game_loop(mode)