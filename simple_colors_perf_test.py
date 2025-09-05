#!/usr/bin/env python3
"""
Simplified performance test for colors level rendering bottlenecks.
"""

import pygame
import sys
import os
import time
import math
import random
from typing import Dict, List

# Add the SS6 directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_headless_mode():
    """Setup headless mode for testing."""
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'

def test_colors_rendering_performance():
    """Test the rendering performance of dots with current implementation."""
    
    # Setup
    setup_headless_mode()
    pygame.init()
    
    width, height = 800, 600
    screen = pygame.Surface((width, height))
    
    # Create test dots (same as colors level)
    COLORS_LIST = [
        (0, 0, 255),    # Blue
        (255, 0, 0),    # Red
        (0, 200, 0),    # Green
        (255, 255, 0),  # Yellow
        (128, 0, 255),  # Purple
    ]
    
    dots = []
    for i in range(60):  # Full dot count from colors level
        dots.append({
            "x": 100 + (i % 8) * 90,
            "y": 100 + (i // 8) * 80,
            "dx": random.uniform(-6, 6),
            "dy": random.uniform(-6, 6),
            "color": COLORS_LIST[i % len(COLORS_LIST)],
            "radius": 25,
            "target": i < 12,  # First 12 are targets like in actual game
            "alive": True
        })
    
    # Surface cache for testing
    surface_cache = {}
    shimmer_seeds = {}
    frame_counter = 0
    
    def _calculate_dot_shading(base_color, radius, is_target=False):
        """Calculate depth shading for dots with gradient effect."""
        center_color = tuple(min(255, int(c * 1.3)) for c in base_color)
        edge_color = tuple(max(0, int(c * 0.7)) for c in base_color)
        
        if is_target:
            glow_intensity = 0.2 + 0.1 * math.sin(frame_counter * 0.1)
            center_color = tuple(min(255, int(c * (1.0 + glow_intensity))) for c in center_color)
            
        return center_color, edge_color
    
    def _get_shimmer_effect(dot_id):
        """Get shimmer effect values for a specific dot."""
        if dot_id not in shimmer_seeds:
            shimmer_seeds[dot_id] = random.random() * 6.28
            
        seed = shimmer_seeds[dot_id]
        shimmer = math.sin(frame_counter * 0.05 + seed) * 0.1 + 1.0
        alpha_shimmer = math.sin(frame_counter * 0.08 + seed) * 15 + 240
        
        return shimmer, max(200, min(255, int(alpha_shimmer)))
    
    def _get_circle_surface(color, radius):
        """Return cached filled-circle surface for given color & radius."""
        key = (color, radius)
        surf = surface_cache.get(key)
        
        if surf is None:
            if len(surface_cache) >= 50:  # Cache limit
                # Simple eviction - remove 25% oldest
                keys_to_remove = list(surface_cache.keys())[:len(surface_cache)//4]
                for old_key in keys_to_remove:
                    surface_cache.pop(old_key, None)
            
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (radius, radius), radius)
            surface_cache[key] = surf
                
        return surf
    
    def draw_current_implementation(dots_to_draw):
        """Draw dots using the current (complex) implementation."""
        screen.fill((0, 0, 0))  # Black background
        
        for dot in dots_to_draw:
            if not dot["alive"]:
                continue
                
            dot_id = id(dot)
            
            # Apply shimmer effects to target dots only
            if dot["target"]:
                shimmer_scale, shimmer_alpha = _get_shimmer_effect(dot_id)
            else:
                shimmer_scale, shimmer_alpha = 1.0, 255
            
            # Calculate shaded colors
            center_color, edge_color = _calculate_dot_shading(dot["color"], dot["radius"], dot["target"])
            
            # Apply shimmer to radius
            shimmer_radius = int(dot["radius"] * shimmer_scale)
            
            draw_x = int(dot["x"])
            draw_y = int(dot["y"])
            
            # Draw depth gradient (3 circles for smooth gradient)
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
                        dot_surface = _get_circle_surface(blended_color, gradient_radius).copy()
                        dot_surface.set_alpha(shimmer_alpha)
                        screen.blit(dot_surface, (draw_x - gradient_radius, draw_y - gradient_radius))
                    else:
                        pygame.draw.circle(screen, blended_color, (draw_x, draw_y), gradient_radius)
                                         
            # Add extra glow for target dots
            if dot["target"]:
                glow_radius = shimmer_radius + 8
                glow_intensity = int(50 + 30 * math.sin(frame_counter * 0.15))
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*dot["color"], glow_intensity), 
                                 (glow_radius, glow_radius), glow_radius)
                screen.blit(glow_surface, (draw_x - glow_radius, draw_y - glow_radius))
    
    def draw_optimized_implementation(dots_to_draw):
        """Draw dots using an optimized implementation."""
        screen.fill((0, 0, 0))  # Black background
        
        for dot in dots_to_draw:
            if not dot["alive"]:
                continue
                
            draw_x = int(dot["x"])
            draw_y = int(dot["y"])
            
            if dot["target"]:
                # Simple glow for target dots
                glow_intensity = int(40 + 20 * math.sin(frame_counter * 0.1))
                glow_color = (*dot["color"], glow_intensity)
                glow_surface = pygame.Surface((dot["radius"] * 3, dot["radius"] * 3), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, glow_color, 
                                 (dot["radius"] * 3 // 2, dot["radius"] * 3 // 2), 
                                 dot["radius"] + 5)
                screen.blit(glow_surface, (draw_x - dot["radius"] - 5, draw_y - dot["radius"] - 5))
            
            # Simple 2-layer gradient
            # Outer darker circle
            edge_color = tuple(max(0, int(c * 0.7)) for c in dot["color"])
            pygame.draw.circle(screen, edge_color, (draw_x, draw_y), dot["radius"])
            
            # Inner lighter circle
            center_color = tuple(min(255, int(c * 1.2)) for c in dot["color"])
            pygame.draw.circle(screen, center_color, (draw_x, draw_y), dot["radius"] - 3)
    
    # Performance testing
    test_frames = 100
    print(f"Testing rendering performance with {len(dots)} dots over {test_frames} frames...")
    
    # Test current implementation
    print("\nTesting CURRENT implementation...")
    current_times = []
    for frame in range(test_frames):
        frame_counter = frame
        start_time = time.perf_counter()
        draw_current_implementation(dots)
        end_time = time.perf_counter()
        current_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        if frame % 20 == 0:
            print(f"  Frame {frame}: {current_times[-1]:.2f}ms")
    
    # Reset for optimized test
    surface_cache.clear()
    shimmer_seeds.clear()
    
    # Test optimized implementation
    print("\nTesting OPTIMIZED implementation...")
    optimized_times = []
    for frame in range(test_frames):
        frame_counter = frame
        start_time = time.perf_counter()
        draw_optimized_implementation(dots)
        end_time = time.perf_counter()
        optimized_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        if frame % 20 == 0:
            print(f"  Frame {frame}: {optimized_times[-1]:.2f}ms")
    
    # Calculate results
    current_avg = sum(current_times) / len(current_times)
    current_fps = 1000 / current_avg
    
    optimized_avg = sum(optimized_times) / len(optimized_times)
    optimized_fps = 1000 / optimized_avg
    
    improvement = ((current_avg - optimized_avg) / current_avg) * 100
    fps_improvement = ((optimized_fps - current_fps) / current_fps) * 100
    
    print(f"\n" + "="*60)
    print("RENDERING PERFORMANCE COMPARISON")
    print("="*60)
    print(f"Current Implementation:")
    print(f"  Average frame time: {current_avg:.2f}ms")
    print(f"  Estimated FPS: {current_fps:.1f}")
    print(f"  Max frame time: {max(current_times):.2f}ms")
    print(f"  Min frame time: {min(current_times):.2f}ms")
    
    print(f"\nOptimized Implementation:")
    print(f"  Average frame time: {optimized_avg:.2f}ms")
    print(f"  Estimated FPS: {optimized_fps:.1f}")
    print(f"  Max frame time: {max(optimized_times):.2f}ms")
    print(f"  Min frame time: {min(optimized_times):.2f}ms")
    
    print(f"\nPerformance Improvement:")
    print(f"  Frame time reduction: {improvement:.1f}%")
    print(f"  FPS improvement: {fps_improvement:.1f}%")
    print(f"  Surface cache size: {len(surface_cache)}")
    
    # Performance analysis
    target_fps = 50
    target_frame_time = 1000 / target_fps  # 20ms
    
    print(f"\nPerformance Analysis (Target: {target_fps} FPS / {target_frame_time:.1f}ms):")
    if current_fps < target_fps:
        print(f"  ❌ Current implementation FAILS target ({current_fps:.1f} < {target_fps})")
    else:
        print(f"  ✅ Current implementation meets target ({current_fps:.1f} >= {target_fps})")
        
    if optimized_fps < target_fps:
        print(f"  ❌ Optimized implementation FAILS target ({optimized_fps:.1f} < {target_fps})")
    else:
        print(f"  ✅ Optimized implementation meets target ({optimized_fps:.1f} >= {target_fps})")
    
    pygame.quit()
    
    return {
        'current_fps': current_fps,
        'optimized_fps': optimized_fps,
        'improvement_percent': improvement,
        'meets_target': optimized_fps >= target_fps
    }

if __name__ == "__main__":
    try:
        results = test_colors_rendering_performance()
        
        if results['meets_target']:
            print("\n🎉 Performance optimization SUCCESSFUL!")
            sys.exit(0)
        else:
            print("\n⚠️  Performance still needs improvement")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)