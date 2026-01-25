#!/usr/bin/env python3
"""
FIXED Async Voice Engine - Works reliably
"""

import pyttsx3
import asyncio
from dataclasses import dataclass
import time

@dataclass
class VoiceConfig:
    """Voice configuration"""
    name: str
    voice_gender: str = "male"
    voice_speed: int = 180

class FixedVoiceEngine:
    """RELIABLE voice engine - creates NEW engine for each speech"""
    
    def __init__(self):
        self.available_voices = self._get_available_voices()
        print(f"✓ Voice engine initialized with {len(self.available_voices)} voices")
    
    def _get_available_voices(self):
        """Get list of available voices"""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            engine.stop()
            return voices
        except:
            return []
    
    def _create_engine(self, config: VoiceConfig):
        """Create a NEW engine for each speech"""
        try:
            engine = pyttsx3.init()
            
            # Set rate
            engine.setProperty('rate', config.voice_speed)
            engine.setProperty('volume', 1.0)
            
            # Set voice based on gender
            if self.available_voices:
                if config.voice_gender == "female" and len(self.available_voices) > 1:
                    engine.setProperty('voice', self.available_voices[1].id)
                else:
                    engine.setProperty('voice', self.available_voices[0].id)
            
            return engine
        except Exception as e:
            print(f"❌ Failed to create engine for {config.name}: {e}")
            return None
    
    def speak(self, text: str, config: VoiceConfig):
        """SPEAK RELIABLY - New engine each time"""
        print(f"\n🎤 [{config.name.upper()}]: {text}")
        print("-" * 50)
        
        engine = self._create_engine(config)
        if not engine:
            return False
        
        try:
            engine.say(text)
            engine.runAndWait()
            engine.stop()  # Important: stop the engine
            return True
        except Exception as e:
            print(f"❌ Speech error for {config.name}: {e}")
            return False
        finally:
            # Ensure engine is destroyed
            try:
                del engine
            except:
                pass
    
    async def speak_async(self, text: str, config: VoiceConfig):
        """Async speech with timing"""
        # Run speech in thread
        loop = asyncio.get_event_loop()
        
        # Estimate speech duration
        words = len(text.split())
        duration = max(1.0, words / 3)  # ~3 words per second
        
        # Speak
        await loop.run_in_executor(None, self.speak, text, config)
        
        # Small pause after speech
        await asyncio.sleep(0.3)