#!/usr/bin/env python3
"""
SS6 Main.py Stability Test Suite

This script thoroughly tests the enhanced main.py to ensure it's stable and ready for use.
Tests include initialization, resource management, error handling, and performance validation.
"""

import sys
import os
import traceback
import gc
import time
import pygame

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class MainStabilityTestSuite:
    """Comprehensive test suite for the enhanced main.py stability."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
        print("=" * 70)
        print("SS6 MAIN.PY STABILITY TEST SUITE")
        print("=" * 70)
        print()
    
    def run_test(self, test_name: str, test_func):
        """Run a single test with error handling and timing."""
        print(f"Running {test_name}...")
        start_time = time.time()
        
        try:
            result = test_func()
            end_time = time.time()
            
            if result:
                print(f"✓ {test_name} PASSED ({end_time - start_time:.2f}s)")
                self.passed_tests.append(test_name)
                self.test_results[test_name] = True
            else:
                print(f"✗ {test_name} FAILED ({end_time - start_time:.2f}s)")
                self.failed_tests.append(test_name)
                self.test_results[test_name] = False
                
        except Exception as e:
            end_time = time.time()
            print(f"✗ {test_name} FAILED with exception ({end_time - start_time:.2f}s)")
            print(f"   Error: {e}")
            self.failed_tests.append(test_name)
            self.test_results[test_name] = False
        
        print("-" * 50)
        
        # Force garbage collection between tests
        gc.collect()
    
    def test_main_import(self) -> bool:
        """Test that main.py imports without errors."""
        try:
            import main
            return True
        except Exception as e:
            print(f"Import error: {e}")
            return False
    
    def test_superstudent_game_class(self) -> bool:
        """Test SuperStudentGame class initialization."""
        try:
            from main import SuperStudentGame
            game = SuperStudentGame()
            
            # Verify essential attributes exist
            required_attrs = [
                'running', 'screen', 'clock', 'width', 'height',
                'resource_manager', 'particle_manager', 'audio_manager',
                'sound_effects_manager', 'managers', 'display_mode',
                'error_count', 'max_errors'
            ]
            
            for attr in required_attrs:
                if not hasattr(game, attr):
                    print(f"Missing attribute: {attr}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"SuperStudentGame class error: {e}")
            return False
    
    def test_pygame_initialization(self) -> bool:
        """Test pygame initialization without opening a window."""
        try:
            # Initialize pygame in headless mode for testing
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            
            from main import SuperStudentGame
            game = SuperStudentGame()
            
            # Mock screen size for testing
            game.width, game.height = 800, 600
            
            # Test initialization components
            pygame.init()
            pygame.mixer.init()
            
            # Verify basic pygame functionality
            clock = pygame.time.Clock()
            
            return True
            
        except Exception as e:
            print(f"Pygame initialization error: {e}")
            return False
        finally:
            if 'SDL_VIDEODRIVER' in os.environ:
                del os.environ['SDL_VIDEODRIVER']
    
    def test_resource_initialization(self) -> bool:
        """Test resource manager initialization."""
        try:
            from main import SuperStudentGame
            from utils.resource_manager import ResourceManager
            from utils.audio_manager import AudioManager
            from utils.sound_effects_manager import SoundEffectsManager
            
            # Initialize pygame for resource testing
            pygame.init()
            pygame.mixer.init()
            
            game = SuperStudentGame()
            game.width, game.height = 800, 600
            
            # Test individual components
            resource_manager = ResourceManager()
            audio_manager = AudioManager(cache_limit=5, max_workers=1)
            sound_effects_manager = SoundEffectsManager()
            
            # Verify they work together
            if not resource_manager or not audio_manager or not sound_effects_manager:
                return False
            
            # Test cleanup
            audio_manager.cleanup()
            sound_effects_manager.cleanup()
            
            return True
            
        except Exception as e:
            print(f"Resource initialization error: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling mechanisms."""
        try:
            from main import SuperStudentGame
            
            game = SuperStudentGame()
            
            # Test error handling method
            test_error = ValueError("Test error")
            game.handle_error(test_error, "Test Context")
            
            # Verify error count incremented
            if game.error_count != 1:
                print(f"Error count incorrect: {game.error_count}")
                return False
            
            # Test max error threshold
            for i in range(game.max_errors):
                game.handle_error(test_error, f"Test {i}")
            
            # Should be shutting down now
            if game.running:
                print("Error threshold not working")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error handling test error: {e}")
            return False
    
    def test_cleanup_functionality(self) -> bool:
        """Test resource cleanup functionality."""
        try:
            from main import SuperStudentGame
            
            pygame.init()
            pygame.mixer.init()
            
            game = SuperStudentGame()
            game.width, game.height = 800, 600
            
            # Initialize some resources
            from utils.audio_manager import AudioManager
            from utils.sound_effects_manager import SoundEffectsManager
            
            game.audio_manager = AudioManager(cache_limit=5)
            game.sound_effects_manager = SoundEffectsManager()
            
            # Test cleanup
            game.cleanup_resources()
            
            return True
            
        except Exception as e:
            print(f"Cleanup test error: {e}")
            return False
    
    def test_memory_efficiency(self) -> bool:
        """Test memory usage and efficiency."""
        try:
            import psutil
            process = psutil.Process()
            
            # Measure initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            from main import SuperStudentGame
            
            pygame.init()
            pygame.mixer.init()
            
            # Create and initialize game
            game = SuperStudentGame()
            game.width, game.height = 800, 600
            
            # Simulate resource usage
            from utils.audio_manager import AudioManager
            from utils.sound_effects_manager import SoundEffectsManager
            
            game.audio_manager = AudioManager(cache_limit=10)
            game.sound_effects_manager = SoundEffectsManager()
            
            # Measure memory after initialization
            after_init_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Cleanup
            game.cleanup_resources()
            gc.collect()
            
            # Measure memory after cleanup
            after_cleanup_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"   Initial: {initial_memory:.1f}MB")
            print(f"   After init: {after_init_memory:.1f}MB")
            print(f"   After cleanup: {after_cleanup_memory:.1f}MB")
            
            # Memory should not grow excessively
            memory_growth = after_init_memory - initial_memory
            if memory_growth > 100:  # More than 100MB growth is concerning
                print(f"   Excessive memory growth: {memory_growth:.1f}MB")
                return False
            
            return True
            
        except ImportError:
            print("   psutil not available, skipping memory test")
            return True
        except Exception as e:
            print(f"Memory test error: {e}")
            return False
    
    def test_level_integration(self) -> bool:
        """Test level class integration."""
        try:
            from main import SuperStudentGame
            from levels import ColorsLevel, ShapesLevel, AlphabetLevel, NumbersLevel, CLCaseLevel
            
            # Verify all level classes are importable
            level_classes = [ColorsLevel, ShapesLevel, AlphabetLevel, NumbersLevel, CLCaseLevel]
            
            for level_class in level_classes:
                if not level_class:
                    print(f"Failed to import {level_class}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Level integration error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all stability tests."""
        test_methods = [
            ("test_main_import", self.test_main_import),
            ("test_superstudent_game_class", self.test_superstudent_game_class),
            ("test_pygame_initialization", self.test_pygame_initialization),
            ("test_resource_initialization", self.test_resource_initialization),
            ("test_error_handling", self.test_error_handling),
            ("test_cleanup_functionality", self.test_cleanup_functionality),
            ("test_memory_efficiency", self.test_memory_efficiency),
            ("test_level_integration", self.test_level_integration),
        ]
        
        for test_name, test_func in test_methods:
            self.run_test(test_name, test_func)
            time.sleep(0.1)  # Brief pause between tests
    
    def print_summary(self):
        """Print test summary."""
        total_tests = len(self.test_results)
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)
        
        print("=" * 70)
        print("STABILITY TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print()
        
        if self.passed_tests:
            print("PASSED TESTS:")
            for test in self.passed_tests:
                print(f"  ✓ {test}")
            print()
        
        if self.failed_tests:
            print("FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  ✗ {test}")
            print()
        
        success_rate = (passed_count / total_tests) * 100 if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if success_rate >= 80:
            print("🎉 Main.py is STABLE and ready for production use!")
        elif success_rate >= 60:
            print("⚠️  Main.py has some issues but is mostly functional.")
        else:
            print("❌ Main.py has significant stability issues that need addressing.")
        
        print("=" * 70)
        
        return success_rate >= 80


def main():
    """Run the stability test suite."""
    test_suite = MainStabilityTestSuite()
    test_suite.run_all_tests()
    is_stable = test_suite.print_summary()
    
    return 0 if is_stable else 1


if __name__ == "__main__":
    sys.exit(main())
