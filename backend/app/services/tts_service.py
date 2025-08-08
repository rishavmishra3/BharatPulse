import pyttsx3
import asyncio
import base64
import io
import os
import tempfile
from gtts import gTTS
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.engine = None
        self._init_pyttsx3()
        
        # Language voice mapping
        self.voice_mapping = {
            "hi": "hi",
            "en": "en",
            "bn": "bn",
            "ta": "ta"
        }
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 for offline TTS"""
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            
            # Find Hindi voice if available
            for voice in voices:
                if 'hindi' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            # Set speech rate and volume
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 1.0)
            logger.info("✅ pyttsx3 TTS initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ pyttsx3 initialization failed: {e}")
            self.engine = None
    
    async def synthesize(self, text: str, lang: str = "hi", slow: bool = False) -> str:
        """Synthesize text to speech and return base64 audio"""
        try:
            # Try offline TTS first
            if self.engine and lang == "hi":
                audio_data = await self._offline_tts(text, slow)
            else:
                # Use online TTS as fallback
                audio_data = await self._online_tts(text, lang, slow)
            
            if audio_data:
                # Convert to base64
                audio_base64 = base64.b64encode(audio_data).decode()
                return audio_base64
            else:
                return ""
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return ""
    
    async def _offline_tts(self, text: str, slow: bool = False) -> bytes:
        """Generate speech using pyttsx3 (offline)"""
        if not self.engine:
            raise Exception("pyttsx3 engine not available")
        
        def generate_speech():
            try:
                # Adjust rate for slow speech
                rate = 100 if slow else 150
                self.engine.setProperty('rate', rate)
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_filename = temp_file.name
                
                # Generate speech
                self.engine.save_to_file(text, temp_filename)
                self.engine.runAndWait()
                
                # Read the generated file
                with open(temp_filename, 'rb') as f:
                    audio_data = f.read()
                
                # Clean up
                os.unlink(temp_filename)
                
                return audio_data
                
            except Exception as e:
                logger.error(f"Offline TTS generation error: {e}")
                return b""
        
        # Run in thread to avoid blocking
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(None, generate_speech)
        
        return audio_data
    
    async def _online_tts(self, text: str, lang: str, slow: bool = False) -> bytes:
        """Generate speech using gTTS (requires internet)"""
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=lang, slow=slow)
            
            # Save to memory buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            
            # Get audio data
            audio_buffer.seek(0)
            audio_data = audio_buffer.read()
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Online TTS failed: {e}")
            # Try offline TTS as final fallback
            if self.engine:
                return await self._offline_tts(text, slow)
            return b""
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get list of available voices"""
        voices = {}
        
        if self.engine:
            engine_voices = self.engine.getProperty('voices')
            for voice in engine_voices:
                lang_code = self._extract_lang_code(voice.name)
                voices[lang_code] = voice.name
        
        return voices
    
    def _extract_lang_code(self, voice_name: str) -> str:
        """Extract language code from voice name"""
        voice_name_lower = voice_name.lower()
        if 'hindi' in voice_name_lower:
            return 'hi'
        elif 'english' in voice_name_lower:
            return 'en'
        elif 'bengali' in voice_name_lower:
            return 'bn'
        else:
            return 'en'  # Default to English
