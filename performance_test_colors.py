#!/usr/bin/env python3
"""
Performance test for the colors level to measure optimization improvements.
"""

import pygame
import sys
import os
import time
import psutil
from typing import Dict, List

# Add the SS6 directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_headless_mode():
    """Setup headless mode for testing."""
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'

def measure_colors_level_performance() -> Dict:
    """
    Measure the performance of the colors level.
    
    Returns:
        Dict: Performance metrics
    """
    # Import after setting up headless mode
    from levels.colors_level import ColorsLevel
    from utils.particle_system import ParticleManager
    from universal_class import GlassShatterManager, HUDManager, MultiTouchManager
    from utils.level_resource_manager import LevelResourceManager
    
    pygame.init()
    
    # Create test environment
    width, height = 800, 600
    screen = pygame.Surface((width, height))
    small_font = pygame.font.Font(None, 24)
    
    # Create managers
    particle_manager = ParticleManager(max_particles=200)
    glass_shatter_manager = GlassShatterManager(width, height, particle_manager)
    multi_touch_manager = MultiTouchManager(width, height)  
    hud_manager = HUDManager(width, height, small_font, glass_shatter_manager)
    
    # Mock functions for testing
    def mock_explosion_func(*args, **kwargs):
        pass
        
    def mock_checkpoint_func(*args, **kwargs):
        return True
        
    def mock_game_over_func(*args, **kwargs):
        return False
    
    explosions_list = []
    
    def mock_draw_explosion_func(*args, **kwargs):
        pass
    
    # Create colors level instance
    colors_level = ColorsLevel(
        width=width,
        height=height,
        screen=screen,
        small_font=small_font,
        particle_manager=particle_manager,
        glass_shatter_manager=glass_shatter_manager,
        multi_touch_manager=multi_touch_manager,
        hud_manager=hud_manager,
        mother_radius=50,
        create_explosion_func=mock_explosion_func,
        checkpoint_screen_func=mock_checkpoint_func,
        game_over_screen_func=mock_game_over_func,
        explosions_list=explosions_list,
        draw_explosion_func=mock_draw_explosion_func
    )
    
    # Setup level state for testing
    colors_level.reset_level_state()
    colors_level.color_idx = 0
    colors_level.mother_color = colors_level.COLORS_LIST[0]
    colors_level.mother_color_name = colors_level.color_names[0]
    
    # Create test dots
    colors_level.dots = []
    for i in range(60):  # Full dot count
        colors_level.dots.append({
            "x": 100 + (i % 8) * 90,
            "y": 100 + (i // 8) * 80,
            "dx": 0,
            "dy": 0,
            "color": colors_level.COLORS_LIST[i % len(colors_level.COLORS_LIST)],
            "radius": 25,
            "target": i < 12,  # First 12 are targets
            "alive": True
        })
    colors_level.dots_active = True
    colors_level.collision_enabled = True
    
    # Background stars for testing
    stars = []
    for _ in range(100):
        stars.append([100, 100, 3])
    
    # Performance measurement
    process = psutil.Process()
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    frame_times = []
    update_times = []
    draw_times = []
    collision_times = []
    
    print("Starting colors level performance test...")
    print(f"Testing with {len(colors_level.dots)} dots")
    
    # Test frames
    test_frames = 100
    for frame in range(test_frames):
        frame_start = time.perf_counter()
        
        # Measure update time
        update_start = time.perf_counter()
        colors_level._update_dots()
        update_time = time.perf_counter() - update_start
        update_times.append(update_time * 1000)  # Convert to ms
        
        # Measure collision detection time
        collision_start = time.perf_counter()
        colors_level._handle_dot_collisions()
        collision_time = time.perf_counter() - collision_start
        collision_times.append(collision_time * 1000)  # Convert to ms
        
        # Measure draw time
        draw_start = time.perf_counter()
        colors_level._draw_frame(stars)
        draw_time = time.perf_counter() - draw_start
        draw_times.append(draw_time * 1000)  # Convert to ms
        
        frame_time = time.perf_counter() - frame_start
        frame_times.append(frame_time * 1000)  # Convert to ms
        
        # Update frame counter for shimmer effects
        colors_level.frame_counter += 1
        
        if frame % 20 == 0:
            print(f"Frame {frame}/{test_frames} - {frame_time*1000:.2f}ms")
    
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    
    # Calculate statistics
    def calc_stats(times: List[float]) -> Dict:
        if not times:
            return {"avg": 0, "min": 0, "max": 0, "p95": 0}
        times_sorted = sorted(times)
        return {
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "p95": times_sorted[int(len(times) * 0.95)]
        }
    
    results = {
        "total_frames": test_frames,
        "frame_stats": calc_stats(frame_times),
        "update_stats": calc_stats(update_times),
        "collision_stats": calc_stats(collision_times),
        "draw_stats": calc_stats(draw_times),
        "memory_usage": {
            "before_mb": memory_before,
            "after_mb": memory_after,
            "increase_mb": memory_after - memory_before
        },
        "surface_cache_size": len(colors_level.surface_cache),
        "dots_count": len(colors_level.dots),
        "target_fps": 50,
        "achieved_fps": 1000 / (sum(frame_times) / len(frame_times)) if frame_times else 0
    }
    
    # Cleanup
    colors_level._cleanup_level()
    pygame.quit()
    
    return results

def print_performance_results(results: Dict):
    """Print formatted performance results."""
    print("\n" + "="*60)
    print("COLORS LEVEL PERFORMANCE RESULTS")
    print("="*60)
    
    print(f"Total frames tested: {results['total_frames']}")
    print(f"Target FPS: {results['target_fps']}")
    print(f"Achieved FPS: {results['achieved_fps']:.1f}")
    print(f"Dots count: {results['dots_count']}")
    print(f"Surface cache size: {results['surface_cache_size']}")
    
    print(f"\nMemory Usage:")
    print(f"  Before: {results['memory_usage']['before_mb']:.1f} MB")
    print(f"  After: {results['memory_usage']['after_mb']:.1f} MB")
    print(f"  Increase: {results['memory_usage']['increase_mb']:.1f} MB")
    
    print(f"\nTiming Breakdown (milliseconds):")
    for section, stats in [
        ("Frame Total", results['frame_stats']),
        ("Update", results['update_stats']),
        ("Collision", results['collision_stats']),
        ("Draw", results['draw_stats'])
    ]:
        print(f"  {section}:")
        print(f"    Average: {stats['avg']:.2f}ms")
        print(f"    Min: {stats['min']:.2f}ms")
        print(f"    Max: {stats['max']:.2f}ms")
        print(f"    95th percentile: {stats['p95']:.2f}ms")
    
    # Performance warnings
    print(f"\nPerformance Analysis:")
    if results['achieved_fps'] < results['target_fps']:
        print(f"  ⚠️  FPS below target ({results['achieved_fps']:.1f} < {results['target_fps']})")
    else:
        print(f"  ✅ FPS meets target ({results['achieved_fps']:.1f} >= {results['target_fps']})")
    
    if results['frame_stats']['avg'] > 20:  # 20ms = 50fps
        print(f"  ⚠️  Frame time high ({results['frame_stats']['avg']:.2f}ms)")
    else:
        print(f"  ✅ Frame time acceptable ({results['frame_stats']['avg']:.2f}ms)")
    
    if results['draw_stats']['avg'] > 15:  # Drawing should be < 15ms
        print(f"  ⚠️  Draw time high ({results['draw_stats']['avg']:.2f}ms)")
    else:
        print(f"  ✅ Draw time acceptable ({results['draw_stats']['avg']:.2f}ms)")

def main():
    """Run the performance test."""
    print("SS6 Colors Level Performance Test")
    print("=================================")
    
    setup_headless_mode()
    
    try:
        results = measure_colors_level_performance()
        print_performance_results(results)
        
        # Return appropriate exit code
        if results['achieved_fps'] >= results['target_fps']:
            print("\n🎉 Performance test PASSED!")
            return 0
        else:
            print("\n❌ Performance test FAILED!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Performance test ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())