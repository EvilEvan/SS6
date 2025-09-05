#!/usr/bin/env python3
"""
SS6 Performance Analysis Tool

Analyzes the performance characteristics of SS6 components
to identify optimization opportunities.
"""

import os
import sys
import time
import psutil
import gc
import pygame
import cProfile
import pstats
import io
from pathlib import Path

# Add repository root to Python path
_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Import core modules for analysis
try:
    from utils.particle_system import ParticleManager
    from utils.resource_manager import ResourceManager
    from utils.audio_manager import AudioManager
    from utils.sound_effects_manager import SoundEffectsManager
    from universal_class import (
        GlassShatterManager, MultiTouchManager, HUDManager,
        CheckpointManager, FlamethrowerManager, CenterPieceManager
    )
    from levels.colors_level import ColorsLevel
    from settings import *
    import Display_settings
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class PerformanceAnalyzer:
    """Analyzes performance characteristics of SS6 components."""
    
    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
        
    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function."""
        # Force garbage collection before measurement
        gc.collect()
        mem_before = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute function
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Measure memory after
        mem_after = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'result': result,
            'execution_time': end_time - start_time,
            'memory_before': mem_before,
            'memory_after': mem_after,
            'memory_delta': mem_after - mem_before
        }
    
    def profile_function(self, func, *args, **kwargs):
        """Profile a function with cProfile."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        
        # Get statistics
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s)
        stats.sort_stats('cumulative')
        stats.print_stats(20)
        
        return {
            'result': result,
            'profile_output': s.getvalue()
        }
    
    def test_particle_system_performance(self):
        """Test particle system performance at different scales."""
        print("=== Testing Particle System Performance ===")
        
        results = {}
        particle_counts = [50, 100, 200, 500, 1000]
        
        for count in particle_counts:
            print(f"Testing with {count} particles...")
            
            def create_particles():
                pm = ParticleManager(max_particles=count)
                pm.set_culling_distance(1920)
                
                # Create particles
                for i in range(count):
                    pm.create_particle(
                        x=i % 100, y=i % 100,
                        color=(255, 0, 0), size=5,
                        dx=1, dy=1, duration=60
                    )
                
                # Update particles for several frames
                for frame in range(60):
                    pm.update()
                
                return pm
            
            perf_data = self.measure_memory_usage(create_particles)
            results[count] = perf_data
            
            print(f"  Time: {perf_data['execution_time']:.3f}s")
            print(f"  Memory delta: {perf_data['memory_delta']:.2f}MB")
        
        self.results['particle_system'] = results
        return results
    
    def test_colors_level_initialization(self):
        """Test colors level initialization performance."""
        print("=== Testing Colors Level Initialization ===")
        
        # Initialize pygame without audio to avoid ALSA errors
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        pygame.init()
        pygame.mixer.quit()  # Disable audio
        
        try:
            # Create minimal test environment
            width, height = 800, 600
            screen = pygame.display.set_mode((width, height), pygame.HIDDEN)
            font = pygame.font.Font(None, 24)
            
            # Create required managers
            particle_manager = ParticleManager(max_particles=100)
            glass_shatter = GlassShatterManager(width, height, particle_manager)
            multi_touch = MultiTouchManager(width, height)
            hud_manager = HUDManager(width, height, font, None)
            
            def init_colors_level():
                # Create minimal colors level for testing
                level = ColorsLevel(
                    width=width, height=height, screen=screen, small_font=font,
                    particle_manager=particle_manager,
                    glass_shatter_manager=glass_shatter,
                    multi_touch_manager=multi_touch,
                    hud_manager=hud_manager,
                    mother_radius=50,
                    create_explosion_func=lambda *args: None,
                    checkpoint_screen_func=lambda *args: True,
                    game_over_screen_func=lambda *args: True,
                    explosions_list=[],
                    draw_explosion_func=lambda *args: None
                )
                
                # Initialize level state
                level.reset_level_state()
                
                # Test spatial grid creation (performance critical)
                level.dots = []
                for i in range(60):  # Current optimized dot count
                    level.dots.append({
                        'x': i * 10 % width,
                        'y': i * 10 % height,
                        'alive': True,
                        'color': (255, 0, 0)
                    })
                
                # Test grid operations
                for _ in range(100):  # Simulate game loop iterations
                    grid = level._create_spatial_grid()
                    neighbors = level._get_grid_neighbors(400, 300)
                
                return level
            
            perf_data = self.measure_memory_usage(init_colors_level)
            
            print(f"  Initialization time: {perf_data['execution_time']:.3f}s")
            print(f"  Memory delta: {perf_data['memory_delta']:.2f}MB")
            
            self.results['colors_level_init'] = perf_data
            return perf_data
            
        finally:
            pygame.quit()
    
    def test_surface_caching_performance(self):
        """Test surface caching performance impact."""
        print("=== Testing Surface Caching Performance ===")
        
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        pygame.init()
        pygame.mixer.quit()
        
        try:
            screen = pygame.display.set_mode((800, 600), pygame.HIDDEN)
            
            def test_with_cache():
                cache = {}
                surfaces_created = 0
                
                # Simulate repeated surface creation with caching
                for _ in range(1000):
                    color = (255, 0, 0)
                    radius = 20
                    key = (color, radius)
                    
                    if key not in cache:
                        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(surf, color, (radius, radius), radius)
                        cache[key] = surf
                        surfaces_created += 1
                
                return surfaces_created
            
            def test_without_cache():
                surfaces_created = 0
                
                # Simulate repeated surface creation without caching
                for _ in range(1000):
                    color = (255, 0, 0)
                    radius = 20
                    
                    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, color, (radius, radius), radius)
                    surfaces_created += 1
                
                return surfaces_created
            
            cached_perf = self.measure_memory_usage(test_with_cache)
            uncached_perf = self.measure_memory_usage(test_without_cache)
            
            print(f"  With cache - Time: {cached_perf['execution_time']:.3f}s, Memory: {cached_perf['memory_delta']:.2f}MB")
            print(f"  Without cache - Time: {uncached_perf['execution_time']:.3f}s, Memory: {uncached_perf['memory_delta']:.2f}MB")
            print(f"  Performance improvement: {uncached_perf['execution_time'] / cached_perf['execution_time']:.2f}x faster")
            
            self.results['surface_caching'] = {
                'cached': cached_perf,
                'uncached': uncached_perf,
                'improvement_factor': uncached_perf['execution_time'] / cached_perf['execution_time']
            }
            
        finally:
            pygame.quit()
    
    def test_audio_manager_performance(self):
        """Test audio manager performance and memory usage."""
        print("=== Testing Audio Manager Performance ===")
        
        def create_audio_managers():
            # Test different cache sizes
            small_cache = AudioManager(cache_limit=10, max_workers=1)
            large_cache = AudioManager(cache_limit=50, max_workers=2)
            
            # Test sound effects manager
            sfx_manager = SoundEffectsManager()
            
            # Simulate some operations
            for i in range(20):
                try:
                    # These will fail in headless environment but test initialization
                    small_cache.get_speech_rate()
                    large_cache.get_speech_rate()
                    sfx_manager.play_destruction_sound()
                except:
                    pass  # Expected in headless environment
            
            # Cleanup
            small_cache.cleanup()
            large_cache.cleanup()
            sfx_manager.cleanup()
            
            return True
        
        perf_data = self.measure_memory_usage(create_audio_managers)
        
        print(f"  Audio manager operations time: {perf_data['execution_time']:.3f}s")
        print(f"  Memory delta: {perf_data['memory_delta']:.2f}MB")
        
        self.results['audio_manager'] = perf_data
        return perf_data
    
    def analyze_import_performance(self):
        """Analyze import performance of major modules."""
        print("=== Testing Import Performance ===")
        
        import_tests = [
            ('pygame', 'import pygame'),
            ('settings', 'from settings import *'),
            ('universal_class', 'from universal_class import *'),
            ('utils.particle_system', 'from utils.particle_system import ParticleManager'),
            ('utils.audio_manager', 'from utils.audio_manager import AudioManager'),
            ('levels.colors_level', 'from levels.colors_level import ColorsLevel'),
        ]
        
        results = {}
        
        for module_name, import_statement in import_tests:
            start_time = time.time()
            try:
                exec(import_statement)
                end_time = time.time()
                results[module_name] = {
                    'success': True,
                    'time': end_time - start_time
                }
                print(f"  {module_name}: {results[module_name]['time']:.3f}s")
            except Exception as e:
                results[module_name] = {
                    'success': False,
                    'error': str(e),
                    'time': 0
                }
                print(f"  {module_name}: FAILED - {e}")
        
        self.results['imports'] = results
        return results
    
    def generate_report(self):
        """Generate comprehensive performance report."""
        print("\n" + "=" * 60)
        print("SS6 PERFORMANCE ANALYSIS REPORT")
        print("=" * 60)
        
        if 'particle_system' in self.results:
            print("\n🔥 PARTICLE SYSTEM PERFORMANCE:")
            for count, data in self.results['particle_system'].items():
                print(f"  {count} particles: {data['execution_time']:.3f}s, {data['memory_delta']:.2f}MB")
        
        if 'colors_level_init' in self.results:
            print("\n🎨 COLORS LEVEL INITIALIZATION:")
            data = self.results['colors_level_init']
            print(f"  Time: {data['execution_time']:.3f}s")
            print(f"  Memory usage: {data['memory_delta']:.2f}MB")
        
        if 'surface_caching' in self.results:
            print("\n💾 SURFACE CACHING IMPACT:")
            data = self.results['surface_caching']
            print(f"  Performance improvement: {data['improvement_factor']:.2f}x faster with caching")
        
        if 'audio_manager' in self.results:
            print("\n🔊 AUDIO MANAGER PERFORMANCE:")
            data = self.results['audio_manager']
            print(f"  Time: {data['execution_time']:.3f}s")
            print(f"  Memory usage: {data['memory_delta']:.2f}MB")
        
        if 'imports' in self.results:
            print("\n📦 IMPORT PERFORMANCE:")
            total_import_time = sum(r['time'] for r in self.results['imports'].values() if r['success'])
            print(f"  Total import time: {total_import_time:.3f}s")
            
            slowest_import = max(
                (name, data) for name, data in self.results['imports'].items() 
                if data['success']
            )[0]
            print(f"  Slowest import: {slowest_import}")
        
        print(f"\n💻 SYSTEM INFORMATION:")
        print(f"  CPU count: {psutil.cpu_count()}")
        print(f"  Memory total: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB")
        print(f"  Memory available: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.1f}GB")

def main():
    """Run performance analysis."""
    print("Starting SS6 Performance Analysis...")
    
    analyzer = PerformanceAnalyzer()
    
    try:
        # Run all performance tests
        analyzer.analyze_import_performance()
        analyzer.test_particle_system_performance()
        analyzer.test_surface_caching_performance()
        analyzer.test_audio_manager_performance()
        analyzer.test_colors_level_initialization()
        
        # Generate comprehensive report
        analyzer.generate_report()
        
        print("\n✅ Performance analysis completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Performance analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())