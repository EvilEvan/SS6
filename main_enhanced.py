"""
Super Student 6 - Enhanced Main Entry Point

This is the optimized main entry point for SS6 that incorporates all performance
and audio enhancements while maintaining maximum stability. It features:

- Comprehensive error handling and recovery
- Resource management and cleanup
- Performance monitoring
- Audio optimization integration
- Display mode optimization
- Memory management and leak prevention
"""

import pygame
import sys
import traceback
import os
import pathlib
import gc
from typing import Optional

# Ensure repository root is on sys.path for imports
_REPO_ROOT = pathlib.Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Import core game modules with error handling
try:
    from settings import *
    from Display_settings import *
    from universal_class import *
    from welcome_screen import welcome_screen, level_menu
    from levels import ColorsLevel, ShapesLevel, AlphabetLevel, NumbersLevel, CLCaseLevel
    from utils.resource_manager import ResourceManager
    from utils.particle_system import ParticleManager
    from utils.level_resource_manager import LevelResourceManager
    from utils.audio_manager import AudioManager
    from utils.sound_effects_manager import SoundEffectsManager
except ImportError as e:
    print(f"Critical import error: {e}")
    print("Please ensure all required modules are available.")
    sys.exit(1)


class SuperStudentGame:
    """
    Main game controller that manages the entire SS6 application lifecycle.
    Provides robust error handling, resource management, and performance optimization.
    """
    
    def __init__(self):
        """Initialize the game controller with all necessary managers."""
        self.running = True
        self.screen = None
        self.clock = None
        self.width = 0
        self.height = 0
        self.resource_manager = None
        self.particle_manager = None
        self.audio_manager = None
        self.sound_effects_manager = None
        self.managers = {}
        self.display_mode = DEFAULT_MODE
        self.error_count = 0
        self.max_errors = 5  # Maximum errors before graceful shutdown
        
    def initialize_pygame(self) -> bool:
        """
        Initialize pygame with comprehensive error handling.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            pygame.init()
            
            # Configure allowed events for performance
            pygame.event.set_allowed([
                pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION,
                pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, 
                pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION
            ])
            
            # Get display info and setup screen
            info = pygame.display.Info()
            self.width, self.height = info.current_w, info.current_h
            
            self.screen = pygame.display.set_mode(
                (self.width, self.height), 
                pygame.FULLSCREEN
            )
            pygame.display.set_caption("Super Student 6 - Enhanced")
            
            self.clock = pygame.time.Clock()
            
            print(f"Pygame initialized successfully - Resolution: {self.width}x{self.height}")
            return True
            
        except Exception as e:
            print(f"Failed to initialize pygame: {e}")
            return False
    
    def initialize_resources(self) -> bool:
        """
        Initialize all game resources with the optimized managers.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Load display mode preferences
            self.display_mode = load_display_mode()
            
            # Initialize core resource manager
            self.resource_manager = ResourceManager()
            self.resource_manager.set_display_mode(self.display_mode)
            
            # Initialize core resources
            resources = self.resource_manager.initialize_game_resources()
            
            # Initialize particle manager with optimized settings
            max_particles = PARTICLES_SETTINGS[self.display_mode]
            self.particle_manager = ParticleManager(max_particles=max_particles)
            self.particle_manager.set_culling_distance(self.width)
            
            # Initialize audio systems
            self.audio_manager = AudioManager(cache_limit=30, max_workers=2)
            self.sound_effects_manager = SoundEffectsManager()
            
            # Initialize universal class managers
            self.managers = {
                'glass_shatter': GlassShatterManager(self.width, self.height, self.particle_manager),
                'multi_touch': MultiTouchManager(self.width, self.height),
                'hud': HUDManager(self.width, self.height, resources['small_font'], None),
                'checkpoint': CheckpointManager(self.width, self.height, resources['fonts'], resources['small_font']),
                'flamethrower': FlamethrowerManager(),
                'center_piece': CenterPieceManager(
                    self.width, self.height, self.display_mode, 
                    self.particle_manager, SWIRL_SETTINGS[self.display_mode], 
                    self.resource_manager
                )
            }
            
            # Link managers that need references to each other
            self.managers['hud'].glass_shatter_manager = self.managers['glass_shatter']
            
            # Save display mode preference
            save_display_mode(self.display_mode)
            
            print(f"Resources initialized successfully for display mode: {self.display_mode}")
            print(f"Audio Manager: {'Enabled' if self.audio_manager.enabled else 'Disabled'}")
            print(f"Sound Effects: {'Enabled' if self.sound_effects_manager.enabled else 'Disabled'}")
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize resources: {e}")
            traceback.print_exc()
            return False
    
    def cleanup_resources(self):
        """Thoroughly clean up all resources to prevent memory leaks."""
        try:
            print("Cleaning up game resources...")
            
            # Cleanup audio systems
            if hasattr(self, 'audio_manager') and self.audio_manager:
                self.audio_manager.cleanup()
                
            if hasattr(self, 'sound_effects_manager') and self.sound_effects_manager:
                self.sound_effects_manager.cleanup()
            
            # Cleanup particle systems
            if hasattr(self, 'particle_manager') and self.particle_manager:
                self.particle_manager.clear()
            
            # Cleanup managers
            for manager_name, manager in self.managers.items():
                if hasattr(manager, 'cleanup'):
                    manager.cleanup()
            
            # Force garbage collection
            gc.collect()
            
            print("Resource cleanup completed")
            
        except Exception as e:
            print(f"Error during resource cleanup: {e}")
    
    def handle_error(self, error: Exception, context: str = "Unknown"):
        """
        Handle errors gracefully with logging and recovery.
        
        Args:
            error: The exception that occurred
            context: Description of when/where the error occurred
        """
        self.error_count += 1
        
        print(f"\n=== ERROR #{self.error_count} in {context} ===")
        print(f"Error: {error}")
        print("Traceback:")
        traceback.print_exc()
        print("=" * 50)
        
        if self.error_count >= self.max_errors:
            print(f"Maximum error count ({self.max_errors}) reached. Shutting down gracefully...")
            self.running = False
    
    def run_level(self, level_mode: str) -> bool:
        """
        Run a specific game level with comprehensive error handling.
        
        Args:
            level_mode: The game mode/level to run
            
        Returns:
            bool: True if level should restart, False otherwise
        """
        try:
            print(f"\n=== Starting Level: {level_mode} ===")
            
            # Create level resource manager for isolation
            level_resource_manager = LevelResourceManager(
                audio_manager=self.audio_manager,
                sound_effects_manager=self.sound_effects_manager
            )
            
            # Get core resources for level
            resources = self.resource_manager.initialize_game_resources()
            
            # Common level arguments
            level_args = (
                self.width, self.height, self.screen,
                resources['fonts'], resources['small_font'], resources['target_font'],
                self.particle_manager, self.managers['glass_shatter'], self.managers['multi_touch'],
                self.managers['hud'], self.managers['checkpoint'], self.managers['center_piece'],
                self.managers['flamethrower'], level_resource_manager
            )
            
            # Create and run the appropriate level
            level_instance = None
            
            if level_mode == "colors":
                level_instance = ColorsLevel(*level_args)
            elif level_mode == "shapes":
                level_instance = ShapesLevel(*level_args)
            elif level_mode == "alphabet":
                level_instance = AlphabetLevel(*level_args)
            elif level_mode == "numbers":
                level_instance = NumbersLevel(*level_args)
            elif level_mode == "clcase":
                level_instance = CLCaseLevel(*level_args)
            else:
                raise ValueError(f"Unknown level mode: {level_mode}")
            
            # Run the level
            result = level_instance.run()
            
            # Cleanup level resources
            level_resource_manager.cleanup()
            
            print(f"Level {level_mode} completed successfully")
            return result
            
        except Exception as e:
            self.handle_error(e, f"Level: {level_mode}")
            return False
    
    def main_loop(self):
        """Main game loop with comprehensive error handling and resource management."""
        try:
            # Show welcome screen and get display mode
            self.display_mode = welcome_screen(
                self.width, self.height, self.screen, 
                self.resource_manager.initialize_game_resources()['small_font'],
                lambda: self.initialize_resources()
            )
            
            # Main game loop
            while self.running:
                try:
                    # Show level selection menu
                    selected_mode = level_menu(
                        self.width, self.height, self.screen,
                        self.resource_manager.initialize_game_resources()['small_font']
                    )
                    
                    if selected_mode is None:
                        break
                    
                    # Run selected level with restart capability
                    restart_level = self.run_level(selected_mode)
                    
                    # Handle level restart for shapes and colors levels
                    while restart_level and selected_mode in ["shapes", "colors"]:
                        print(f"Restarting level: {selected_mode}")
                        restart_level = self.run_level(selected_mode)
                        
                except KeyboardInterrupt:
                    print("Game interrupted by user")
                    break
                except Exception as e:
                    self.handle_error(e, "Main Loop")
                    if self.error_count >= self.max_errors:
                        break
                        
        except Exception as e:
            self.handle_error(e, "Main Loop Setup")
    
    def run(self):
        """Main entry point for the game."""
        try:
            print("=" * 60)
            print("SUPER STUDENT 6 - ENHANCED EDITION")
            print("=" * 60)
            print("Initializing game systems...")
            
            # Initialize pygame
            if not self.initialize_pygame():
                print("Failed to initialize pygame. Exiting.")
                return 1
            
            # Initialize game resources
            if not self.initialize_resources():
                print("Failed to initialize game resources. Exiting.")
                return 1
                
            print("Initialization complete. Starting game...")
            
            # Run main game loop
            self.main_loop()
            
            print("Game session completed.")
            return 0
            
        except KeyboardInterrupt:
            print("\nGame interrupted by user")
            return 0
        except Exception as e:
            print(f"Critical error: {e}")
            traceback.print_exc()
            return 1
        finally:
            # Always cleanup resources
            self.cleanup_resources()
            if pygame.get_init():
                pygame.quit()
            print("Game shutdown complete.")


def main():
    """Entry point function."""
    game = SuperStudentGame()
    return game.run()


if __name__ == "__main__":
    sys.exit(main())