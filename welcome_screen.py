import pygame
import random
import math
from settings import WHITE, BLACK, FLAME_COLORS
from Display_settings import (
    DISPLAY_MODES, DEFAULT_MODE, DISPLAY_SETTINGS_PATH,
    DEBUG_MODE, SHOW_FPS, detect_display_type, load_display_mode, 
    save_display_mode, draw_neon_button, DisplayModeSelector
)

def level_menu(WIDTH, HEIGHT, screen, small_font):
    """Display the Level Options screen to choose the mission using a cyberpunk neon display."""
    running = True
    clock = pygame.time.Clock()
    
    # Load display mode to adjust particle count
    display_mode = load_display_mode()
    
    # Adjust particle count based on display mode for performance
    particle_count = 200 if display_mode == "QBOARD" else 400  # Reduced from 700
    
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

    # Create OUTWARD moving particles (optimized count)
    repel_particles = []
    for _ in range(particle_count):
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

    # Pre-render static text surfaces for better performance
    title_surface = small_font.render("Choose Mission:", True, WHITE)
    abc_surface = small_font.render("A B C", True, WHITE)
    num_surface = small_font.render("1 2 3", True, WHITE)
    shapes_surface = small_font.render("Shapes", True, WHITE)
    clcase_surface = small_font.render("C/L Case", True, WHITE)
    colors_surface = small_font.render("Colors", True, WHITE)

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

        # Draw the outward moving particles (optimized)
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

        # Draw title (re-render only when color changes significantly)
        if color_transition < 0.02 or color_transition > 0.98:  # Only re-render at color transitions
            title_surface = small_font.render("Choose Mission:", True, title_color)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
        screen.blit(title_surface, title_rect)

        # Draw the A B C button with a neon cyberpunk look
        draw_neon_button(screen, abc_rect, (255, 0, 150))
        abc_text_rect = abc_surface.get_rect(center=abc_rect.center)
        screen.blit(abc_surface, abc_text_rect)

        # Draw the 1 2 3 button with a neon cyberpunk look
        draw_neon_button(screen, num_rect, (0, 200, 255))
        num_text_rect = num_surface.get_rect(center=num_rect.center)
        screen.blit(num_surface, num_text_rect)

        # Draw the Shapes button with a neon cyberpunk look
        draw_neon_button(screen, shapes_rect, (0, 255, 0))
        shapes_text_rect = shapes_surface.get_rect(center=shapes_rect.center)
        screen.blit(shapes_surface, shapes_text_rect)

        # Draw the new C/L Case Letters button
        draw_neon_button(screen, clcase_rect, (255, 255, 0))
        clcase_text_rect = clcase_surface.get_rect(center=clcase_rect.center)
        screen.blit(clcase_surface, clcase_text_rect)

        # Draw the new Colors button with a neon rainbow look
        draw_neon_button(screen, colors_rect, (128, 0, 255))
        colors_text_rect = colors_surface.get_rect(center=colors_rect.center)
        screen.blit(colors_surface, colors_text_rect)

        pygame.display.flip()
        # Reduce frame rate for QBoard to improve performance
        target_fps = 45 if display_mode == "QBOARD" else 60
        clock.tick(target_fps)

def welcome_screen(WIDTH, HEIGHT, screen, small_font, init_resources_callback):
    """Show the welcome screen with display size options."""
    # Initialize with default mode first
    DISPLAY_MODE = DEFAULT_MODE

    # Load display mode from settings or auto-detect
    DISPLAY_MODE = load_display_mode()
    
    # Create display mode selector
    display_selector = DisplayModeSelector(WIDTH, HEIGHT, screen, small_font, FLAME_COLORS)
    
    # --- Main welcome screen loop with animations ---
    running = True
    clock = pygame.time.Clock()
    last_time = pygame.time.get_ticks()
    
    # Adjust frame rate based on display mode for performance
    target_fps = 45 if DISPLAY_MODE == "QBOARD" else 60
    
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
                selected_mode = display_selector.handle_click(mx, my)
                if selected_mode:
                    DISPLAY_MODE = selected_mode
                    save_display_mode(DISPLAY_MODE)
                    init_resources_callback()
                    running = False
        
        # Get mouse position for hover effects
        mx, my = pygame.mouse.get_pos()
        default_hover, qboard_hover = display_selector.get_hover_states(mx, my)
        
        # Update animations
        display_selector.update_color_transition(delta_time)
        display_selector.update_title_float(delta_time)
        display_selector.update_particles(delta_time)
        
        # Get current title color
        title_color = display_selector.get_title_color()
        
        # Draw everything
        screen.fill(BLACK)
        
        # Draw all visual elements using the display selector
        display_selector.draw_particles()
        display_selector.draw_title(title_color)
        display_selector.draw_instructions()
        display_selector.draw_buttons(default_hover, qboard_hover)
        display_selector.draw_auto_detected_indicator(current_time, default_hover, qboard_hover)
        display_selector.draw_collaboration_text(current_time)
        display_selector.draw_creator_text(current_time)
        display_selector.draw_fps(clock)
        
        pygame.display.flip()
        clock.tick(target_fps)  # Use adaptive frame rate
    
    return DISPLAY_MODE 