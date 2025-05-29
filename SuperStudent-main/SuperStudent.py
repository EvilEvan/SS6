import pygame
import random
import math

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

# Define colors and effects
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FLAME_COLORS = [
    (255, 69, 0),    # OrangeRed
    (255, 140, 0),   # DarkOrange
    (255, 165, 0),   # Orange
    (255, 215, 0),   # Gold
    (255, 255, 0),   # Yellow
    (138, 43, 226),  # BlueViolet
    (75, 0, 130),    # Indigo
    (65, 105, 225)   # RoyalBlue
]

LASER_EFFECTS = [
    {"colors": FLAME_COLORS, "widths": [120, 140, 160, 180], "type": "flamethrower"},
    {"colors": [(173, 216, 230), (135, 206, 250)], "widths": [30, 50], "type": "ice"},
    {"colors": [(255, 20, 147), (255, 105, 180)], "widths": [40, 60], "type": "pink_magic"},
]

# Fonts and sizes
font_sizes = [260, 270, 280, 290, 210]
fonts = [pygame.font.Font(None, size) for size in font_sizes]
large_font = pygame.font.Font(None, 300)  # for watermark or big target display
small_font = pygame.font.Font(None, 36)
TARGET_FONT = pygame.font.Font(None, 840)  # new font for falling targets (doubled from 420 to 840 for 100% increase)
TITLE_FONT = pygame.font.Font(None, 640)  # Define a new title font (300% bigger than before based on fonts[2])

# Game constants
LETTER_SPAWN_INTERVAL = 30  # spawn interval in frames

# Global variables for effects and touches.
particles = []
shake_duration = 0
shake_magnitude = 10
active_touches = {}

# Declare explosions and lasers in global scope so they are available to all functions
explosions = []
lasers = []

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

def welcome_screen():
    """Show a static welcome screen (image only, no animation)."""
    # --- Draw everything ONCE to a surface ---
    static_surface = pygame.Surface((WIDTH, HEIGHT))
    # Vivid bright colors for particles
    particle_colors = [
        (255, 0, 128),   # Bright pink
        (0, 255, 128),   # Bright green
        (128, 0, 255),   # Bright purple
        (255, 128, 0),   # Bright orange
        (0, 128, 255)    # Bright blue
    ]
    # Draw static gravitational particles (random positions)
    grav_particles = []
    for _ in range(120):
        angle = random.uniform(0, math.pi * 2)
        distance = random.uniform(200, max(WIDTH, HEIGHT))
        x = WIDTH // 2 + math.cos(angle) * distance
        y = HEIGHT // 2 + math.sin(angle) * distance
        grav_particles.append({
            "x": x,
            "y": y,
            "color": random.choice(particle_colors),
            "size": random.randint(13, 17),
        })
    static_surface.fill(BLACK)
    for particle in grav_particles:
        pygame.draw.circle(static_surface, particle["color"],
                           (int(particle["x"]), int(particle["y"])),
                           particle["size"])
    # Smooth color transition for title (pick a random color)
    current_color = random.choice(FLAME_COLORS)
    next_color = random.choice(FLAME_COLORS)
    r = int(current_color[0] * 0.5 + next_color[0] * 0.5)
    g = int(current_color[1] * 0.5 + next_color[1] * 0.5)
    b = int(current_color[2] * 0.5 + next_color[2] * 0.5)
    title_color = (r, g, b)
    # Draw title with depth/glow effect (single frame)
    title_text = "Super Student"
    title_rect_center = (WIDTH // 2, HEIGHT // 2)
    shadow_color = (20, 20, 20)
    for depth in range(1, 0, -1):
        shadow = TITLE_FONT.render(title_text, True, shadow_color)
        shadow_rect = shadow.get_rect(center=(title_rect_center[0] + depth, title_rect_center[1] + depth))
        static_surface.blit(shadow, shadow_rect)
    glow_colors = [(r//2, g//2, b//2), (r//3, g//3, b//3)]
    for i, glow_color in enumerate(glow_colors):
        glow = TITLE_FONT.render(title_text, True, glow_color)
        offset = i + 1
        for dx, dy in [(-offset,0), (offset,0), (0,-offset), (0,offset)]:
            glow_rect = glow.get_rect(center=(title_rect_center[0] + dx, title_rect_center[1] + dy))
            static_surface.blit(glow, glow_rect)
    highlight_color = (min(r+80, 255), min(g+80, 255), min(b+80, 255))
    shadow_color = (max(r-90, 0), max(g-90, 0), max(b-90, 0))
    mid_color = (max(r-40, 0), max(g-40, 0), max(b-40, 0))
    highlight = TITLE_FONT.render(title_text, True, highlight_color)
    highlight_rect = highlight.get_rect(center=(title_rect_center[0] - 4, title_rect_center[1] - 4))
    static_surface.blit(highlight, highlight_rect)
    mid_tone = TITLE_FONT.render(title_text, True, mid_color)
    mid_rect = mid_tone.get_rect(center=(title_rect_center[0] + 2, title_rect_center[1] + 2))
    static_surface.blit(mid_tone, mid_rect)
    inner_shadow = TITLE_FONT.render(title_text, True, shadow_color)
    inner_shadow_rect = inner_shadow.get_rect(center=(title_rect_center[0] + 4, title_rect_center[1] + 4))
    static_surface.blit(inner_shadow, inner_shadow_rect)
    title = TITLE_FONT.render(title_text, True, title_color)
    title_rect = title.get_rect(center=title_rect_center)
    static_surface.blit(title, title_rect)
    # Instructions
    instructions = small_font.render("Click to start!", True, (255, 0, 0))
    instruction_rect = instructions.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 200))
    static_surface.blit(instructions, instruction_rect)
    # Pulsing SANGSOM text effect (pick a static pulse)
    pulse_factor = 0.5
    bright_yellow = (255, 255, 0)
    lite_yellow = (255, 255, 150)
    sangsom_color = tuple(int(bright_yellow[i] * (1 - pulse_factor) + lite_yellow[i] * pulse_factor) for i in range(3))
    collab_font = pygame.font.Font(None, 100)
    collab_text1 = collab_font.render("In collaboration with ", True, WHITE)
    collab_text2 = collab_font.render("SANGSOM", True, sangsom_color)
    collab_text3 = collab_font.render(" Kindergarten", True, WHITE)
    collab_rect1 = collab_text1.get_rect()
    collab_rect1.right = WIDTH // 2 - collab_text2.get_width() // 2
    collab_rect1.centery = HEIGHT // 2 + 350
    collab_rect2 = collab_text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 350))
    collab_rect3 = collab_text3.get_rect()
    collab_rect3.left = collab_rect2.right
    collab_rect3.centery = HEIGHT // 2 + 350
    static_surface.blit(collab_text1, collab_rect1)
    static_surface.blit(collab_text2, collab_rect2)
    static_surface.blit(collab_text3, collab_rect3)
    creator_text = small_font.render("Created by Teacher Evan and Teacher Lee", True, WHITE)
    creator_rect = creator_text.get_rect(center=(WIDTH // 2, HEIGHT - 40))
    static_surface.blit(creator_text, creator_rect)
    # --- Show the static image until click/quit ---
    running = True
    while running:
        screen.blit(static_surface, (0, 0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                running = False

def draw_neon_button(rect, base_color):
    """Draws a button with a neon glow effect."""
    # Fill the button with a dark background
    pygame.draw.rect(screen, (20, 20, 20), rect)
    # Draw a neon glow border by drawing multiple expanding outlines
    for i in range(1, 6):
        neon_rect = pygame.Rect(rect.x - i, rect.y - i, rect.width + 2*i, rect.height + 2*i)
        pygame.draw.rect(screen, base_color, neon_rect, 1)
    # Draw a solid border
    pygame.draw.rect(screen, base_color, rect, 2)

def level_menu():
    """Display the Level Options screen to choose the mission using a cyberpunk neon display."""
    running = True
    clock = pygame.time.Clock()
    # Button dimensions and positions (arranged in two rows)
    button_width = 300
    button_height = 80
    abc_rect = pygame.Rect((WIDTH // 2 - button_width - 20, HEIGHT // 2 - button_height - 10), (button_width, button_height))
    num_rect = pygame.Rect((WIDTH // 2 + 20, HEIGHT // 2 - button_height - 10), (button_width, button_height))
    shapes_rect = pygame.Rect((WIDTH // 2 - button_width - 20, HEIGHT // 2 + 10), (button_width, button_height))
    clcase_rect = pygame.Rect((WIDTH // 2 + 20, HEIGHT // 2 + 10), (button_width, button_height))
    colors_rect = pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 + 120), (300, 80))  # Add a new Colors button

    # Set up smooth color transition variables for the title
    color_transition = 0.0
    current_color = FLAME_COLORS[0]
    next_color = FLAME_COLORS[1]

    # Vivid bright colors for particles - similar to welcome screen
    particle_colors = [
        (255, 0, 128),   # Bright pink
        (0, 255, 128),   # Bright green
        (128, 0, 255),   # Bright purple
        (255, 128, 0),   # Bright orange
        (0, 128, 255)    # Bright blue
    ]

    # Create OUTWARD moving particles (reverse of welcome screen)
    repel_particles = []
    for _ in range(700):
        # Start particles near center
        angle = random.uniform(0, math.pi * 2)
        distance = random.uniform(10, 100)  # Close to center
        x = WIDTH // 2 + math.cos(angle) * distance
        y = HEIGHT // 2 + math.sin(angle) * distance
        repel_particles.append({
            "x": x,
            "y": y,
            "color": random.choice(particle_colors),
            "size": random.randint(5, 7),
            "speed": random.uniform(3.0, 6.0),
            "angle": angle  # Store the angle for outward movement
        })

    # Brief delay so that time-based effects start smoothly
    pygame.time.delay(100)

    while running:
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if abc_rect.collidepoint(mx, my):
                    return "alphabet"
                elif num_rect.collidepoint(mx, my):
                    return "numbers"
                elif shapes_rect.collidepoint(mx, my):
                    return "shapes"
                elif clcase_rect.collidepoint(mx, my):
                    return "clcase"
                elif colors_rect.collidepoint(mx, my):  # Handle Colors button click
                    return "colors"

        # Draw the outward moving particles
        for particle in repel_particles:
            # Move particles AWAY from center
            particle["x"] += math.cos(particle["angle"]) * particle["speed"]
            particle["y"] += math.sin(particle["angle"]) * particle["speed"]

            # Reset particles that move off screen
            if (particle["x"] < 0 or particle["x"] > WIDTH or
                particle["y"] < 0 or particle["y"] > HEIGHT):
                # New angle for variety
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(5, 50)  # Start close to center , was 50
                particle["x"] = WIDTH // 2 + math.cos(angle) * distance
                particle["y"] = HEIGHT // 2 + math.sin(angle) * distance
                particle["angle"] = angle
                particle["color"] = random.choice(particle_colors)
                particle["size"] = random.randint(13, 17)
                particle["speed"] = random.uniform(1.0, 3.0)

            # Draw the particle
            pygame.draw.circle(screen, particle["color"],
                              (int(particle["x"]), int(particle["y"])),
                              particle["size"])

        # Update title color transition
        color_transition += 0.01
        if color_transition >= 1:
            color_transition = 0
            current_color = next_color
            next_color = random.choice(FLAME_COLORS)
        r = int(current_color[0] * (1 - color_transition) + next_color[0] * color_transition)
        g = int(current_color[1] * (1 - color_transition) + next_color[1] * color_transition)
        b = int(current_color[2] * (1 - color_transition) + next_color[2] * color_transition)
        title_color = (r, g, b)

        # Draw title
        title_text = small_font.render("Choose Mission:", True, title_color)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
        screen.blit(title_text, title_rect)

        # Draw the A B C button with a neon cyberpunk look
        draw_neon_button(abc_rect, (255, 0, 150))
        abc_text = small_font.render("A B C", True, WHITE)
        abc_text_rect = abc_text.get_rect(center=abc_rect.center)
        screen.blit(abc_text, abc_text_rect)

        # Draw the 1 2 3 button with a neon cyberpunk look
        draw_neon_button(num_rect, (0, 200, 255))
        num_text = small_font.render("1 2 3", True, WHITE)
        num_text_rect = num_text.get_rect(center=num_rect.center)
        screen.blit(num_text, num_text_rect)

        # Draw the Shapes button with a neon cyberpunk look
        draw_neon_button(shapes_rect, (0, 255, 0))
        shapes_text = small_font.render("Shapes", True, WHITE)
        shapes_text_rect = shapes_text.get_rect(center=shapes_rect.center)
        screen.blit(shapes_text, shapes_text_rect)

        # Draw the new C/L Case Letters button
        draw_neon_button(clcase_rect, (255, 255, 0))
        clcase_text = small_font.render("C/L Case", True, WHITE)
        clcase_text_rect = clcase_text.get_rect(center=clcase_rect.center)
        screen.blit(clcase_text, clcase_text_rect)

        # Draw the new Colors button with a neon rainbow look
        draw_neon_button(colors_rect, (128, 0, 255))
        colors_text = small_font.render("Colors", True, WHITE)
        colors_text_rect = colors_text.get_rect(center=colors_rect.center)
        screen.blit(colors_text, colors_text_rect)

        pygame.display.flip()
        clock.tick(60)

###############################################################################
#                          GAME LOGIC & EFFECTS                               #
###############################################################################

def game_loop(mode):
    global shake_duration, shake_magnitude, particles, active_touches, explosions, lasers, player_color_transition, player_current_color, player_next_color, charging_ability, charge_timer, charge_particles, ability_target, swirl_particles, particles_converging, convergence_target, convergence_timer

    # REVERT: Restore swirl particles and explosion counts for levels gameplay
    create_swirl_particles(WIDTH // 2, HEIGHT // 2, count=50)  # Restore to 50

    # Reset all game states
    particles = []
    explosions = []
    lasers = []
    active_touches = {}
    charging_ability = False
    charge_timer = 0
    charge_particles = []
    ability_target = None
    swirl_particles = [] # Ensure swirl particles are reset
    particles_converging = False
    convergence_target = None
    convergence_timer = 0

    # Add a flag to prevent checkpoint screen after level completion
    just_completed_level = False

    # Add checkpoint delay counter
    checkpoint_delay_frames = 0
    checkpoint_waiting = False

    # Create sequence based on selected mode
    if mode == "alphabet":
        sequence = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    elif mode == "numbers":
        sequence = [str(i) for i in range(1, 27)]
    elif mode == "shapes":
        sequence = ["Rectangle", "Square", "Circle", "Triangle", "Pentagon"]
    elif mode == "clcase":  # New C/L Case letters mode
        sequence = list("abcdefghijklmnopqrstuvwxyz")
    elif mode == "colors":  # New Colors mode
        sequence = []  # Colors mode doesn't use sequence logic
    else:
        sequence = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") # Default or fallback

    # Split into groups of 5
    groups = [sequence[i:i+5] for i in range(0, len(sequence), 5)]

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
    overall_destroyed = 0  # <-- Initialize here to avoid UnboundLocalError
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
        # --- Setup ---
        COLORS_LIST = [
            (0, 0, 255),    # Blue
            (255, 0, 0),    # Red
            (0, 200, 0),    # Green
            (255, 255, 0),  # Yellow
            (128, 0, 255),  # Purple
        ]
        color_names = ["Blue", "Red", "Green", "Yellow", "Purple"]
        mother_color_idx = random.randint(0, len(COLORS_LIST) - 1)
        mother_color = COLORS_LIST[mother_color_idx]
        mother_color_name = color_names[mother_color_idx]
        center = (WIDTH // 2, HEIGHT // 2)
        mother_radius = 180
        vibration_frames = 30
        disperse_frames = 30
        running = True
        clock = pygame.time.Clock()
        score = 0
        # --- VICTORY: Only 10 dots needed ---
        target_dots_left = 10
        dots = []
        dots_active = False
        frame = 0
        overall_destroyed = 0  # <-- Already initialized above, but safe to re-initialize here

        # --- Mother Dot Vibration ---
        for vib in range(vibration_frames):
            screen.fill(BLACK)
            vib_x = center[0] + random.randint(-6, 6)
            vib_y = center[1] + random.randint(-6, 6)
            pygame.draw.circle(screen, mother_color, (vib_x, vib_y), mother_radius)
            # Draw label
            label = small_font.render("Remember this color!", True, WHITE)
            label_rect = label.get_rect(center=(WIDTH // 2, HEIGHT // 2 + mother_radius + 60))
            screen.blit(label, label_rect)
            # Remove all other text (set to black for easy finding)
            screen.blit(small_font.render("", True, BLACK), (0,0))
            pygame.display.flip()
            clock.tick(50)  # PERFORMANCE: Lower FPS

        # --- WAIT FOR CLICK TO START DISPERSION ---
        waiting_for_dispersion = True
        while waiting_for_dispersion:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    waiting_for_dispersion = False
            # Draw the mother dot and prompt
            screen.fill(BLACK)
            pygame.draw.circle(screen, mother_color, center, mother_radius)
            label = small_font.render("Remember this color!", True, WHITE)
            label_rect = label.get_rect(center=(WIDTH // 2, HEIGHT // 2 + mother_radius + 60))
            screen.blit(label, label_rect)
            prompt = small_font.render("Click to start!", True, (255, 255, 0))
            prompt_rect = prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + mother_radius + 120))
            screen.blit(prompt, prompt_rect)
            # Remove all other text (set to black for easy finding)
            screen.blit(small_font.render("", True, BLACK), (0,0))
            pygame.display.flip()
            clock.tick(50)  # PERFORMANCE: Lower FPS

        # --- Mother Dot Disperse Animation ---
        disperse_particles = []
        for i in range(100):
            angle = random.uniform(0, 2 * math.pi)
            disperse_particles.append({
                "angle": angle,
                "radius": 0,
                "speed": random.uniform(12, 18),
                "color": mother_color if i < 25 else None,  # Will assign distractor colors below
            })
        # Assign distractor colors (robust to any number of distractor colors)
        distractor_colors = [c for idx, c in enumerate(COLORS_LIST) if idx != mother_color_idx]
        num_distractor_colors = len(distractor_colors)
        total_distractor_dots = 75
        dots_per_color = total_distractor_dots // num_distractor_colors
        extra = total_distractor_dots % num_distractor_colors
        idx = 25
        for color_idx, color in enumerate(distractor_colors):
            count = dots_per_color + (1 if color_idx < extra else 0)
            for _ in range(count):
                if idx < 100:
                    disperse_particles[idx]["color"] = color
                    idx += 1

        # --- Initialize Bouncing Dots ---
        dots = []
        for i, p in enumerate(disperse_particles):
            x = int(center[0] + math.cos(p["angle"]) * p["radius"])
            y = int(center[1] + math.sin(p["angle"]) * p["radius"])
            dx = random.uniform(-6, 6)
            dy = random.uniform(-6, 6)
            dots.append({
                "x": x, "y": y,
                "dx": dx, "dy": dy,
                "color": p["color"],
                "radius": 24,  # was 22, now 10% bigger
                "target": True if p["color"] == mother_color else False,
                "alive": True,
            })
        dots_active = True
        for t in range(disperse_frames):
            screen.fill(BLACK)
            for p in disperse_particles:
                p["radius"] += p["speed"]
                x = int(center[0] + math.cos(p["angle"]) * p["radius"])
                y = int(center[1] + math.sin(p["angle"]) * p["radius"])
                pygame.draw.circle(screen, p["color"], (x, y), 24)
            # Remove all other text (set to black for easy finding)
            screen.blit(small_font.render("", True, BLACK), (0,0))
            pygame.display.flip()
            clock.tick(50)  # PERFORMANCE: Lower FPS

        # --- Main Colors Level Loop ---
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    break
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    for dot in dots:
                        if dot["alive"]:
                            dist = math.hypot(mx - dot["x"], my - dot["y"])
                            if dist <= dot["radius"]:
                                if dot["target"]:
                                    dot["alive"] = False
                                    target_dots_left -= 1
                                    score += 10
                                    overall_destroyed += 1  # <-- Increment destroyed count
                                    create_explosion(dot["x"], dot["y"], color=dot["color"], max_radius=60, duration=15)  # PERFORMANCE: shorter explosion
                                # No effect for distractors
                                break
            # --- Update Dots ---
            for dot in dots:
                if not dot["alive"]:
                    continue
                dot["x"] += dot["dx"]
                dot["y"] += dot["dy"]
                # Bounce off walls
                if dot["x"] - dot["radius"] < 0:
                    dot["x"] = dot["radius"]
                    dot["dx"] *= -1
                if dot["x"] + dot["radius"] > WIDTH:
                    dot["x"] = WIDTH - dot["radius"]
                    dot["dx"] *= -1
                if dot["y"] - dot["radius"] < 0:
                    dot["y"] = dot["radius"]
                    dot["dy"] *= -1
                if dot["y"] + dot["radius"] > HEIGHT:
                    dot["y"] = HEIGHT - dot["radius"]
                    dot["dy"] *= -1
            # --- Draw ---
            screen.fill(BLACK)
            # Draw all alive dots
            for dot in dots:
                if dot["alive"]:
                    pygame.draw.circle(screen, dot["color"], (int(dot["x"]), int(dot["y"])), dot["radius"])
            # Draw explosions
            for explosion in explosions[:]:
                if explosion["duration"] > 0:
                    draw_explosion(explosion)
                    explosion["duration"] -= 1
                else:
                    explosions.remove(explosion)
            # HUD
            info = small_font.render(f"Target Color: {mother_color_name}   Remaining: {target_dots_left}   Score: {score}", True, WHITE)
            screen.blit(info, (20, 20))
            # Show a sample target dot at top right
            pygame.draw.circle(screen, mother_color, (WIDTH - 60, 60), 24)
            pygame.draw.rect(screen, WHITE, (WIDTH - 90, 30, 60, 60), 2)
            # Remove all other text (set to black for easy finding)
            screen.blit(small_font.render("", True, BLACK), (0,0))
            display_info(score, "color", mother_color_name, overall_destroyed, 10, "colors")
            pygame.display.flip()
            clock.tick(50)  # PERFORMANCE: Lower FPS
            # End condition
            if target_dots_left <= 0:
                pygame.time.delay(500)
                well_done_screen(score)
                return True
        return False

    # --- Main Game Loop ---
    while running:

        # -------------------- Event Handling --------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
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
                        # --- Process Click on Target ---
                        for letter_obj in letters[:]:
                            if letter_obj["rect"].collidepoint(click_x, click_y):
                                if letter_obj["value"] == target_letter:
                                    score += 10
                                    # Common destruction effects
                                    create_explosion(letter_obj["x"], letter_obj["y"])
                                    create_flame_effect(player_x, player_y - 80, letter_obj["x"], letter_obj["y"])
                                    trigger_particle_convergence(letter_obj["x"], letter_obj["y"])
                                    apply_explosion_effect(letter_obj["x"], letter_obj["y"], 150, letters) # Apply push effect

                                    # Add visual feedback particles
                                    for i in range(20):
                                        particles.append({
                                            "x": letter_obj["x"], "y": letter_obj["y"],
                                            "color": random.choice(FLAME_COLORS),
                                            "size": random.randint(40, 80),
                                            "dx": random.uniform(-2, 2), "dy": random.uniform(-2, 2),
                                            "duration": 20
                                        })

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


            if event.type == pygame.FINGERDOWN:
                touch_id = event.finger_id
                touch_x = event.x * WIDTH
                touch_y = event.y * HEIGHT
                active_touches[touch_id] = (touch_x, touch_y)
                if not game_started:
                    game_started = True
                else:
                    # --- Process Touch on Target ---
                    for letter_obj in letters[:]:
                        if letter_obj["rect"].collidepoint(touch_x, touch_y):
                            if letter_obj["value"] == target_letter:
                                score += 10
                                # Common destruction effects
                                create_explosion(letter_obj["x"], letter_obj["y"])
                                create_flame_effect(player_x, player_y - 80, letter_obj["x"], letter_obj["y"])
                                trigger_particle_convergence(letter_obj["x"], letter_obj["y"])
                                apply_explosion_effect(letter_obj["x"], letter_obj["y"], 150, letters) # Apply push effect

                                # Add visual feedback particles
                                for i in range(20):
                                    particles.append({
                                        "x": letter_obj["x"], "y": letter_obj["y"],
                                        "color": random.choice(FLAME_COLORS),
                                        "size": random.randint(40, 80),
                                        "dx": random.uniform(-2, 2), "dy": random.uniform(-2, 2),
                                        "duration": 20
                                    })

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


            if event.type == pygame.FINGERUP:
                touch_id = event.finger_id
                if touch_id in active_touches:
                    del active_touches[touch_id]

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
        if shake_duration > 0:
            offset_x = random.randint(-shake_magnitude, shake_magnitude)
            offset_y = random.randint(-shake_magnitude, shake_magnitude)
            shake_duration -= 1
        else:
            offset_x, offset_y = 0, 0

        # Fill background (apply offset if shaking)
        screen.fill(WHITE) # Draw solid background first

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

        # --- Draw Swirling Particles around Center ---
        # Ensure swirl particles are updated even if target is a shape
        update_swirl_particles(player_x, player_y)


        # --- Draw Center Target Display ---
        # Smooth color transition for player target (center display)
        transition_speed = 0.02
        player_color_transition += transition_speed
        if player_color_transition >= 1:
            player_color_transition = 0
            current_index = FLAME_COLORS.index(player_current_color)
            next_index = (current_index + 1) % len(FLAME_COLORS)
            player_current_color = FLAME_COLORS[current_index]
            player_next_color = FLAME_COLORS[next_index]

        # Interpolate between current and next color
        r = int(player_current_color[0] * (1 - player_color_transition) + player_next_color[0] * player_color_transition)
        g = int(player_current_color[1] * (1 - player_color_transition) + player_next_color[1] * player_color_transition)
        b = int(player_current_color[2] * (1 - player_color_transition) + player_next_color[2] * player_color_transition)
        center_target_color = (r, g, b)

        if mode == "shapes":
            # Draw the center target display as a shape outline
            value = target_letter
            size = 500  # adjust size as needed for display
            pos = (player_x + offset_x, player_y + offset_y)
            outline_color = BLACK # Use black outline for shapes
            rect = pygame.Rect(pos[0] - int(size*1.5)//2, pos[1] - size//2, int(size*1.5), size)
            if value == "Rectangle":
                pygame.draw.rect(screen, outline_color, rect, 8)  # Border only, 1.5:1 aspect
            elif value == "Square":
                square_rect = pygame.Rect(pos[0] - size//2, pos[1] - size//2, size, size)
                pygame.draw.rect(screen, outline_color, square_rect, 8)  # Border only
            elif value == "Circle":
                pygame.draw.circle(screen, outline_color, pos, size//2, 8)  # Border only
            elif value == "Triangle":
                points = [
                    (pos[0], pos[1] - size//2),
                    (pos[0] - size//2, pos[1] + size//2),
                    (pos[0] + size//2, pos[1] + size//2)
                ]
                pygame.draw.polygon(screen, outline_color, points, 8)  # Border only
            elif value == "Pentagon":
                points = []
                r_size = size // 2
                for i in range(5):
                    angle = math.radians(72 * i - 90)
                    points.append((pos[0] + r_size * math.cos(angle), pos[1] + r_size * math.sin(angle)))
                pygame.draw.polygon(screen, outline_color, points, 8)  # Border only
        else:  # Alphabet, Numbers, C/L Case
            player_font = pygame.font.Font(None, 900)
            display_char = target_letter  # default

            # *** MODIFICATION START: always uppercase in C/L Case centre ***
            if mode == "clcase":
                display_char = target_letter.upper()
            elif mode == "alphabet" and target_letter == "a":
                display_char = "α"  # keep Greek alpha only in alphabet mode
            # *** MODIFICATION END ***

            player_text = player_font.render(display_char, True, center_target_color)
            player_rect = player_text.get_rect(center=(player_x + offset_x, player_y + offset_y))
            screen.blit(player_text, player_rect)


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

            if mode == "shapes":
                value = letter_obj["value"]
                color = BLACK # always draw falling shapes as solid BLACK border
                size = letter_obj["size"]
                pos = (draw_pos_x, draw_pos_y)
                if value == "Rectangle":
                    rect = pygame.Rect(pos[0] - int(size*1.5)//2, pos[1] - size//2, int(size*1.5), size)
                    letter_obj["rect"] = rect
                    pygame.draw.rect(screen, color, rect, 6)  # Border only, 1.5:1 aspect
                elif value == "Square":
                    rect = pygame.Rect(pos[0]-size//2, pos[1]-size//2, size, size)
                    letter_obj["rect"] = rect
                    pygame.draw.rect(screen, color, rect, 6)  # Border only
                elif value == "Circle":
                    rect = pygame.Rect(pos[0]-size//2, pos[1]-size//2, size, size)
                    letter_obj["rect"] = rect
                    pygame.draw.circle(screen, color, pos, size//2, 6)  # Border only
                elif value == "Triangle":
                    points = [
                        (pos[0], pos[1] - size//2),
                        (pos[0] - size//2, pos[1] + size//2),
                        (pos[0] + size//2, pos[1] + size//2)
                    ]
                    letter_obj["rect"] = pygame.Rect(pos[0]-size//2, pos[1]-size//2, size, size)
                    pygame.draw.polygon(screen, color, points, 6)  # Border only
                elif value == "Pentagon":
                    cx, cy = pos
                    r = size // 2
                    points = []
                    for i in range(5):
                        angle = math.radians(72 * i - 90)
                        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
                    letter_obj["rect"] = pygame.Rect(cx-r, cy-r, size, size)
                    pygame.draw.polygon(screen, color, points, 6)  # Border only
            else: # Alphabet, Numbers, C/L Case
                display_value = letter_obj["value"] # Default character to display

                # *** MODIFICATION START: handle 'a' -> 'α' for falling letters in C/L Case ***
                if mode == "clcase" and letter_obj["value"] == "a":
                    display_value = "α"
                # *** MODIFICATION END ***

                # Use gray for non-target letters, black for the target letter
                text_color = BLACK if letter_obj["value"] == target_letter else (150, 150, 150)
                text_surface = TARGET_FONT.render(display_value, True, text_color)
                text_rect = text_surface.get_rect(center=(draw_pos_x, draw_pos_y))
                letter_obj["rect"] = text_rect # Update rect for collision detection
                screen.blit(text_surface, text_rect)


        # --- Simple Collision Detection Between Items ---
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


        # --- Process Lasers / Flame Effects ---
        for laser in lasers[:]:
            if laser["duration"] > 0:
                if laser["type"] == "flamethrower":
                    draw_flamethrower(laser, offset_x, offset_y) # Pass shake offset
                # Add other laser types if needed (ice, pink_magic)
                # else:
                #     pygame.draw.line(screen, random.choice(laser["colors"]),
                #                      (laser["start_pos"][0] + offset_x, laser["start_pos"][1] + offset_y),
                #                      (laser["end_pos"][0] + offset_x, laser["end_pos"][1] + offset_y),
                #                       random.choice(laser["widths"]))
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
                            particles.append({
                                "x": particle["x"], "y": particle["y"],
                                "color": particle["color"], "size": particle["size"] / 2,
                                "dx": -norm_dx * 0.5, "dy": -norm_dy * 0.5,
                                "duration": 50 # Shorter trail duration
                            })

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
        for particle in particles[:]:
            if particle["duration"] > 0:
                particle["x"] += particle["dx"]
                particle["y"] += particle["dy"]
                particle["duration"] -= 1
                # Apply fading effect
                alpha = max(0, 255 * (particle["duration"] / particle.get("start_duration", 30))) # Fade out
                color = (*particle["color"][:3], int(alpha))

                # Draw particle with alpha (apply shake offset)
                # Need to use SRCALPHA surface for transparency
                size = int(particle["size"])
                if size > 0:
                    particle_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surf, color, (size, size), size)
                    screen.blit(particle_surf, (int(particle["x"] - size + offset_x), int(particle["y"] - size + offset_y)))

            else:
                particles.remove(particle)

        # --- Display HUD Info ---
        if mode != "colors":
            display_info(score, current_ability, target_letter, overall_destroyed + letters_destroyed, TOTAL_LETTERS, mode) # Pass mode

        # --- Player Trail Effect (less relevant if player doesn't move) ---
        # if game_started:
        #     create_player_trail(player_x, player_y)


        # --- Update Display ---
        pygame.display.flip()
        clock.tick(50)  # PERFORMANCE: Lower FPS for all main game loops
        frame_count += 1


        # --- Checkpoint Logic ---
        overall_destroyed = total_destroyed + letters_destroyed

        # If waiting for animations before showing checkpoint screen
        if checkpoint_waiting:
            # Only show checkpoint after delay AND when animations are mostly complete
            if checkpoint_delay_frames <= 0 and len(explosions) <= 1 and len(lasers) <= 1 and not particles_converging:
                checkpoint_waiting = False
                game_started = False  # Pause the game
                if not checkpoint_screen(): # If checkpoint returns False (chose Menu)
                    running = False # Exit game loop to return to menu
                    break
                else:
                    game_started = True # Resume game if continuing
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
                # --- All Groups Completed ---
                # Ensure final count matches total expected
                if total_destroyed >= TOTAL_LETTERS:
                    if well_done_screen(score): # If well_done returns True (clicked next mission)
                        running = False # Exit game loop to go back to menu
                        break
                    else: # Should not happen if well_done forces click
                        running = False
                        break
                else:
                    # This case might indicate an issue if not all letters were destroyed
                    print(f"Warning: Game ended but total destroyed ({total_destroyed}) doesn't match total letters ({TOTAL_LETTERS}).")
                    running = False # End game loop
                    break

    # --- End of Main Game Loop ---
    # Return True if we exited to go back to the menu (e.g., from checkpoint or well_done)
    # Return False if we exited via ESC or Quit event
    return True if running == False else False # A bit confusing, revise this return logic if needed


###############################################################################
#                          SUPPORT FUNCTIONS                                  #
###############################################################################

def create_flame_effect(start_x, start_y, end_x, end_y):
    """Creates a laser/flame visual effect between two points."""
    global lasers
    # Always use flamethrower effect for now
    effect = LASER_EFFECTS[0] # Force flamethrower
    # effect = random.choice(LASER_EFFECTS) # Or choose randomly
    lasers.append({
        "start_pos": (start_x, start_y),
        "end_pos": (end_x, end_y),
        "colors": effect["colors"],
        "widths": effect["widths"], # Used by draw_flamethrower indirectly
        "duration": 10, # Short duration visual effect
        "type": effect["type"],
    })

def draw_flamethrower(laser, offset_x=0, offset_y=0):
    """Draws a flamethrower style effect using circles along a line."""
    start_x, start_y = laser["start_pos"]
    end_x, end_y = laser["end_pos"]
    dx = end_x - start_x
    dy = end_y - start_y
    length = math.hypot(dx, dy)
    if length == 0: return # Avoid division by zero

    angle = math.atan2(dy, dx)
    num_circles = int(length / 10) # Draw a circle every 10 pixels

    for i in range(num_circles):
        # Interpolate position along the line
        ratio = i / num_circles
        x = start_x + dx * ratio
        y = start_y + dy * ratio
        # Vary radius and color for flame effect
        radius = random.randint(20, 40 + int(20 * (1-ratio))) # Wider near start
        color = random.choice(laser["colors"])
        # Apply shake offset
        draw_x = int(x + offset_x)
        draw_y = int(y + offset_y)
        # Draw with alpha for softer edges (optional)
        flame_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(flame_surf, (*color, 180), (radius, radius), radius)
        screen.blit(flame_surf, (draw_x - radius, draw_y - radius))
        # pygame.draw.circle(screen, color, (draw_x, draw_y), radius)


def create_explosion(x, y, color=None, max_radius=270, duration=30):
    """Adds an explosion effect to the list."""
    global shake_duration, explosions
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


def display_info(score, ability, target_letter, overall_destroyed, total_letters, mode):
    """Displays the HUD elements (Score, Ability, Target, Progress)."""
    # Left-aligned elements
    score_text = small_font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (20, 20))
    ability_text = small_font.render(f"Ability: {ability.capitalize()}", True, BLACK)
    ability_rect = ability_text.get_rect(topleft=(20, 60))
    screen.blit(ability_text, ability_rect)

    # Right-aligned elements
    display_target = target_letter
    # *** MODIFICATION START: handle 'a' -> 'α' in HUD Target display ***
    if (mode == "alphabet" or mode == "clcase") and target_letter == "a":
         display_target = "α"
    # *** MODIFICATION END ***
    elif mode == "clcase":
        # Show uppercase in HUD for C/L case target
        display_target = target_letter.upper()

    target_text = small_font.render(f"Target: {display_target}", True, BLACK)
    target_rect = target_text.get_rect(topright=(WIDTH - 20, 20))
    screen.blit(target_text, target_rect)

    progress_text = small_font.render(f"Destroyed: {overall_destroyed}/{total_letters}", True, BLACK)
    progress_rect = progress_text.get_rect(topright=(WIDTH - 20, 60))
    screen.blit(progress_text, progress_rect)


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


def checkpoint_screen():
    """Display the checkpoint screen after every 10 targets with options."""
    running = True
    clock = pygame.time.Clock()
    color_transition = 0.0
    current_color = FLAME_COLORS[0]
    next_color = FLAME_COLORS[1]

    # Button dimensions and positions
    button_width = 300
    button_height = 80
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    continue_rect = pygame.Rect((center_x - button_width - 20, center_y + 50), (button_width, button_height))
    menu_rect = pygame.Rect((center_x + 20, center_y + 50), (button_width, button_height))

    # Restore checkpoint screen swirling particles
    swirling_particles = []
    for _ in range(150):  # Restore to 150
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(100, max(WIDTH, HEIGHT) * 0.6) # Start further out
        angular_speed = random.uniform(0.01, 0.03) * random.choice([-1, 1]) # Slower swirl
        radius = random.randint(5, 10)
        color = random.choice(FLAME_COLORS)
        swirling_particles.append({
            "angle": angle, "distance": distance, "angular_speed": angular_speed,
            "radius": radius, "color": color
        })

    while running:
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if continue_rect.collidepoint(mx, my):
                    return True  # Continue game
                elif menu_rect.collidepoint(mx, my):
                    return False  # Return to level menu

        # Update and draw swirling particles
        for particle in swirling_particles:
            particle["angle"] += particle["angular_speed"]
            # Optional: Add slight inward/outward drift or pulse
            # particle["distance"] += math.sin(particle["angle"]) * 0.1
            x = center_x + particle["distance"] * math.cos(particle["angle"])
            y = center_y + particle["distance"] * math.sin(particle["angle"])
            pygame.draw.circle(screen, particle["color"], (int(x), int(y)), particle["radius"])
            # Keep particles within a reasonable boundary (optional)
            if particle["distance"] > max(WIDTH, HEIGHT) * 0.8:
                 particle["distance"] = random.uniform(50, 200) # Reset closer


        # Smooth color transition for heading
        color_transition += 0.02
        if color_transition >= 1:
            color_transition = 0
            current_color = next_color
            next_color = random.choice(FLAME_COLORS)
        r = int(current_color[0] * (1 - color_transition) + next_color[0] * color_transition)
        g = int(current_color[1] * (1 - color_transition) + next_color[1] * color_transition)
        b = int(current_color[2] * (1 - color_transition) + next_color[2] * color_transition)
        heading_color = (r, g, b)

        # Draw heading
        checkpoint_font = fonts[2] # Use a larger font
        checkpoint_text = checkpoint_font.render("Checkpoint!", True, heading_color)
        checkpoint_rect = checkpoint_text.get_rect(center=(center_x, center_y - 150))
        screen.blit(checkpoint_text, checkpoint_rect)

        # Additional message
        subtext = small_font.render("10 targets destroyed!", True, WHITE)
        subtext_rect = subtext.get_rect(center=(center_x, center_y - 100))
        screen.blit(subtext, subtext_rect)

        # Draw buttons with neon effect
        draw_neon_button(continue_rect, (0, 255, 0)) # Green for continue
        draw_neon_button(menu_rect, (255, 165, 0))   # Orange for menu

        cont_text = small_font.render("Continue", True, WHITE)
        menu_text = small_font.render("Menu", True, WHITE)
        screen.blit(cont_text, cont_text.get_rect(center=continue_rect.center))
        screen.blit(menu_text, menu_text.get_rect(center=menu_rect.center))

        pygame.display.flip()
        clock.tick(60)

def create_player_trail(x, y):
    """Creates trail particles behind the (currently static) player position."""
    # This might be less useful if the player doesn't move, but kept for potential future use.
    for _ in range(1): # Reduce particle count for static player
        particles.append({
            "x": x + random.uniform(-10, 10), # Spawn around center
            "y": y + random.uniform(-10, 10),
            "color": random.choice(FLAME_COLORS),
            "size": random.randint(2, 4),
            "dx": random.uniform(-0.2, 0.2), # Slow drift
            "dy": random.uniform(-0.2, 0.2),
            "duration": 20, # Shorter duration
            "start_duration": 20
        })

# Restore charge particle count for charge-up effect
def start_charge_up_effect(player_x, player_y, target_x, target_y):
    global charging_ability, charge_timer, charge_particles, ability_target
    charging_ability = True
    charge_timer = 45
    ability_target = (target_x, target_y)
    charge_particles = []
    for _ in range(150):  # Restore to 150
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

# Restore swirl particle count for create_swirl_particles
def create_swirl_particles(center_x, center_y, radius=150, count=50):  # Restore to 50
    global swirl_particles
    swirl_particles = [] # Clear existing ones

    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        # Start particles within a tighter band around the target radius
        distance = random.uniform(radius * 0.8, radius * 1.2)
        angular_speed = random.uniform(0.02, 0.05) * random.choice([-1, 1])
        particle_radius = random.randint(3, 6) # Slightly larger swirl particles
        color = random.choice(FLAME_COLORS)

        swirl_particles.append({
            "angle": angle,
            "distance": distance,
            "base_distance": distance, # Store original distance for pulsing
            "angular_speed": angular_speed,
            "radius": particle_radius,
            "color": color,
            "pulse_offset": random.uniform(0, 2 * math.pi), # For varied pulsing
            "pulse_speed": random.uniform(0.03, 0.06) # Slightly faster pulse
        })

def update_swirl_particles(center_x, center_y):
    """Updates and draws swirling particles, handles convergence."""
    global swirl_particles, particles_converging, convergence_timer, convergence_target

    # Add occasional new particles if count is low
    if len(swirl_particles) < 30 and random.random() < 0.1:
         create_swirl_particles(center_x, center_y, count=10) # Add a few more

    current_time_ms = pygame.time.get_ticks() # Use milliseconds for smoother pulsing
    particles_to_remove = []

    for particle in swirl_particles:
        if particles_converging and convergence_target:
            # --- Convergence Logic ---
            target_x, target_y = convergence_target
            # Calculate vector towards target
            dx = target_x - (center_x + particle["distance"] * math.cos(particle["angle"]))
            dy = target_y - (center_y + particle["distance"] * math.sin(particle["angle"]))
            dist_to_target = math.hypot(dx, dy)

            if dist_to_target > 15: # Move until close
                # Move particle directly towards target
                move_speed = 8 # Adjust convergence speed
                particle["angle"] = math.atan2(dy, dx) # Point towards target (less relevant now)
                # Update distance directly based on speed towards target
                particle["distance"] = max(0, particle["distance"] - move_speed) # Move inward
                # Or update x/y directly:
                # current_x = center_x + particle["distance"] * math.cos(particle["angle"])
                # current_y = center_y + particle["distance"] * math.sin(particle["angle"])
                # current_x += (dx / dist_to_target) * move_speed
                # current_y += (dy / dist_to_target) * move_speed
                # # Recalculate angle/distance if needed, or just use x/y (simpler)
                # particle["x"] = current_x # Need to store x/y if not using angle/dist
                # particle["y"] = current_y

            else:
                # Particle reached target, mark for removal and explosion
                particles_to_remove.append(particle)
                continue
        else:
            # --- Normal Swirling Motion ---
            particle["angle"] += particle["angular_speed"]
            # Pulsing distance effect
            pulse = math.sin(current_time_ms * 0.001 * particle["pulse_speed"] + particle["pulse_offset"]) * 20 # Pulse magnitude
            particle["distance"] = particle["base_distance"] + pulse


        # Calculate particle position (common for both modes)
        x = center_x + particle["distance"] * math.cos(particle["angle"])
        y = center_y + particle["distance"] * math.sin(particle["angle"])

        # Draw particle with glow effect
        glow_radius = particle["radius"] * 1.5
        glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*particle["color"], 60), (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (int(x - glow_radius), int(y - glow_radius)))

        # Draw main particle
        pygame.draw.circle(screen, particle["color"], (int(x), int(y)), particle["radius"])


    # --- Handle Removed Particles (Reached Convergence Target) ---
    if particles_to_remove and convergence_target:
        target_x, target_y = convergence_target
        for particle in particles_to_remove:
            if particle in swirl_particles: # Ensure it wasn't already removed
                 swirl_particles.remove(particle)

            # Create mini-explosion effect at convergence point
            for _ in range(3): # Fewer particles per mini-explosion
                explosion_color = particle["color"]
                particles.append({ # Add to main particle list
                    "x": target_x + random.uniform(-5, 5), # Slight spread
                    "y": target_y + random.uniform(-5, 5),
                    "color": explosion_color,
                    "size": random.uniform(8, 16), # Smaller explosion particles
                    "dx": random.uniform(-1.5, 1.5),
                    "dy": random.uniform(-1.5, 1.5),
                    "duration": random.randint(20, 40),
                    "start_duration": 40
                })

        # Add a small shockwave effect once when particles hit
        if random.random() < 0.5: # Chance to add shockwave
             create_explosion(target_x, target_y, color=random.choice(FLAME_COLORS), max_radius=100, duration=20)


    # --- Reset Convergence State ---
    if particles_converging:
        convergence_timer -= 1
        if convergence_timer <= 0 or not swirl_particles: # Stop if timer runs out or no particles left
            particles_converging = False
            convergence_target = None
            # Optionally regenerate particles if too few remain
            if len(swirl_particles) < 20:
                 create_swirl_particles(center_x, center_y, count=30) # Regenerate some


def trigger_particle_convergence(target_x, target_y):
    """Triggers swirling particles to converge toward a target point."""
    global particles_converging, convergence_target, convergence_timer
    if not particles_converging: # Prevent re-triggering while already converging
        particles_converging = True
        convergence_target = (target_x, target_y)
        convergence_timer = 30  # Duration for convergence (frames)

        # Optional: Add a visual pulse from center towards target
        # dx = target_x - (WIDTH // 2)
        # dy = target_y - (HEIGHT // 2)
        # dist = math.hypot(dx, dy)
        # if dist > 0:
        #     for i in range(5):
        #         particles.append({
        #             "x": WIDTH // 2, "y": HEIGHT // 2,
        #             "color": random.choice(FLAME_COLORS),
        #             "size": random.uniform(4, 8),
        #             "dx": (dx / dist) * (5 + i), # Pulse outwards towards target
        #             "dy": (dy / dist) * (5 + i),
        #             "duration": 15, "start_duration": 15
        #         })


###############################################################################
#                                MAIN                                       #
###############################################################################

if __name__ == "__main__":
    try:
        while True:
            welcome_screen()
            mode = level_menu()
            if mode:  # Check if a valid mode was selected
                # Keep looping the game for the selected mode until user chooses 'Menu'
                # from checkpoint or finishes the level set.
                while game_loop(mode):
                    # If game_loop returns True, it means user chose 'Menu' or finished.
                    # We break this inner loop to go back to the level_menu().
                    break
            else:
                # If level_menu returns None (e.g., user closed window during menu)
                break # Exit the main application loop
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc() # Print detailed traceback
    finally:
        pygame.quit() 