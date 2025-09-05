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
import tempfile
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
        self.lock_file = None
        self.lock_file_path = os.path.join(tempfile.gettempdir(), "ss6_game.lock")
        
    def check_single_instance(self) -> bool:
        """
        Check if another instance is already running.
        
        Returns:
            bool: True if this is the only instance, False otherwise
        """
        try:
            if os.path.exists(self.lock_file_path):
                # Check if the process is still running
                try:
                    with open(self.lock_file_path, 'r') as f:
                        pid = int(f.read().strip())
                    
                    # Check if process exists (Windows-compatible)
                    import psutil
                    if psutil.pid_exists(pid):
                        print(f"Another SS6 instance is already running (PID: {pid})")
                        return False
                    else:
                        # Stale lock file, remove it
                        os.remove(self.lock_file_path)
                except (ValueError, FileNotFoundError):
                    # Invalid or missing lock file
                    if os.path.exists(self.lock_file_path):
                        os.remove(self.lock_file_path)
            
            # Create lock file
            with open(self.lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            
            self.lock_file = self.lock_file_path
            return True
            
        except Exception as e:
            print(f"Warning: Could not check for single instance: {e}")
            return True  # Allow to run if check fails
    
    def cleanup_lock_file(self):
        """Clean up the lock file on exit."""
        try:
            if self.lock_file and os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                print("Lock file cleaned up")
        except Exception as e:
            print(f"Warning: Could not clean up lock file: {e}")
        
    def initialize_pygame(self) -> bool:
        """
        Initialize pygame with comprehensive error handling for headless environments.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Check for headless environment before initializing audio
            headless_mode = self._detect_headless_environment()
            if headless_mode:
                print("Headless environment detected - initializing in silent mode")
                os.environ['SDL_AUDIODRIVER'] = 'dummy'
            
            # Initialize pygame with environment-appropriate settings
            if headless_mode:
                # Initialize without audio for headless environments
                pygame.display.init()
                pygame.font.init()
                # Skip mixer initialization in headless mode
            else:
                pygame.init()
            
            # Configure allowed events for performance
            pygame.event.set_allowed([
                pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION,
                pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, 
                pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION
            ])
            
            # Get display info and setup screen
            try:
                info = pygame.display.Info()
                self.width, self.height = info.current_w, info.current_h
            except:
                # Fallback for headless environments
                self.width, self.height = 800, 600
            
            # Try to create display surface (may fail in headless)
            try:
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), 
                    pygame.FULLSCREEN if not headless_mode else 0
                )
                pygame.display.set_caption("Super Student 6 - Enhanced")
            except pygame.error:
                # Fallback for headless - create a surface
                self.screen = pygame.Surface((self.width, self.height))
                print("Display unavailable - using virtual surface")
            
            self.clock = pygame.time.Clock()
            
            print(f"Pygame initialized successfully - Resolution: {self.width}x{self.height}")
            print(f"Audio mode: {'Silent' if headless_mode else 'Enabled'}")
            return True
            
        except Exception as e:
            print(f"Failed to initialize pygame: {e}")
            return False
    
    def _detect_headless_environment(self) -> bool:
        """Detect if we're running in a headless environment."""
        # Check for explicit audio driver setting
        if os.environ.get('SDL_AUDIODRIVER') == 'dummy':
            return True
            
        # Check for display availability on Unix-like systems
        if os.name != 'nt' and not os.environ.get('DISPLAY'):
            return True
            
        # Check for common CI/headless environment indicators
        headless_indicators = ['CI', 'TRAVIS', 'GITHUB_ACTIONS', 'JENKINS', 'BUILDBOT']
        if any(os.environ.get(indicator) for indicator in headless_indicators):
            return True
            
        # Check for specific user variables that indicate testing
        if os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('TESTING'):
            return True
            
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
            max_particles = MAX_PARTICLES[self.display_mode]
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
                    self.particle_manager, MAX_SWIRL_PARTICLES[self.display_mode], 
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
        """Thoroughly clean up all resources to prevent memory leaks with enhanced cleanup."""
        try:
            print("Cleaning up game resources...")
            
            # Enhanced cleanup with memory pressure monitoring
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Cleanup audio systems
            if hasattr(self, 'audio_manager') and self.audio_manager:
                self.audio_manager.cleanup()
                del self.audio_manager
                
            if hasattr(self, 'sound_effects_manager') and self.sound_effects_manager:
                self.sound_effects_manager.cleanup()
                del self.sound_effects_manager
            
            # Cleanup particle systems with enhanced clearing
            if hasattr(self, 'particle_manager') and self.particle_manager:
                if hasattr(self.particle_manager, 'cleanup'):
                    self.particle_manager.cleanup()
                else:
                    # Enhanced fallback cleanup
                    self.particle_manager.particles.clear()
                    for particle in self.particle_manager.particle_pool:
                        particle["active"] = False
                        # Clear particle data
                        particle.update({"x": 0, "y": 0, "dx": 0, "dy": 0, "duration": 0})
                del self.particle_manager
            
            # Enhanced manager cleanup
            for manager_name, manager in self.managers.items():
                if hasattr(manager, 'cleanup'):
                    manager.cleanup()
                # Force deletion of manager references
                del manager
            self.managers.clear()
            
            # Clear resource manager caches
            if hasattr(self, 'resource_manager') and self.resource_manager:
                if hasattr(self.resource_manager, 'font_cache'):
                    self.resource_manager.font_cache.clear()
                del self.resource_manager
            
            # Aggressive garbage collection
            gc.collect()
            gc.collect()  # Call twice for circular references
            
            # Clean up lock file
            self.cleanup_lock_file()
            
            # Memory usage reporting
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_freed = memory_before - memory_after
            print(f"Resource cleanup completed - Memory freed: {memory_freed:.2f}MB")
            
        except Exception as e:
            print(f"Error during resource cleanup: {e}")
    
    def _check_memory_pressure(self) -> bool:
        """Check if system is under memory pressure and trigger cleanup if needed."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            # If available memory is less than 20% or we're using > 200MB
            if memory.percent > 80:
                print(f"Memory pressure detected: {memory.percent}% used")
                gc.collect()  # Force garbage collection
                return True
                
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            if process_memory > 200:  # More than 200MB
                print(f"High process memory usage: {process_memory:.1f}MB")
                gc.collect()
                return True
                
            return False
            
        except Exception:
            return False  # If we can't check, assume no pressure
    
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
            
            # Check for memory pressure after level completion
            if self._check_memory_pressure():
                print("Performing additional cleanup due to memory pressure")
                gc.collect()
            
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
            
            # Check for single instance
            if not self.check_single_instance():
                print("Another instance is already running. Exiting.")
                return 1
            
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