import pygame
import random
import math
from settings import (
    DISPLAY_MODES, DEFAULT_MODE, DISPLAY_SETTINGS_PATH,
    WHITE, BLACK, FLAME_COLORS, DEBUG_MODE, SHOW_FPS
)

def detect_display_type():
    """Function to determine initial display mode based on screen size."""
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h
    
    # If screen is larger than typical desktop monitors, assume it's a QBoard
    if screen_w >= 1920 and screen_h >= 1080:
        if screen_w > 2560 or screen_h > 1440:  # Larger than QHD is likely QBoard
            return "QBOARD"
    
    # Default to smaller format for typical monitors/laptops
    return "DEFAULT"

def draw_neon_button(screen, rect, base_color):
    """Draws a button with a neon glow effect."""
    # Fill the button with a dark background
    pygame.draw.rect(screen, (20, 20, 20), rect)
    # Draw a neon glow border by drawing multiple expanding outlines
    for i in range(1, 6):
        neon_rect = pygame.Rect(rect.x - i, rect.y - i, rect.width + 2*i, rect.height + 2*i)
        pygame.draw.rect(screen, base_color, neon_rect, 1)
    # Draw a solid border
    pygame.draw.rect(screen, base_color, rect, 2)

def level_menu(WIDTH, HEIGHT, screen, small_font):
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
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
        draw_neon_button(screen, abc_rect, (255, 0, 150))
        abc_text = small_font.render("A B C", True, WHITE)
        abc_text_rect = abc_text.get_rect(center=abc_rect.center)
        screen.blit(abc_text, abc_text_rect)

        # Draw the 1 2 3 button with a neon cyberpunk look
        draw_neon_button(screen, num_rect, (0, 200, 255))
        num_text = small_font.render("1 2 3", True, WHITE)
        num_text_rect = num_text.get_rect(center=num_rect.center)
        screen.blit(num_text, num_text_rect)

        # Draw the Shapes button with a neon cyberpunk look
        draw_neon_button(screen, shapes_rect, (0, 255, 0))
        shapes_text = small_font.render("Shapes", True, WHITE)
        shapes_text_rect = shapes_text.get_rect(center=shapes_rect.center)
        screen.blit(shapes_text, shapes_text_rect)

        # Draw the new C/L Case Letters button
        draw_neon_button(screen, clcase_rect, (255, 255, 0))
        clcase_text = small_font.render("C/L Case", True, WHITE)
        clcase_text_rect = clcase_text.get_rect(center=clcase_rect.center)
        screen.blit(clcase_text, clcase_text_rect)

        # Draw the new Colors button with a neon rainbow look
        draw_neon_button(screen, colors_rect, (128, 0, 255))
        colors_text = small_font.render("Colors", True, WHITE)
        colors_text_rect = colors_text.get_rect(center=colors_rect.center)
        screen.blit(colors_text, colors_text_rect)

        pygame.display.flip()
        clock.tick(60)

def welcome_screen(WIDTH, HEIGHT, screen, small_font, init_resources_callback):
    """Show the welcome screen with display size options."""
    # Initialize with default mode first
    DISPLAY_MODE = DEFAULT_MODE

    # Try to load previous display mode setting
    try:
        with open(DISPLAY_SETTINGS_PATH, "r") as f:
            loaded_mode = f.read().strip()
            if loaded_mode in DISPLAY_MODES:
                DISPLAY_MODE = loaded_mode
    except:
        # If file doesn't exist or can't be read, use auto-detection
        DISPLAY_MODE = detect_display_type()
    
    # Calculate scaling factor based on current screen size
    # This ensures welcome screen elements fit properly on any display
    base_height = 1080  # Base design height
    scale_factor = HEIGHT / base_height
    
    # Apply scaling to title and buttons
    title_offset = int(50 * scale_factor)
    button_width = int(200 * scale_factor)
    button_height = int(60 * scale_factor)
    button_spacing = int(20 * scale_factor)
    button_y_pos = int(200 * scale_factor)
    instruction_y_pos = int(150 * scale_factor)
    
    # Vivid bright colors for particles
    particle_colors = [
        (255, 0, 128),   # Bright pink
        (0, 255, 128),   # Bright green
        (128, 0, 255),   # Bright purple
        (255, 128, 0),   # Bright orange
        (0, 128, 255)    # Bright blue
    ]
    
    # Create dynamic gravitational particles that orbit around the title
    particles = []
    for _ in range(120):
        angle = random.uniform(0, math.pi * 2)
        distance = random.uniform(200, max(WIDTH, HEIGHT) * 0.4)
        x = WIDTH // 2 + math.cos(angle) * distance
        y = HEIGHT // 2 + math.sin(angle) * distance
        size = random.randint(int(9 * scale_factor), int(15 * scale_factor))
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
    
    # Button hover state tracking
    default_hover = False
    qboard_hover = False
    
    # Create buttons for display size options
    default_button = pygame.Rect((WIDTH // 2 - button_width - button_spacing, HEIGHT // 2 + button_y_pos), (button_width, button_height))
    qboard_button = pygame.Rect((WIDTH // 2 + button_spacing, HEIGHT // 2 + button_y_pos), (button_width, button_height))
    
    # Set up smooth color transition variables for the title
    color_transition = 0.0
    color_transition_speed = 0.01
    current_color = random.choice(FLAME_COLORS)
    next_color = random.choice(FLAME_COLORS)
    
    # Scale collaboration font based on display size
    collab_font_size = int(100 * scale_factor)
    collab_font = pygame.font.Font(None, collab_font_size)
    
    # Use scaled font size for title based on current display
    title_font_size = int(320 * scale_factor)
    title_font = pygame.font.Font(None, title_font_size)
    
    # For title floating effect
    title_offset_y = 0
    title_float_speed = 0.002
    title_float_direction = 1
    
    # Get the auto-detected display type
    detected_display = detect_display_type()
    
    # --- Main welcome screen loop with animations ---
    running = True
    clock = pygame.time.Clock()
    last_time = pygame.time.get_ticks()
    
    while running:
        # Calculate delta time for smooth animations regardless of FPS
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - last_time) / 1000.0  # Convert to seconds
        last_time = current_time
        
        # Clear events at the start of each frame - collect all events first
        events = pygame.event.get()
        
        # Handle events
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if default_button.collidepoint(mx, my):
                    DISPLAY_MODE = "DEFAULT"
                    init_resources_callback()
                    running = False
                elif qboard_button.collidepoint(mx, my):
                    DISPLAY_MODE = "QBOARD"
                    init_resources_callback()
                    running = False
        
        # Get mouse position for hover effects
        mx, my = pygame.mouse.get_pos()
        default_hover = default_button.collidepoint(mx, my)
        qboard_hover = qboard_button.collidepoint(mx, my)
        
        # Update color transition
        color_transition += color_transition_speed * delta_time * 60
        if color_transition >= 1.0:
            color_transition = 0.0
            current_color = next_color
            next_color = random.choice([c for c in FLAME_COLORS if c != current_color])
        
        # Calculate interpolated title color
        r = int(current_color[0] * (1 - color_transition) + next_color[0] * color_transition)
        g = int(current_color[1] * (1 - color_transition) + next_color[1] * color_transition)
        b = int(current_color[2] * (1 - color_transition) + next_color[2] * color_transition)
        title_color = (r, g, b)
        
        # Update title floating effect
        title_offset_y += title_float_direction * title_float_speed * delta_time * 60
        if abs(title_offset_y) > 10:
            title_float_direction *= -1
        
        # Update particles
        for particle in particles:
            # Orbital movement
            particle["angle"] += particle["orbit_speed"] * delta_time * 60
            particle["x"] = WIDTH // 2 + math.cos(particle["angle"]) * particle["orbit_distance"]
            particle["y"] = HEIGHT // 2 + math.sin(particle["angle"]) * particle["orbit_distance"]
            
            # Pulsing effect
            particle["pulse_factor"] += particle["pulse_speed"] * delta_time * 60
            if particle["pulse_factor"] > 1.0:
                particle["pulse_factor"] = 0.0
            pulse = 0.7 + 0.3 * math.sin(particle["pulse_factor"] * math.pi * 2)
            particle["size"] = particle["orig_size"] * pulse
        
        # Draw everything
        screen.fill(BLACK)
        
        # Draw orbiting particles
        for particle in particles:
            pygame.draw.circle(screen, particle["color"],
                             (int(particle["x"]), int(particle["y"])),
                             int(particle["size"]))
        
        # Calculate title position with float effect
        title_rect_center = (WIDTH // 2, HEIGHT // 2 - title_offset + title_offset_y)
        
        # Draw title with depth/glow effect
        title_text = "Super Student"
        shadow_color = (20, 20, 20)
        for depth in range(1, 0, -1):
            shadow = title_font.render(title_text, True, shadow_color)
            shadow_rect = shadow.get_rect(center=(title_rect_center[0] + depth, title_rect_center[1] + depth))
            screen.blit(shadow, shadow_rect)
        
        # Add dynamic glow based on title color
        glow_colors = [(r//2, g//2, b//2), (r//3, g//3, b//3)]
        for i, glow_color in enumerate(glow_colors):
            glow = title_font.render(title_text, True, glow_color)
            offset = i + 1
            for dx, dy in [(-offset,0), (offset,0), (0,-offset), (0,offset)]:
                glow_rect = glow.get_rect(center=(title_rect_center[0] + dx, title_rect_center[1] + dy))
                screen.blit(glow, glow_rect)
        
        # Create the 3D effect with highlight and shadow
        highlight_color = (min(r+80, 255), min(g+80, 255), min(b+80, 255))
        shadow_color = (max(r-90, 0), max(g-90, 0), max(b-90, 0))
        mid_color = (max(r-40, 0), max(g-40, 0), max(b-40, 0))
        
        highlight = title_font.render(title_text, True, highlight_color)
        highlight_rect = highlight.get_rect(center=(title_rect_center[0] - 4, title_rect_center[1] - 4))
        screen.blit(highlight, highlight_rect)
        
        mid_tone = title_font.render(title_text, True, mid_color)
        mid_rect = mid_tone.get_rect(center=(title_rect_center[0] + 2, title_rect_center[1] + 2))
        screen.blit(mid_tone, mid_rect)
        
        inner_shadow = title_font.render(title_text, True, shadow_color)
        inner_shadow_rect = inner_shadow.get_rect(center=(title_rect_center[0] + 4, title_rect_center[1] + 4))
        screen.blit(inner_shadow, inner_shadow_rect)
        
        title = title_font.render(title_text, True, title_color)
        title_rect = title.get_rect(center=title_rect_center)
        screen.blit(title, title_rect)
        
        # Instructions
        display_text = small_font.render("Choose Display Size:", True, (255, 255, 255))
        display_rect = display_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + instruction_y_pos))
        screen.blit(display_text, display_rect)
        
        # Draw default button with hover effect
        pygame.draw.rect(screen, (20, 20, 20), default_button)
        glow_intensity = 6 if default_hover else 5
        for i in range(1, glow_intensity):
            multiplier = 1.5 if default_hover else 1.0
            alpha_factor = (1 - i/glow_intensity) * multiplier
            glow_color = (0, min(int(200 + 55 * default_hover * alpha_factor), 255), 255)
            default_rect = pygame.Rect(default_button.x - i, default_button.y - i, default_button.width + 2*i, default_button.height + 2*i)
            pygame.draw.rect(screen, glow_color, default_rect, 1)
        border_width = 3 if default_hover else 2
        pygame.draw.rect(screen, (0, 200, 255), default_button, border_width)
        default_text = small_font.render("Default", True, WHITE)
        default_text_rect = default_text.get_rect(center=default_button.center)
        screen.blit(default_text, default_text_rect)
        
        # Draw QBoard button with hover effect
        pygame.draw.rect(screen, (20, 20, 20), qboard_button)
        glow_intensity = 6 if qboard_hover else 5
        for i in range(1, glow_intensity):
            multiplier = 1.5 if qboard_hover else 1.0
            alpha_factor = (1 - i/glow_intensity) * multiplier
            glow_color = (min(int(255 * multiplier * alpha_factor), 255), 0, min(int(150 * multiplier * alpha_factor), 255))
            qboard_rect = pygame.Rect(qboard_button.x - i, qboard_button.y - i, qboard_button.width + 2*i, qboard_button.height + 2*i)
            pygame.draw.rect(screen, glow_color, qboard_rect, 1)
        border_width = 3 if qboard_hover else 2
        pygame.draw.rect(screen, (255, 0, 150), qboard_button, border_width)
        qboard_text = small_font.render("QBoard", True, WHITE)
        qboard_text_rect = qboard_text.get_rect(center=qboard_button.center)
        screen.blit(qboard_text, qboard_text_rect)
        
        # Auto-detected mode indicator with pulsing effect if it matches a button
        auto_text_color = (200, 200, 200)
        if detected_display == "DEFAULT" and default_hover:
            pulse = 0.5 + 0.5 * math.sin(current_time * 0.005)
            auto_text_color = (0, int(200 + 55 * pulse), 255)
        elif detected_display == "QBOARD" and qboard_hover:
            pulse = 0.5 + 0.5 * math.sin(current_time * 0.005)
            auto_text_color = (255, 0, int(150 * pulse))
        
        auto_text = small_font.render(f"Auto-detected: {detected_display}", True, auto_text_color)
        auto_rect = auto_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + button_y_pos + button_height + 30))
        screen.blit(auto_text, auto_rect)
        
        # Pulsing SANGSOM text effect
        pulse_factor = 0.5 + 0.5 * math.sin(current_time * 0.002)
        bright_yellow = (255, 255, 0)
        lite_yellow = (255, 255, 150)
        sangsom_color = tuple(int(bright_yellow[i] * (1 - pulse_factor) + lite_yellow[i] * pulse_factor) for i in range(3))
        
        collab_text1 = collab_font.render("In collaboration with ", True, WHITE)
        collab_text2 = collab_font.render("SANGSOM", True, sangsom_color)
        collab_text3 = collab_font.render(" Kindergarten", True, WHITE)
        
        collab_rect1 = collab_text1.get_rect()
        collab_rect1.right = WIDTH // 2 - collab_text2.get_width() // 2
        collab_rect1.centery = HEIGHT // 2 + int(350 * scale_factor)
        
        collab_rect2 = collab_text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + int(350 * scale_factor)))
        
        collab_rect3 = collab_text3.get_rect()
        collab_rect3.left = collab_rect2.right
        collab_rect3.centery = HEIGHT // 2 + int(350 * scale_factor)
        
        screen.blit(collab_text1, collab_rect1)
        screen.blit(collab_text2, collab_rect2)
        screen.blit(collab_text3, collab_rect3)
        
        # Add subtle floating to creator text
        creator_float = 2 * math.sin(current_time * 0.001)
        creator_text = small_font.render("Created by Teacher Evan and Teacher Lee", True, WHITE)
        creator_rect = creator_text.get_rect(center=(WIDTH // 2, HEIGHT - 40 + creator_float))
        screen.blit(creator_text, creator_rect)
        
        # Show FPS if in debug mode
        if DEBUG_MODE and SHOW_FPS:
            fps = int(clock.get_fps())
            fps_text = small_font.render(f"FPS: {fps}", True, (255, 255, 255))
            screen.blit(fps_text, (10, 10))
        
        pygame.display.flip()
        clock.tick(60)  # Cap at 60 FPS
    
    return DISPLAY_MODE 