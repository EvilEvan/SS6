#!/usr/bin/env python3
"""
SS6 Audio System Optimization Test Suite

This script tests all the audio optimizations implemented:
1. SoundEffectsManager with 5 fart sound variants
2. Voice speed reduction (10% slower TTS)
3. Error handling and graceful degradation
4. Resource cleanup and memory management
"""

import sys
import os
import pygame
import time
import traceback

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.audio_manager import AudioManager
from utils.sound_effects_manager import SoundEffectsManager, get_sound_effects_manager
from utils.level_resource_manager import LevelResourceManager


class AudioTestSuite:
    """Comprehensive test suite for SS6 audio optimizations."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
        # Initialize pygame for audio testing
        pygame.init()
        pygame.mixer.init()
        
        print("=" * 70)
        print("SS6 AUDIO SYSTEM OPTIMIZATION TEST SUITE")
        print("=" * 70)
        print()
    
    def run_all_tests(self):
        """Run all audio system tests."""
        test_methods = [
            self.test_audio_manager_initialization,
            self.test_sound_effects_manager_creation,
            self.test_fart_sound_generation,
            self.test_fart_sound_variety,
            self.test_voice_speed_optimization,
            self.test_level_resource_manager_integration,
            self.test_error_handling,
            self.test_graceful_degradation,
            self.test_memory_management,
            self.test_cleanup_functionality
        ]
        
        for test_method in test_methods:
            try:
                print(f"Running {test_method.__name__}...")
                result = test_method()
                if result:
                    self.passed_tests.append(test_method.__name__)
                    print(f"✓ {test_method.__name__} PASSED")
                else:
                    self.failed_tests.append(test_method.__name__)
                    print(f"✗ {test_method.__name__} FAILED")
            except Exception as e:
                self.failed_tests.append(test_method.__name__)
                print(f"✗ {test_method.__name__} FAILED with exception: {e}")
                traceback.print_exc()
            print("-" * 50)
        
        self.print_summary()
    
    def test_audio_manager_initialization(self):
        """Test AudioManager initialization with optimizations."""
        try:
            audio_manager = AudioManager()
            
            # Test that speech rate is optimized (10% slower)
            expected_rate = int(150 * 0.9)  # 135
            if audio_manager.speech_rate != expected_rate:
                print(f"Expected speech rate {expected_rate}, got {audio_manager.speech_rate}")
                return False
            
            # Test initialization success
            if not audio_manager.mixer_initialized:
                print("AudioManager failed to initialize mixer")
                return False
            
            print(f"✓ Speech rate optimized: {audio_manager.speech_rate} (10% slower than {audio_manager.base_speech_rate})")
            
            # Cleanup
            audio_manager.cleanup()
            return True
            
        except Exception as e:
            print(f"AudioManager initialization failed: {e}")
            return False
    
    def test_sound_effects_manager_creation(self):
        """Test SoundEffectsManager creation and initialization."""
        try:
            sound_manager = SoundEffectsManager()
            
            # Test that it's enabled
            if not sound_manager.enabled:
                print("SoundEffectsManager should be enabled after successful initialization")
                return False
            
            # Test that fart sounds were generated
            if sound_manager.get_sound_count() == 0:
                print("No fart sounds were generated")
                return False
            
            print(f"✓ Generated {sound_manager.get_sound_count()} fart sound variants")
            
            # Cleanup
            sound_manager.cleanup()
            return True
            
        except Exception as e:
            print(f"SoundEffectsManager creation failed: {e}")
            return False
    
    def test_fart_sound_generation(self):
        """Test that 5 different fart sounds are generated."""
        try:
            sound_manager = SoundEffectsManager(max_sounds=5)
            
            # Check that exactly 5 sounds were generated
            if sound_manager.get_sound_count() != 5:
                print(f"Expected 5 fart sounds, got {sound_manager.get_sound_count()}")
                return False
            
            print(f"✓ Successfully generated 5 fart sound variants")
            
            # Test that sounds can be played (without actually playing)
            for i in range(5):
                if not sound_manager.fart_sounds[i]:
                    print(f"Fart sound {i} is None")
                    return False
            
            print("✓ All fart sounds are valid pygame.mixer.Sound objects")
            
            # Cleanup
            sound_manager.cleanup()
            return True
            
        except Exception as e:
            print(f"Fart sound generation test failed: {e}")
            return False
    
    def test_fart_sound_variety(self):
        """Test that fart sounds rotate through variants."""
        try:
            sound_manager = SoundEffectsManager(max_sounds=5)
            
            # Test round-robin rotation
            initial_rotation = sound_manager.sound_rotation
            
            # Simulate playing sounds
            for i in range(10):
                sound_manager.play_destruction_sound("test")
                expected_rotation = (initial_rotation + i + 1) % 5
                if sound_manager.sound_rotation != expected_rotation:
                    print(f"Round-robin not working correctly at iteration {i}")
                    return False
            
            print("✓ Round-robin sound rotation working correctly")
            
            # Cleanup
            sound_manager.cleanup()
            return True
            
        except Exception as e:
            print(f"Fart sound variety test failed: {e}")
            return False
    
    def test_voice_speed_optimization(self):
        """Test that voice speed is properly optimized."""
        try:
            audio_manager = AudioManager()
            
            # Test speech rate settings
            base_rate = audio_manager.base_speech_rate
            optimized_rate = audio_manager.speech_rate
            expected_rate = int(base_rate * 0.9)
            
            if optimized_rate != expected_rate:
                print(f"Speech rate not optimized correctly: expected {expected_rate}, got {optimized_rate}")
                return False
            
            print(f"✓ Speech rate optimized: {base_rate} → {optimized_rate} (10% reduction)")
            
            # Test dynamic rate adjustment
            audio_manager.set_speech_rate(200)
            if audio_manager.speech_rate != int(200 * 0.9):
                print("Dynamic speech rate adjustment not working")
                return False
            
            print("✓ Dynamic speech rate adjustment working")
            
            # Cleanup
            audio_manager.cleanup()
            return True
            
        except Exception as e:
            print(f"Voice speed optimization test failed: {e}")
            return False
    
    def test_level_resource_manager_integration(self):
        """Test LevelResourceManager integration with audio systems."""
        try:
            level_manager = LevelResourceManager("test_level", 800, 600)
            
            if not level_manager.initialize():
                print("LevelResourceManager failed to initialize")
                return False
            
            # Test that audio_manager is initialized
            if not level_manager.audio_manager:
                print("AudioManager not initialized in LevelResourceManager")
                return False
            
            # Test that sound_effects_manager is initialized
            if not level_manager.sound_effects_manager:
                print("SoundEffectsManager not initialized in LevelResourceManager")
                return False
            
            print("✓ LevelResourceManager properly integrates both audio systems")
            
            # Test methods exist and are callable
            if not hasattr(level_manager, 'play_destruction_sound'):
                print("play_destruction_sound method missing")
                return False
            
            if not hasattr(level_manager, 'play_target_sound'):
                print("play_target_sound method missing")
                return False
            
            print("✓ All required audio methods are available")
            
            # Cleanup
            level_manager.cleanup()
            return True
            
        except Exception as e:
            print(f"LevelResourceManager integration test failed: {e}")
            return False
    
    def test_error_handling(self):
        """Test error handling and recovery mechanisms."""
        try:
            # Test AudioManager error handling
            audio_manager = AudioManager()
            
            # Test graceful handling of invalid input
            result = audio_manager.play_pronunciation("")
            if result is None:
                print("play_pronunciation should return boolean, not None")
                return False
            
            # Test SoundEffectsManager error handling
            sound_manager = SoundEffectsManager()
            
            # Test graceful handling when disabled
            sound_manager.set_enabled(False)
            result = sound_manager.play_destruction_sound("test")
            if result is not False:
                print("Disabled SoundEffectsManager should return False")
                return False
            
            print("✓ Error handling mechanisms working correctly")
            
            # Cleanup
            audio_manager.cleanup()
            sound_manager.cleanup()
            return True
            
        except Exception as e:
            print(f"Error handling test failed: {e}")
            return False
    
    def test_graceful_degradation(self):
        """Test graceful degradation when audio systems fail."""
        try:
            level_manager = LevelResourceManager("test_level", 800, 600)
            level_manager.initialize()
            
            # Simulate audio manager failure
            level_manager.audio_manager = None
            
            # Should still return True (graceful degradation)
            result = level_manager.play_target_sound("test")
            if not result:
                print("play_target_sound should gracefully degrade when audio_manager is None")
                return False
            
            # Simulate sound effects manager failure
            level_manager.sound_effects_manager = None
            
            # Should still return True (graceful degradation)
            result = level_manager.play_destruction_sound("test")
            if not result:
                print("play_destruction_sound should gracefully degrade when sound_effects_manager is None")
                return False
            
            print("✓ Graceful degradation working correctly")
            
            # Cleanup
            level_manager.cleanup()
            return True
            
        except Exception as e:
            print(f"Graceful degradation test failed: {e}")
            return False
    
    def test_memory_management(self):
        """Test memory management and cache limits."""
        try:
            # Test AudioManager cache limits
            audio_manager = AudioManager(cache_limit=5)
            
            if audio_manager.cache_limit != 5:
                print("Cache limit not set correctly")
                return False
            
            # Test SoundEffectsManager sound limits
            sound_manager = SoundEffectsManager(max_sounds=3)
            
            if sound_manager.max_sounds != 3:
                print("Max sounds limit not set correctly")
                return False
            
            if sound_manager.get_sound_count() != 3:
                print(f"Expected 3 sounds, got {sound_manager.get_sound_count()}")
                return False
            
            print("✓ Memory management and limits working correctly")
            
            # Cleanup
            audio_manager.cleanup()
            sound_manager.cleanup()
            return True
            
        except Exception as e:
            print(f"Memory management test failed: {e}")
            return False
    
    def test_cleanup_functionality(self):
        """Test that cleanup functions work properly."""
        try:
            # Test AudioManager cleanup
            audio_manager = AudioManager()
            initial_cache_size = len(audio_manager.sound_cache)
            
            # Add something to cache (simulate usage)
            audio_manager.sound_cache["test"] = None
            
            # Cleanup should clear cache
            audio_manager.cleanup()
            
            if len(audio_manager.sound_cache) != 0:
                print("AudioManager cleanup did not clear cache")
                return False
            
            # Test SoundEffectsManager cleanup
            sound_manager = SoundEffectsManager()
            initial_sound_count = sound_manager.get_sound_count()
            
            # Cleanup should clear sounds
            sound_manager.cleanup()
            
            if sound_manager.get_sound_count() != 0:
                print("SoundEffectsManager cleanup did not clear sounds")
                return False
            
            print("✓ Cleanup functionality working correctly")
            return True
            
        except Exception as e:
            print(f"Cleanup functionality test failed: {e}")
            return False
    
    def print_summary(self):
        """Print test summary."""
        print()
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests: {len(self.passed_tests) + len(self.failed_tests)}")
        print(f"Passed: {len(self.passed_tests)}")
        print(f"Failed: {len(self.failed_tests)}")
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
        
        success_rate = len(self.passed_tests) / (len(self.passed_tests) + len(self.failed_tests)) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        if len(self.failed_tests) == 0:
            print("\n🎉 ALL TESTS PASSED! Audio optimizations are working correctly.")
        else:
            print(f"\n⚠️  {len(self.failed_tests)} test(s) failed. Please review the implementation.")
        
        print("=" * 70)


def main():
    """Run the audio test suite."""
    try:
        test_suite = AudioTestSuite()
        test_suite.run_all_tests()
        
        # Return appropriate exit code
        return 0 if len(test_suite.failed_tests) == 0 else 1
        
    except Exception as e:
        print(f"Test suite failed to run: {e}")
        traceback.print_exc()
        return 1
    finally:
        # Cleanup pygame
        try:
            pygame.quit()
        except:
            pass


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)