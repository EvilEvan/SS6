import pygame
import random
import math

class ParticleManager:
    """Manages particle effects with object pooling for performance."""
    
    def __init__(self, max_particles=100):
        self.max_particles = max_particles
        self.particles = []
        self.particle_pool = []
        self.culling_distance = 1920  # Default culling distance
        
        # Pre-create particle pool for object reuse
        for _ in range(max_particles):
            self.particle_pool.append({
                "x": 0, "y": 0, "color": (0, 0, 0), "size": 0,
                "dx": 0, "dy": 0, "duration": 0, "start_duration": 0,
                "active": False
            })
    
    def set_culling_distance(self, distance):
        """Set the distance at which to cull offscreen particles."""
        self.culling_distance = distance
    
    def get_particle(self):
        """Get a particle from the pool."""
        for particle in self.particle_pool:
            if not particle["active"]:
                particle["active"] = True
                return particle
        return None  # Pool exhausted
    
    def release_particle(self, particle):
        """Return a particle to the pool."""
        if particle in self.particles:
            self.particles.remove(particle)
        particle["active"] = False
    
    def create_particle(self, x, y, color, size, dx, dy, duration):
        """Create a new particle effect."""
        if len(self.particles) >= self.max_particles:
            # Remove oldest particle if at limit
            oldest = min(self.particles, key=lambda p: p["duration"])
            self.release_particle(oldest)
        
        particle = self.get_particle()
        if particle:
            particle.update({
                "x": x, "y": y, "color": color, "size": size,
                "dx": dx, "dy": dy, "duration": duration,
                "start_duration": duration, "active": True
            })
            self.particles.append(particle)
            return particle
        return None
    
    def update(self):
        """Update all active particles with optimized batch processing."""
        if not self.particles:
            return
            
        # Use list comprehension for better performance
        active_particles = []
        
        for particle in self.particles:
            if not particle["active"]:
                continue
                
            # Update position and duration in one pass
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["duration"] -= 1
            
            # Early exit checks for performance
            if particle["duration"] <= 0:
                particle["active"] = False
                continue
            
            # Optimized culling check with single bounds test
            if not (-self.culling_distance <= particle["x"] <= self.culling_distance * 2 and
                    -self.culling_distance <= particle["y"] <= self.culling_distance * 2):
                particle["active"] = False
                continue
                
            active_particles.append(particle)
        
        # Batch update particles list
        self.particles = active_particles
        
        # Return deactivated particles to pool in batch
        for particle in self.particle_pool:
            if not particle["active"] and particle not in self.particles:
                continue  # Already returned to pool
    
    def draw(self, screen, offset_x=0, offset_y=0):
        """Draw all active particles with optimized rendering."""
        if not self.particles:
            return
            
        # Pre-calculate common values
        screen_rect = screen.get_rect()
        
        for particle in self.particles:
            if not particle["active"]:
                continue
            
            # Early culling for screen bounds
            draw_x = int(particle["x"] + offset_x)
            draw_y = int(particle["y"] + offset_y)
            size = int(particle["size"])
            
            # Skip particles outside screen bounds plus margin
            if (draw_x + size < screen_rect.left - 50 or 
                draw_x - size > screen_rect.right + 50 or
                draw_y + size < screen_rect.top - 50 or 
                draw_y - size > screen_rect.bottom + 50):
                continue
                
            # Calculate alpha based on remaining duration (optimized)
            alpha = 255
            if particle["start_duration"] > 0:
                alpha_ratio = particle["duration"] / particle["start_duration"]
                alpha = max(50, min(255, int(255 * alpha_ratio)))  # Minimum alpha for visibility
            
            # Use direct drawing for better performance on small particles
            if size <= 2:
                # Small particles - direct pixel drawing
                color = particle["color"][:3]  # Remove alpha if present
                pygame.draw.circle(screen, color, (draw_x, draw_y), size)
            else:
                # Larger particles - use surface with alpha
                color_with_alpha = (*particle["color"][:3], alpha)
                particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, color_with_alpha, (size, size), size)
                screen.blit(particle_surface, (draw_x - size, draw_y - size))
    
    def get_active_count(self) -> int:
        """Get the number of currently active particles."""
        return len(self.particles)
    
    def set_adaptive_quality(self, target_fps: float = 60.0, current_fps: float = 60.0):
        """Adjust particle quality based on performance."""
        if current_fps < target_fps * 0.8:  # If FPS drops below 80% of target
            # Reduce particle count by removing oldest particles
            particles_to_remove = min(10, len(self.particles) // 4)
            for i in range(particles_to_remove):
                if self.particles:
                    oldest_particle = min(self.particles, key=lambda p: p["duration"])
                    self.release_particle(oldest_particle)
    
    def cleanup(self):
        """Clean up all particles and reset the system."""
        try:
            # Deactivate all particles
            for particle in self.particles:
                particle["active"] = False
            
            # Clear particle list
            self.particles.clear()
            
            print("ParticleManager: Cleanup completed")
        except Exception as e:
            print(f"ParticleManager: Error during cleanup: {e}") 