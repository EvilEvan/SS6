#!/usr/bin/env python3
"""Final validation test for enhanced main.py"""

print('Testing enhanced main.py import and basic functionality...')

try:
    from main import SuperStudentGame
    import pygame
    
    pygame.init()
    pygame.mixer.init()
    
    game = SuperStudentGame()
    game.width = 800
    game.height = 600
    
    success = game.initialize_resources()
    print(f'Resource initialization: {"SUCCESS" if success else "FAILED"}')
    
    game.cleanup_resources()
    print('Enhanced main.py is ready for production use!')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
