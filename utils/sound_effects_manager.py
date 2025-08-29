import pygame
import numpy as np
import random
import threading
from typing import List, Optional
import math


class SoundEffectsManager:
    """
    Manages comedy sound effects for target destruction in SS6.
    Generates fart sound variants programmatically using sound synthesis.
    """
    
    def __init__(self, sample_rate: int = 22050, max_sounds: int = 5):
        """
        Initialize the SoundEffectsManager with robust error handling.
        
        Args:
            sample_rate (int): Audio sample rate for sound generation
            max_sounds (int): Number of fart sound variants to generate
        """
        self.sample_rate = sample_rate
        self.max_sounds = max_sounds
        self.sound_rotation = 0  # Round-robin counter
        self.fart_sounds: List[pygame.mixer.Sound] = []
        self.enabled = True
        self.volume = 0.7
        self._shutdown_requested = False
        
        # Threading lock for sound operations
        self._sound_lock = threading.Lock()
        
        # Initialize sound generation with error handling
        try:
            self._generate_fart_sounds()
        except Exception as e:
            print(f"SoundEffectsManager: Critical error during initialization: {e}")
            self.enabled = False
    
    def _generate_fart_sounds(self) -> None:
        """Generate 5 different fart sound variants using sound synthesis."""
        try:
            print("SoundEffectsManager: Generating fart sound variants...")
            
            # Clear existing sounds
            self.fart_sounds.clear()
            
            # Generate 5 unique fart sound variants
            for i in range(self.max_sounds):
                sound = self._create_fart_sound_variant(i)
                if sound:
                    self.fart_sounds.append(sound)
                    print(f"SoundEffectsManager: Generated fart sound variant {i+1}")
                
            print(f"SoundEffectsManager: Successfully generated {len(self.fart_sounds)} sound variants")
            
        except Exception as e:
            print(f"SoundEffectsManager: Failed to generate fart sounds: {e}")
            self.enabled = False
    
    def _create_fart_sound_variant(self, variant_id: int) -> Optional[pygame.mixer.Sound]:
        """
        Create a unique fart sound variant using procedural audio generation.
        
        Args:
            variant_id (int): Variant identifier (0-4) for different sound characteristics
            
        Returns:
            Optional[pygame.mixer.Sound]: Generated sound or None if failed
        """
        try:
            # Different characteristics for each variant
            sound_profiles = [
                {"duration": 0.3, "base_freq": 80, "freq_mod": 20, "noise_level": 0.6},    # Short pop
                {"duration": 0.6, "base_freq": 60, "freq_mod": 40, "noise_level": 0.8},    # Medium burp
                {"duration": 0.4, "base_freq": 100, "freq_mod": 15, "noise_level": 0.5},   # High pitched
                {"duration": 0.8, "base_freq": 45, "freq_mod": 60, "noise_level": 0.9},    # Long rumble
                {"duration": 0.2, "base_freq": 120, "freq_mod": 30, "noise_level": 0.4}    # Quick squeak
            ]
            
            profile = sound_profiles[variant_id % len(sound_profiles)]
            duration = profile["duration"]
            base_freq = profile["base_freq"]
            freq_modulation = profile["freq_mod"]
            noise_level = profile["noise_level"]
            
            # Calculate sample count
            num_samples = int(self.sample_rate * duration)
            
            # Generate time array
            t = np.linspace(0, duration, num_samples, False)
            
            # Create base tone with frequency modulation
            frequency_curve = base_freq + freq_modulation * np.sin(2 * np.pi * 3 * t)
            phase = np.cumsum(2 * np.pi * frequency_curve / self.sample_rate)
            base_tone = np.sin(phase)
            
            # Add harmonics for more complex sound
            harmonics = 0.3 * np.sin(2 * phase) + 0.2 * np.sin(3 * phase)
            base_tone += harmonics
            
            # Add noise component for realistic texture
            noise = noise_level * (np.random.random(num_samples) - 0.5)
            
            # Combine tone and noise
            sound_wave = base_tone + noise
            
            # Apply envelope (fade in/out) to avoid clicks
            envelope = self._create_envelope(num_samples, variant_id)
            sound_wave *= envelope
            
            # Normalize to prevent clipping
            if np.max(np.abs(sound_wave)) > 0:
                sound_wave = sound_wave / np.max(np.abs(sound_wave)) * 0.8
            
            # Convert to pygame sound format (16-bit integers)
            sound_array = (sound_wave * 32767).astype(np.int16)
            
            # Create stereo sound (duplicate mono to both channels)
            stereo_array = np.array([sound_array, sound_array]).T
            
            # Ensure array is C-contiguous for pygame
            stereo_array = np.ascontiguousarray(stereo_array)
            
            # Create pygame Sound object
            sound = pygame.sndarray.make_sound(stereo_array)
            return sound
            
        except Exception as e:
            print(f"SoundEffectsManager: Failed to create sound variant {variant_id}: {e}")
            return None
    
    def _create_envelope(self, num_samples: int, variant_id: int) -> np.ndarray:
        """
        Create amplitude envelope for natural sound fade-in/fade-out.
        
        Args:
            num_samples (int): Total number of audio samples
            variant_id (int): Variant ID for envelope customization
            
        Returns:
            np.ndarray: Amplitude envelope array
        """
        envelope = np.ones(num_samples)
        
        # Different envelope shapes for different variants
        if variant_id == 0:  # Quick attack, quick decay
            fade_in_samples = int(num_samples * 0.05)
            fade_out_samples = int(num_samples * 0.3)
        elif variant_id == 1:  # Gradual attack, sustained, gradual decay
            fade_in_samples = int(num_samples * 0.1)
            fade_out_samples = int(num_samples * 0.4)
        elif variant_id == 2:  # Sharp attack, sharp decay
            fade_in_samples = int(num_samples * 0.02)
            fade_out_samples = int(num_samples * 0.2)
        elif variant_id == 3:  # Slow attack, long sustain, slow decay
            fade_in_samples = int(num_samples * 0.15)
            fade_out_samples = int(num_samples * 0.5)
        else:  # Very quick attack and decay
            fade_in_samples = int(num_samples * 0.01)
            fade_out_samples = int(num_samples * 0.1)
        
        # Apply fade in
        if fade_in_samples > 0:
            envelope[:fade_in_samples] = np.linspace(0, 1, fade_in_samples)
        
        # Apply fade out
        if fade_out_samples > 0 and fade_out_samples < num_samples:
            start_idx = num_samples - fade_out_samples
            envelope[start_idx:] = np.linspace(1, 0, fade_out_samples)
        
        return envelope
    
    def play_destruction_sound(self, target_type: str = "default") -> bool:
        """
        Play a fart sound effect for target destruction.
        
        Args:
            target_type (str): Type of target destroyed (for future customization)
            
        Returns:
            bool: True if sound played successfully, False otherwise
        """
        if not self.enabled or not self.fart_sounds:
            return False
        
        try:
            with self._sound_lock:
                # Get next sound in rotation
                sound = self.fart_sounds[self.sound_rotation % len(self.fart_sounds)]
                
                # Add slight pitch variation for more variety
                sound.set_volume(self.volume + random.uniform(-0.1, 0.1))
                
                # Play the sound
                sound.play()
                
                # Advance rotation counter
                self.sound_rotation = (self.sound_rotation + 1) % len(self.fart_sounds)
                
                return True
                
        except Exception as e:
            print(f"SoundEffectsManager: Failed to play destruction sound: {e}")
            return False
    
    def set_volume(self, volume: float) -> None:
        """
        Set the volume for all fart sounds.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable sound effects.
        
        Args:
            enabled (bool): Whether sound effects are enabled
        """
        self.enabled = enabled
    
    def get_sound_count(self) -> int:
        """
        Get the number of available sound variants.
        
        Returns:
            int: Number of sound variants
        """
        return len(self.fart_sounds)
    
    def cleanup(self) -> None:
        """Clean up resources used by the sound effects manager."""
        try:
            print("SoundEffectsManager: Starting cleanup...")
            self._shutdown_requested = True
            
            with self._sound_lock:
                # Stop all playing sounds
                for sound in self.fart_sounds:
                    try:
                        sound.stop()
                    except:
                        pass
                
                # Clear sound list
                self.fart_sounds.clear()
                self.enabled = False
                print("SoundEffectsManager: Cleanup completed")
                
        except Exception as e:
            print(f"SoundEffectsManager: Error during cleanup: {e}")


# Global instance for easy access (optional)
_sound_effects_manager = None

def get_sound_effects_manager() -> SoundEffectsManager:
    """
    Get or create global SoundEffectsManager instance.
    
    Returns:
        SoundEffectsManager: Global sound effects manager
    """
    global _sound_effects_manager
    if _sound_effects_manager is None:
        _sound_effects_manager = SoundEffectsManager()
    return _sound_effects_manager


def cleanup_sound_effects():
    """Cleanup global sound effects manager."""
    global _sound_effects_manager
    if _sound_effects_manager is not None:
        _sound_effects_manager.cleanup()
        _sound_effects_manager = None
        _sound_effects_manager = None