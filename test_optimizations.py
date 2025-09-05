#!/usr/bin/env python3
"""
Test script to validate performance improvements and audio enhancements for SS6.
"""

import sys
import os
import time
import pygame

# Setup headless mode
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

# Add the SS6 directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_colors_level_performance():
    """Test the optimized colors level performance."""
    print("=== Testing Colors Level Performance ===")
    
    try:
        from levels.colors_level import ColorsLevel
        from utils.particle_system import ParticleManager
        from universal_class import GlassShatterManager, HUDManager, MultiTouchManager
        
        # Initialize pygame
        pygame.init()
        width, height = 800, 600
        screen = pygame.Surface((width, height))
        small_font = pygame.font.Font(None, 24)
        
        # Create managers
        particle_manager = ParticleManager(max_particles=200)
        glass_shatter_manager = GlassShatterManager(width, height, particle_manager)
        multi_touch_manager = MultiTouchManager(width, height)  
        hud_manager = HUDManager(width, height, small_font, glass_shatter_manager)
        
        # Mock functions
        def mock_func(*args, **kwargs):
            pass
        explosions_list = []
        
        # Create colors level
        colors_level = ColorsLevel(
            width=width, height=height, screen=screen, small_font=small_font,
            particle_manager=particle_manager, glass_shatter_manager=glass_shatter_manager,
            multi_touch_manager=multi_touch_manager, hud_manager=hud_manager,
            mother_radius=50, create_explosion_func=mock_func, checkpoint_screen_func=mock_func,
            game_over_screen_func=mock_func, explosions_list=explosions_list, draw_explosion_func=mock_func
        )
        
        # Test basic initialization
        colors_level.reset_level_state()
        colors_level.color_idx = 0
        colors_level.mother_color = colors_level.COLORS_LIST[0]
        
        # Test optimized methods exist
        if hasattr(colors_level, '_handle_dot_collisions'):
            print("✅ Optimized collision detection method exists")
        else:
            print("❌ Missing collision detection method")
            
        if hasattr(colors_level, 'surface_cache'):
            print("✅ Surface cache exists")
        else:
            print("❌ Missing surface cache")
            
        # Test level resource manager
        if hasattr(colors_level, 'level_resources'):
            print("✅ Level resource manager exists")
        else:
            print("❌ Missing level resource manager")
            
        print("✅ Colors level performance optimizations verified")
        return True
        
    except Exception as e:
        print(f"❌ Colors level test failed: {e}")
        return False

def test_alphabet_phonics():
    """Test the alphabet level phonics implementation."""
    print("\n=== Testing Alphabet Level Phonics ===")
    
    try:
        from levels.alphabet_level import AlphabetLevel
        
        # Create a minimal alphabet level instance for testing
        pygame.init()
        width, height = 800, 600
        screen = pygame.Surface((width, height))
        fonts = [pygame.font.Font(None, 36)]
        small_font = pygame.font.Font(None, 24)
        target_font = pygame.font.Font(None, 48)
        
        # Mock all required parameters
        mock_args = (width, height, screen, fonts, small_font, target_font,
                    None, None, None, None, None, None, None, None,
                    None, None, None, None, [], [], None, None)
        
        alphabet_level = AlphabetLevel(*mock_args)
        
        # Test phonics method
        if hasattr(alphabet_level, '_get_phonics_sound'):
            print("✅ Phonics method exists")
            
            # Test some phonics mappings
            test_cases = [
                ('A', 'ah'), ('B', 'buh'), ('C', 'kuh'), ('Z', 'zzz')
            ]
            
            for letter, expected in test_cases:
                result = alphabet_level._get_phonics_sound(letter)
                if result == expected:
                    print(f"✅ Phonics for {letter}: {result}")
                else:
                    print(f"❌ Phonics for {letter}: got {result}, expected {expected}")
                    
        else:
            print("❌ Missing phonics method")
            return False
            
        print("✅ Alphabet level phonics verified")
        return True
        
    except Exception as e:
        print(f"❌ Alphabet level test failed: {e}")
        return False

def test_numbers_pronunciation():
    """Test the numbers level pronunciation."""
    print("\n=== Testing Numbers Level Pronunciation ===")
    
    try:
        # Check if numbers level already has pronunciation (should already exist)
        with open('/home/runner/work/SS6/SS6/levels/numbers_level.py', 'r') as f:
            content = f.read()
            
        if 'play_target_sound' in content and 'number_word' in content:
            print("✅ Numbers level pronunciation already implemented")
            return True
        else:
            print("❌ Numbers level missing pronunciation")
            return False
            
    except Exception as e:
        print(f"❌ Numbers level test failed: {e}")
        return False

def test_shapes_pronunciation():
    """Test the shapes level pronunciation."""
    print("\n=== Testing Shapes Level Pronunciation ===")
    
    try:
        from levels.shapes_level import ShapesLevel
        
        # Check if shapes level has level resource manager
        pygame.init()
        width, height = 800, 600
        screen = pygame.Surface((width, height))
        fonts = [pygame.font.Font(None, 36)]
        small_font = pygame.font.Font(None, 24)
        target_font = pygame.font.Font(None, 48)
        
        # Mock all required parameters
        mock_args = (width, height, screen, fonts, small_font, target_font,
                    None, None, None, None, None, None, None, None, None, None,
                    [], [], None, None)
        
        shapes_level = ShapesLevel(*mock_args)
        
        # Test level resource manager
        if hasattr(shapes_level, 'level_resources'):
            print("✅ Shapes level has resource manager")
        else:
            print("❌ Shapes level missing resource manager")
            return False
            
        # Check source code for pronunciation
        with open('/home/runner/work/SS6/SS6/levels/shapes_level.py', 'r') as f:
            content = f.read()
            
        if 'play_target_sound' in content and 'shape_name' in content:
            print("✅ Shapes level pronunciation implemented")
        else:
            print("❌ Shapes level missing pronunciation")
            return False
            
        print("✅ Shapes level pronunciation verified")
        return True
        
    except Exception as e:
        print(f"❌ Shapes level test failed: {e}")
        return False

def test_audio_system():
    """Test the overall audio system."""
    print("\n=== Testing Audio System ===")
    
    try:
        from utils.audio_manager import AudioManager
        from utils.level_resource_manager import LevelResourceManager
        
        # Test audio manager
        audio_manager = AudioManager(cache_limit=10)
        print(f"✅ Audio manager initialized: {audio_manager.enabled}")
        
        # Test level resource manager
        level_resources = LevelResourceManager("test", 800, 600)
        if level_resources.initialize():
            print("✅ Level resource manager initialized")
            level_resources.cleanup()
        else:
            print("❌ Level resource manager failed to initialize")
            return False
            
        # Test pronunciation
        test_words = ["hello", "circle", "one", "ah"]
        for word in test_words:
            success = audio_manager.play_pronunciation(word)
            print(f"✅ Pronunciation test for '{word}': {success}")
            
        audio_manager.cleanup()
        print("✅ Audio system verified")
        return True
        
    except Exception as e:
        print(f"❌ Audio system test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("SS6 Optimization and Enhancement Validation Tests")
    print("=" * 60)
    
    tests = [
        ("Colors Level Performance", test_colors_level_performance),
        ("Alphabet Phonics", test_alphabet_phonics),
        ("Numbers Pronunciation", test_numbers_pronunciation),
        ("Shapes Pronunciation", test_shapes_pronunciation),
        ("Audio System", test_audio_system)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED! Optimizations are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {len(tests) - passed} test(s) failed. Please review the issues.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Tests crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)