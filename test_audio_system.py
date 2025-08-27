#!/usr/bin/env python3
"""
Test script for SS6 Audio and Resource Management System
Tests the new audio pronunciation and level isolation features.
"""

import sys
import os
import pygame

# Add the SS6 directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our new classes
from utils.audio_manager import AudioManager
from utils.level_resource_manager import LevelResourceManager


def test_audio_system():
    """Test the audio system functionality."""
    print("=== Testing Audio System ===")
    
    # Initialize pygame
    pygame.init()
    
    try:
        # Test AudioManager initialization
        audio_manager = AudioManager(cache_limit=10)
        print(f"✓ AudioManager initialized: {audio_manager.get_stats()}")
        
        # Test alphabet pronunciation
        alphabet_words = ['a', 'b', 'c', 'd', 'e']
        print("Testing alphabet pronunciation...")
        for letter in alphabet_words[:3]:  # Test first 3 letters
            success = audio_manager.play_pronunciation(letter)
            print(f"  Letter '{letter}': {'✓' if success else '✗'}")
        
        # Test number pronunciation
        number_words = ['one', 'two', 'three']
        print("Testing number pronunciation...")
        for number in number_words:
            success = audio_manager.play_pronunciation(number)
            print(f"  Number '{number}': {'✓' if success else '✗'}")
        
        # Test color pronunciation
        color_words = ['red', 'blue', 'green']
        print("Testing color pronunciation...")
        for color in color_words:
            success = audio_manager.play_pronunciation(color)
            print(f"  Color '{color}': {'✓' if success else '✗'}")
        
        # Test preloading
        preloaded = audio_manager.preload_sounds(['hello', 'world', 'test'])
        print(f"✓ Preloaded {preloaded}/3 sounds")
        
        # Test cache stats
        final_stats = audio_manager.get_stats()
        print(f"✓ Final stats: {final_stats}")
        
        # Cleanup
        audio_manager.cleanup()
        print("✓ AudioManager cleanup completed")
        
    except Exception as e:
        print(f"✗ Audio system test failed: {e}")
        return False
    
    return True


def test_level_resource_manager():
    """Test the level resource management system."""
    print("\n=== Testing Level Resource Manager ===")
    
    try:
        # Test LevelResourceManager initialization
        level_manager = LevelResourceManager("test_level", 800, 600)
        success = level_manager.initialize()
        print(f"✓ LevelResourceManager initialized: {success}")
        
        # Test explosion creation
        for i in range(5):
            level_manager.create_explosion(100 + i * 50, 100, max_radius=50)
        print("✓ Created 5 test explosions")
        
        # Test particle creation
        for i in range(10):
            level_manager.create_particle(200 + i * 10, 200, (255, 0, 0), 5, 0.5, 0.5, 30)
        print("✓ Created 10 test particles")
        
        # Test sound playing
        test_sounds = ['test', 'sound', 'system']
        for sound in test_sounds:
            level_manager.play_target_sound(sound)
        print("✓ Played 3 test sounds")
        
        # Test resource stats
        stats = level_manager.get_resource_stats()
        print(f"✓ Resource stats: {stats}")
        
        # Test cleanup
        level_manager.cleanup()
        cleanup_stats = level_manager.get_resource_stats()
        print(f"✓ Cleanup completed. Final stats: {cleanup_stats}")
        
    except Exception as e:
        print(f"✗ Level resource manager test failed: {e}")
        return False
    
    return True


def test_resource_isolation():
    """Test that multiple level managers don't interfere with each other."""
    print("\n=== Testing Resource Isolation ===")
    
    try:
        # Create multiple level managers
        level1 = LevelResourceManager("alphabet", 800, 600)
        level2 = LevelResourceManager("numbers", 800, 600)
        level3 = LevelResourceManager("colors", 800, 600)
        
        # Initialize all
        level1.initialize()
        level2.initialize()
        level3.initialize()
        print("✓ Initialized 3 separate level managers")
        
        # Add different effects to each
        level1.create_explosion(100, 100)
        level1.play_target_sound('a')
        
        level2.create_explosion(200, 200)
        level2.play_target_sound('one')
        
        level3.create_explosion(300, 300)
        level3.play_target_sound('red')
        
        print("✓ Created separate effects in each level")
        
        # Check isolation
        stats1 = level1.get_resource_stats()
        stats2 = level2.get_resource_stats()
        stats3 = level3.get_resource_stats()
        
        print(f"Level1 stats: explosions={stats1['active_explosions']}, sounds={stats1['cached_sounds']}")
        print(f"Level2 stats: explosions={stats2['active_explosions']}, sounds={stats2['cached_sounds']}")
        print(f"Level3 stats: explosions={stats3['active_explosions']}, sounds={stats3['cached_sounds']}")
        
        # Cleanup one level at a time
        level1.cleanup()
        print("✓ Level1 cleaned up")
        
        # Check that other levels are unaffected
        stats2_after = level2.get_resource_stats()
        stats3_after = level3.get_resource_stats()
        
        if (stats2_after['active_explosions'] == stats2['active_explosions'] and 
            stats3_after['active_explosions'] == stats3['active_explosions']):
            print("✓ Level isolation confirmed - cleanup of one level didn't affect others")
        else:
            print("✗ Level isolation failed - cleanup affected other levels")
            return False
        
        # Cleanup remaining levels
        level2.cleanup()
        level3.cleanup()
        print("✓ All levels cleaned up")
        
    except Exception as e:
        print(f"✗ Resource isolation test failed: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("SS6 Audio and Resource Management Test Suite")
    print("=" * 50)
    
    try:
        # Run all tests
        audio_test = test_audio_system()
        resource_test = test_level_resource_manager()
        isolation_test = test_resource_isolation()
        
        print("\n" + "=" * 50)
        print("TEST RESULTS:")
        print(f"Audio System: {'✓ PASS' if audio_test else '✗ FAIL'}")
        print(f"Resource Manager: {'✓ PASS' if resource_test else '✗ FAIL'}")
        print(f"Resource Isolation: {'✓ PASS' if isolation_test else '✗ FAIL'}")
        
        if all([audio_test, resource_test, isolation_test]):
            print("\n🎉 ALL TESTS PASSED! The system is ready for use.")
            return True
        else:
            print("\n❌ SOME TESTS FAILED. Please check the implementation.")
            return False
    
    except Exception as e:
        print(f"\n💥 TEST SUITE CRASHED: {e}")
        return False
    
    finally:
        # Clean up pygame
        try:
            pygame.quit()
        except:
            pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)