import pygame
import math
import time
from typing import List, Dict, Optional, Any
from utils.audio_manager import AudioManager
from utils.particle_system import ParticleManager


class LevelResourceManager:
    """
    Manages all resources for a single level instance to prevent cross-contamination
    between different game modes. Each level gets its own isolated resource manager.
    """
    
    def __init__(self, level_id: str, width: int, height: int, max_effects: Dict[str, int] = None):
        """
        Initialize level-specific resource manager.
        
        Args:
            level_id (str): Unique identifier for this level
            width (int): Screen width
            height (int): Screen height
            max_effects (Dict[str, int]): Maximum number of each effect type
        """
        self.level_id = level_id
        self.width = width
        self.height = height
        self.initialized = False
        
        # Default limits for performance
        default_limits = {
            "explosions": 20,
            "particles": 100,
            "lasers": 10,
            "sounds": 50
        }
        self.max_effects = max_effects or default_limits
        
        # Level-specific resource pools
        self.explosions: List[Dict[str, Any]] = []
        self.lasers: List[Dict[str, Any]] = []
        self.active_sounds: List[pygame.mixer.Sound] = []
        
        # Managers
        self.audio_manager: Optional[AudioManager] = None
        self.particle_manager: Optional[ParticleManager] = None
        
        # Performance tracking
        self.creation_time = time.time()
        self.resource_stats = {
            "explosions_created": 0,
            "particles_created": 0,
            "sounds_played": 0,
            "cleanup_calls": 0
        }
        
    def initialize(self) -> bool:
        """
        Initialize all level resources.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize audio manager
            self.audio_manager = AudioManager(cache_limit=self.max_effects["sounds"])
            
            # Initialize particle manager with level-specific limits
            self.particle_manager = ParticleManager(max_particles=self.max_effects["particles"])
            self.particle_manager.set_culling_distance(self.width)
            
            self.initialized = True
            print(f"LevelResourceManager: Initialized for level '{self.level_id}'")
            return True
            
        except Exception as e:
            print(f"LevelResourceManager: Failed to initialize level '{self.level_id}': {e}")
            return False
    
    def create_explosion(self, x: int, y: int, color=None, max_radius: int = 270, duration: int = 30) -> bool:
        """
        Create an explosion effect with level-specific management.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            color: Color tuple (optional)
            max_radius (int): Maximum explosion radius
            duration (int): Explosion duration in frames
            
        Returns:
            bool: True if explosion created successfully
        """
        if not self.initialized:
            return False
            
        # Enforce explosion limit
        if len(self.explosions) >= self.max_effects["explosions"]:
            # Remove oldest explosion
            self.explosions.pop(0)
        
        # Use flame colors if no color specified
        if color is None:
            from settings import FLAME_COLORS
            import random
            color = random.choice(FLAME_COLORS)
        
        explosion = {
            "x": x,
            "y": y,
            "radius": 10,  # Start small
            "color": color,
            "max_radius": max_radius,
            "duration": duration,
            "start_duration": duration,
            "created_time": time.time()
        }
        
        self.explosions.append(explosion)
        self.resource_stats["explosions_created"] += 1
        return True
    
    def create_laser(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                     color=None, width: int = 5, duration: int = 10) -> bool:
        """
        Create a laser effect.
        
        Args:
            start_x, start_y (int): Start coordinates
            end_x, end_y (int): End coordinates
            color: Laser color (optional)
            width (int): Laser width
            duration (int): Laser duration in frames
            
        Returns:
            bool: True if laser created successfully
        """
        if not self.initialized:
            return False
            
        # Enforce laser limit
        if len(self.lasers) >= self.max_effects["lasers"]:
            # Remove oldest laser
            self.lasers.pop(0)
        
        if color is None:
            from settings import FLAME_COLORS
            import random
            color = random.choice(FLAME_COLORS)
        
        laser = {
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "color": color,
            "width": width,
            "duration": duration,
            "start_duration": duration,
            "created_time": time.time()
        }
        
        self.lasers.append(laser)
        return True
    
    def play_target_sound(self, target: str, language: str = "en") -> bool:
        """
        Play pronunciation sound for a target.
        
        Args:
            target (str): Target text to pronounce
            language (str): Language code
            
        Returns:
            bool: True if sound played successfully
        """
        if not self.initialized or not self.audio_manager:
            return False
            
        success = self.audio_manager.play_pronunciation(target, language)
        if success:
            self.resource_stats["sounds_played"] += 1
        return success
    
    def preload_level_sounds(self, targets: List[str], language: str = "en") -> int:
        """
        Preload all sounds for this level.
        
        Args:
            targets (List[str]): List of target texts
            language (str): Language code
            
        Returns:
            int: Number of sounds successfully preloaded
        """
        if not self.initialized or not self.audio_manager:
            return 0
            
        return self.audio_manager.preload_sounds(targets, language)
    
    def create_particle(self, x: float, y: float, color, size: int, 
                       dx: float, dy: float, duration: int):
        """
        Create a particle effect.
        
        Args:
            x, y (float): Position coordinates
            color: Particle color
            size (int): Particle size
            dx, dy (float): Velocity components
            duration (int): Particle lifetime in frames
            
        Returns:
            Particle object or None
        """
        if not self.initialized or not self.particle_manager:
            return None
            
        particle = self.particle_manager.create_particle(x, y, color, size, dx, dy, duration)
        if particle:
            self.resource_stats["particles_created"] += 1
        return particle
    
    def update_effects(self):
        """Update all level effects."""
        if not self.initialized:
            return
            
        # Update explosions
        explosions_to_remove = []
        for explosion in self.explosions:
            explosion["duration"] -= 1
            explosion["radius"] += (explosion["max_radius"] - explosion["radius"]) * 0.1
            
            if explosion["duration"] <= 0:
                explosions_to_remove.append(explosion)
        
        for explosion in explosions_to_remove:
            self.explosions.remove(explosion)
        
        # Update lasers
        lasers_to_remove = []
        for laser in self.lasers:
            laser["duration"] -= 1
            
            if laser["duration"] <= 0:
                lasers_to_remove.append(laser)
        
        for laser in lasers_to_remove:
            self.lasers.remove(laser)
        
        # Update particles
        if self.particle_manager:
            self.particle_manager.update()
    
    def draw_effects(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """
        Draw all level effects.
        
        Args:
            screen: Pygame surface to draw on
            offset_x, offset_y (int): Screen shake offsets
        """
        if not self.initialized:
            return
            
        # Draw explosions
        for explosion in self.explosions:
            self._draw_explosion(screen, explosion, offset_x, offset_y)
        
        # Draw lasers
        for laser in self.lasers:
            self._draw_laser(screen, laser, offset_x, offset_y)
        
        # Draw particles
        if self.particle_manager:
            self.particle_manager.draw(screen, offset_x, offset_y)
    
    def _draw_explosion(self, screen: pygame.Surface, explosion: Dict[str, Any], 
                       offset_x: int = 0, offset_y: int = 0):
        """Draw a single explosion."""
        # Calculate alpha based on remaining duration
        alpha = max(0, int(255 * (explosion["duration"] / explosion["start_duration"])))
        color = (*explosion["color"][:3], alpha)
        radius = int(explosion["radius"])
        
        # Apply shake offset
        draw_x = int(explosion["x"] + offset_x)
        draw_y = int(explosion["y"] + offset_y)
        
        # Draw using SRCALPHA surface for transparency
        if radius > 0:
            explosion_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(explosion_surf, color, (radius, radius), radius)
            screen.blit(explosion_surf, (draw_x - radius, draw_y - radius))
    
    def _draw_laser(self, screen: pygame.Surface, laser: Dict[str, Any], 
                   offset_x: int = 0, offset_y: int = 0):
        """Draw a single laser."""
        # Calculate alpha based on remaining duration
        alpha = max(0, int(255 * (laser["duration"] / laser["start_duration"])))
        color = (*laser["color"][:3], alpha)
        
        # Apply shake offset
        start_pos = (int(laser["start_x"] + offset_x), int(laser["start_y"] + offset_y))
        end_pos = (int(laser["end_x"] + offset_x), int(laser["end_y"] + offset_y))
        
        # Draw laser line
        if alpha > 0:
            # Create surface for alpha blending
            laser_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.line(laser_surf, color, start_pos, end_pos, laser["width"])
            screen.blit(laser_surf, (0, 0))
    
    def apply_explosion_effect(self, x: int, y: int, explosion_radius: int, objects: List[Dict]):
        """
        Apply explosion push effect to objects.
        
        Args:
            x, y (int): Explosion center
            explosion_radius (int): Effect radius
            objects (List[Dict]): Objects to affect (must have x, y, dx, dy)
        """
        for obj in objects:
            dx = obj["x"] - x
            dy = obj["y"] - y
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < explosion_radius * explosion_radius and dist_sq > 0:
                dist = math.sqrt(dist_sq)
                # Force is stronger closer to the center
                force = (1 - (dist / explosion_radius)) * 15
                # Apply force directly to velocity
                obj["dx"] += (dx / dist) * force
                obj["dy"] += (dy / dist) * force
                # Ensure the item can bounce after being pushed
                if "can_bounce" in obj:
                    obj["can_bounce"] = True
    
    def handle_audio_event(self, event: pygame.event.Event):
        """Handle audio-related events."""
        if self.audio_manager:
            self.audio_manager.handle_audio_event(event)
    
    def cleanup(self):
        """Clean up all level resources."""
        if not self.initialized:
            return
            
        self.resource_stats["cleanup_calls"] += 1
        
        # Clear all effects
        self.explosions.clear()
        self.lasers.clear()
        self.active_sounds.clear()
        
        # Clean up managers
        if self.audio_manager:
            self.audio_manager.cleanup()
            self.audio_manager = None
            
        if self.particle_manager:
            # Particle manager cleanup
            self.particle_manager.particles.clear()
            self.particle_manager = None
        
        self.initialized = False
        
        # Log cleanup stats
        elapsed_time = time.time() - self.creation_time
        print(f"LevelResourceManager: Cleaned up level '{self.level_id}' after {elapsed_time:.1f}s")
        print(f"  Stats: {self.resource_stats}")
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        return {
            "level_id": self.level_id,
            "initialized": self.initialized,
            "active_explosions": len(self.explosions),
            "active_lasers": len(self.lasers),
            "active_particles": len(self.particle_manager.particles) if self.particle_manager else 0,
            "cached_sounds": len(self.audio_manager.sound_cache) if self.audio_manager else 0,
            "max_effects": self.max_effects,
            "creation_stats": self.resource_stats,
            "uptime": time.time() - self.creation_time
        }
    
    def force_cleanup_old_effects(self, max_age_seconds: float = 30.0):
        """
        Force cleanup of effects older than specified age.
        
        Args:
            max_age_seconds (float): Maximum age for effects
        """
        current_time = time.time()
        
        # Clean old explosions
        self.explosions = [exp for exp in self.explosions 
                          if (current_time - exp["created_time"]) < max_age_seconds]
        
        # Clean old lasers
        self.lasers = [laser for laser in self.lasers 
                      if (current_time - laser["created_time"]) < max_age_seconds]
    
    def __del__(self):
        """Ensure cleanup on object destruction."""
        try:
            self.cleanup()
        except:
            pass  # Ignore cleanup errors during destruction