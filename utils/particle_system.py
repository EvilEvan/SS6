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
        """Update all active particles."""
        particles_to_remove = []
        
        for particle in self.particles:
            if not particle["active"]:
                continue
                
            # Update position
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            
            # Update duration
            particle["duration"] -= 1
            
            # Check if particle should be removed
            if particle["duration"] <= 0:
                particles_to_remove.append(particle)
                continue
            
            # Cull particles that are too far offscreen
            if (particle["x"] < -self.culling_distance or 
                particle["x"] > self.culling_distance * 2 or
                particle["y"] < -self.culling_distance or 
                particle["y"] > self.culling_distance * 2):
                particles_to_remove.append(particle)
        
        # Remove expired/culled particles
        for particle in particles_to_remove:
            self.release_particle(particle)
    
    def draw(self, screen, offset_x=0, offset_y=0):
        """Draw all active particles."""
        for particle in self.particles:
            if not particle["active"]:
                continue
                
            # Calculate alpha based on remaining duration
            if particle["start_duration"] > 0:
                alpha_ratio = particle["duration"] / particle["start_duration"]
                alpha = max(0, min(255, int(255 * alpha_ratio)))
            else:
                alpha = 255
            
            # Create color with alpha
            if len(particle["color"]) == 3:
                color_with_alpha = (*particle["color"], alpha)
            else:
                color_with_alpha = particle["color"]
            
            # Calculate draw position with offset
            draw_x = int(particle["x"] + offset_x)
            draw_y = int(particle["y"] + offset_y)
            size = int(particle["size"])
            
            if size > 0:
                # Create surface with alpha for transparency
                particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, color_with_alpha, (size, size), size)
                screen.blit(particle_surface, (draw_x - size, draw_y - size)) 