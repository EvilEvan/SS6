import pygame
import os
import threading
import tempfile
import time
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor
import logging

# Optional TTS dependencies with graceful fallback
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("Warning: pyttsx3 not available. Offline TTS disabled.")

try:
    from gtts import gTTS
    import requests
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("Warning: gTTS not available. Online TTS disabled.")


class AudioManager:
    """
    Manages audio playback for target pronunciation and sound effects.
    Supports both offline (pyttsx3) and online (gTTS) text-to-speech engines.
    """
    
    def __init__(self, cache_limit: int = 50, max_workers: int = 2):
        """
        Initialize the AudioManager.
        
        Args:
            cache_limit (int): Maximum number of cached audio files
            max_workers (int): Maximum number of worker threads for async TTS
        """
        self.mixer_initialized = False
        self.sound_cache: Dict[str, pygame.mixer.Sound] = {}
        self.cache_access_times: Dict[str, float] = {}
        self.cache_limit = cache_limit
        self.tts_engine = None
        self.temp_dir = tempfile.mkdtemp(prefix="ss6_audio_")
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Audio settings
        self.enabled = True
        self.tts_method = "offline"  # "offline", "online", "prerecorded"
        self.language = "en"
        self.speech_rate = 150
        self.volume = 0.8
        
        # Threading lock for cache operations
        self._cache_lock = threading.Lock()
        
        # Initialize pygame mixer and TTS engine
        self.initialize()
    
    def initialize(self) -> bool:
        """
        Initialize pygame mixer and TTS engines.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Initialize pygame mixer if not already done
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                
            self.mixer_initialized = True
            pygame.mixer.set_num_channels(8)  # Allow multiple sounds simultaneously
            
            # Initialize offline TTS engine
            if PYTTSX3_AVAILABLE and self.tts_method == "offline":
                try:
                    self.tts_engine = pyttsx3.init()
                    self.tts_engine.setProperty('rate', self.speech_rate)
                    self.tts_engine.setProperty('volume', self.volume)
                    
                    # Try to set a clearer voice if available
                    voices = self.tts_engine.getProperty('voices')
                    if voices:
                        for voice in voices:
                            if 'english' in voice.name.lower() or 'zira' in voice.name.lower():
                                self.tts_engine.setProperty('voice', voice.id)
                                break
                                
                    print("AudioManager: Offline TTS engine initialized successfully")
                except Exception as e:
                    print(f"AudioManager: Failed to initialize pyttsx3: {e}")
                    self.tts_engine = None
                    self.tts_method = "online"
            
            return True
            
        except Exception as e:
            print(f"AudioManager: Failed to initialize audio system: {e}")
            self.mixer_initialized = False
            return False
    
    def play_pronunciation(self, text: str, language: str = None, blocking: bool = False) -> bool:
        """
        Play pronunciation of the given text.
        
        Args:
            text (str): Text to pronounce
            language (str): Language code (defaults to self.language)
            blocking (bool): Whether to wait for completion
            
        Returns:
            bool: True if playback started successfully, False otherwise
        """
        if not self.enabled or not self.mixer_initialized:
            return False
            
        text = text.strip().lower()
        language = language or self.language
        cache_key = f"{text}_{language}"
        
        # Check cache first
        with self._cache_lock:
            if cache_key in self.sound_cache:
                try:
                    sound = self.sound_cache[cache_key]
                    sound.set_volume(self.volume)
                    sound.play()
                    self.cache_access_times[cache_key] = time.time()
                    return True
                except Exception as e:
                    print(f"AudioManager: Failed to play cached sound: {e}")
                    # Remove corrupted cache entry
                    del self.sound_cache[cache_key]
                    if cache_key in self.cache_access_times:
                        del self.cache_access_times[cache_key]
        
        # Generate and play new audio
        if blocking:
            return self._generate_and_play_sync(text, language, cache_key)
        else:
            # Async generation for better performance
            self.executor.submit(self._generate_and_play_async, text, language, cache_key)
            return True
    
    def _generate_and_play_sync(self, text: str, language: str, cache_key: str) -> bool:
        """Synchronously generate and play audio."""
        try:
            sound = self._generate_audio(text, language)
            if sound:
                sound.set_volume(self.volume)
                sound.play()
                
                # Cache the sound
                with self._cache_lock:
                    self._add_to_cache(cache_key, sound)
                return True
        except Exception as e:
            print(f"AudioManager: Failed to generate audio for '{text}': {e}")
        return False
    
    def _generate_and_play_async(self, text: str, language: str, cache_key: str):
        """Asynchronously generate and play audio."""
        try:
            sound = self._generate_audio(text, language)
            if sound:
                # Use pygame's threadsafe event system
                pygame.event.post(pygame.event.Event(
                    pygame.USEREVENT + 1, 
                    {"action": "play_audio", "sound": sound, "cache_key": cache_key}
                ))
        except Exception as e:
            print(f"AudioManager: Async audio generation failed for '{text}': {e}")
    
    def _generate_audio(self, text: str, language: str) -> Optional[pygame.mixer.Sound]:
        """Generate audio using the configured TTS method."""
        if self.tts_method == "offline" and self.tts_engine:
            return self._generate_offline_audio(text)
        elif self.tts_method == "online" and GTTS_AVAILABLE:
            return self._generate_online_audio(text, language)
        else:
            print(f"AudioManager: No TTS method available for '{text}'")
            return None
    
    def _generate_offline_audio(self, text: str) -> Optional[pygame.mixer.Sound]:
        """Generate audio using pyttsx3 offline TTS."""
        try:
            temp_file = os.path.join(self.temp_dir, f"tts_{hash(text)}.wav")
            
            # Generate audio file
            self.tts_engine.save_to_file(text, temp_file)
            self.tts_engine.runAndWait()
            
            if os.path.exists(temp_file):
                sound = pygame.mixer.Sound(temp_file)
                # Clean up temp file after loading
                try:
                    os.remove(temp_file)
                except:
                    pass  # Ignore cleanup errors
                return sound
                
        except Exception as e:
            print(f"AudioManager: Offline TTS failed for '{text}': {e}")
        return None
    
    def _generate_online_audio(self, text: str, language: str) -> Optional[pygame.mixer.Sound]:
        """Generate audio using gTTS online service."""
        try:
            temp_file = os.path.join(self.temp_dir, f"gtts_{hash(text)}_{language}.mp3")
            
            # Generate audio using gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(temp_file)
            
            if os.path.exists(temp_file):
                sound = pygame.mixer.Sound(temp_file)
                # Clean up temp file after loading
                try:
                    os.remove(temp_file)
                except:
                    pass  # Ignore cleanup errors
                return sound
                
        except Exception as e:
            print(f"AudioManager: Online TTS failed for '{text}': {e}")
        return None
    
    def _add_to_cache(self, cache_key: str, sound: pygame.mixer.Sound):
        """Add sound to cache with automatic cleanup."""
        # Clean cache if at limit
        if len(self.sound_cache) >= self.cache_limit:
            self._cleanup_old_sounds()
        
        self.sound_cache[cache_key] = sound
        self.cache_access_times[cache_key] = time.time()
    
    def _cleanup_old_sounds(self):
        """Remove least recently used sounds from cache."""
        if not self.cache_access_times:
            return
            
        # Remove oldest 25% of cached sounds
        items_to_remove = max(1, len(self.cache_access_times) // 4)
        sorted_items = sorted(self.cache_access_times.items(), key=lambda x: x[1])
        
        for cache_key, _ in sorted_items[:items_to_remove]:
            if cache_key in self.sound_cache:
                del self.sound_cache[cache_key]
            del self.cache_access_times[cache_key]
    
    def preload_sounds(self, texts: List[str], language: str = None) -> int:
        """
        Preload multiple sounds into cache.
        
        Args:
            texts (List[str]): List of texts to preload
            language (str): Language code
            
        Returns:
            int: Number of sounds successfully preloaded
        """
        if not self.enabled or not self.mixer_initialized:
            return 0
            
        language = language or self.language
        loaded_count = 0
        
        for text in texts:
            text = text.strip().lower()
            cache_key = f"{text}_{language}"
            
            if cache_key not in self.sound_cache:
                try:
                    sound = self._generate_audio(text, language)
                    if sound:
                        with self._cache_lock:
                            self._add_to_cache(cache_key, sound)
                        loaded_count += 1
                except Exception as e:
                    print(f"AudioManager: Failed to preload '{text}': {e}")
        
        print(f"AudioManager: Preloaded {loaded_count}/{len(texts)} sounds")
        return loaded_count
    
    def handle_audio_event(self, event):
        """Handle audio-related pygame events (for async playback)."""
        if hasattr(event, 'action') and event.action == "play_audio":
            try:
                sound = event.sound
                cache_key = event.cache_key
                sound.set_volume(self.volume)
                sound.play()
                
                # Cache the sound
                with self._cache_lock:
                    self._add_to_cache(cache_key, sound)
            except Exception as e:
                print(f"AudioManager: Failed to handle audio event: {e}")
    
    def clear_cache(self):
        """Clear all cached sounds."""
        with self._cache_lock:
            self.sound_cache.clear()
            self.cache_access_times.clear()
    
    def cleanup(self):
        """Clean up resources."""
        self.clear_cache()
        
        # Shutdown TTS engine
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        # Clean up temp directory
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
    
    def set_enabled(self, enabled: bool):
        """Enable or disable audio."""
        self.enabled = enabled
    
    def set_volume(self, volume: float):
        """Set audio volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
    
    def set_tts_method(self, method: str):
        """Set TTS method: 'offline', 'online', or 'prerecorded'."""
        if method in ["offline", "online", "prerecorded"]:
            self.tts_method = method
            print(f"AudioManager: TTS method set to {method}")
        else:
            print(f"AudioManager: Invalid TTS method '{method}'")
    
    def get_stats(self) -> Dict:
        """Get audio manager statistics."""
        return {
            "enabled": self.enabled,
            "mixer_initialized": self.mixer_initialized,
            "tts_method": self.tts_method,
            "cached_sounds": len(self.sound_cache),
            "cache_limit": self.cache_limit,
            "volume": self.volume,
            "pyttsx3_available": PYTTSX3_AVAILABLE,
            "gtts_available": GTTS_AVAILABLE
        }