import torch
import whisper
import librosa
import numpy as np
import json
import asyncio
import io
import os
from typing import Optional, Dict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        try:
            # Load Whisper tiny for offline use
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("tiny")
            logger.info("✅ Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            self.whisper_model = None
        
        # Initialize Vosk as fallback
        self.vosk_model = None
        self.recognizer = None
        self._init_vosk()
            
        self.supported_langs = ["hi", "en", "bn", "ta", "te", "mr", "gu"]
    
    def _init_vosk(self):
        """Initialize Vosk model as fallback"""
        try:
            from vosk import Model, KaldiRecognizer
            vosk_path = os.getenv("VOSK_MODEL_PATH", "./models/vosk/")
            if os.path.exists(vosk_path):
                self.vosk_model = Model(vosk_path)
                self.recognizer = KaldiRecognizer(self.vosk_model, 16000)
                logger.info("✅ Vosk model loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ Vosk model not available: {e}")
    
    async def transcribe(self, audio_data: bytes, lang: str = "hi") -> Dict:
        """Transcribe audio to text with language detection"""
        try:
            if not self.whisper_model:
                return {
                    "text": "",
                    "language": lang,
                    "confidence": 0.0,
                    "success": False,
                    "error": "Whisper model not loaded"
                }
            
            # Convert audio bytes to numpy array
            audio_array = await self._bytes_to_audio_array(audio_data)
            
            # Use Whisper for transcription
            result = self.whisper_model.transcribe(
                audio_array, 
                language=lang if lang in self.supported_langs else None
            )
            
            detected_lang = result.get("language", lang)
            text = result["text"].strip()
            confidence = self._calculate_confidence(result)
            
            return {
                "text": text,
                "language": detected_lang,
                "confidence": confidence,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            
            # Fallback to Vosk if available
            if self.vosk_model and self.recognizer:
                return await self._vosk_transcribe(audio_data)
            
            return {
                "text": "",
                "language": lang,
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }
    
    async def _bytes_to_audio_array(self, audio_bytes: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array for Whisper"""
        try:
            # Create a BytesIO object from audio bytes
            audio_io = io.BytesIO(audio_bytes)
            
            # Load audio using librosa
            audio, sr = librosa.load(audio_io, sr=16000, mono=True)
            return audio
            
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            # Return empty array as fallback
            return np.array([])
    
    def _calculate_confidence(self, whisper_result: Dict) -> float:
        """Calculate confidence score from Whisper result"""
        try:
            segments = whisper_result.get("segments", [])
            if not segments:
                return 0.5
            
            # Calculate average confidence from segments
            total_confidence = 0
            total_duration = 0
            
            for segment in segments:
                duration = segment.get("end", 0) - segment.get("start", 0)
                if duration > 0:
                    # Convert log probability to confidence (0-1 scale)
                    logprob = segment.get("avg_logprob", -1.0)
                    confidence = max(0.1, min(1.0, np.exp(logprob)))
                    
                    total_confidence += confidence * duration
                    total_duration += duration
            
            if total_duration > 0:
                return total_confidence / total_duration
            return 0.5
            
        except Exception as e:
            logger.warning(f"Confidence calculation error: {e}")
            return 0.5
    
    async def _vosk_transcribe(self, audio_data: bytes) -> Dict:
        """Fallback transcription using Vosk"""
        try:
            audio_array = await self._bytes_to_audio_array(audio_data)
            
            # Convert to the right format for Vosk
            audio_int16 = (audio_array * 32768).astype(np.int16)
            
            # Process audio with Vosk
            if self.recognizer.AcceptWaveform(audio_int16.tobytes()):
                result = json.loads(self.recognizer.Result())
            else:
                result = json.loads(self.recognizer.PartialResult())
            
            return {
                "text": result.get("text", ""),
                "language": "hi",
                "confidence": result.get("confidence", 0.5),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Vosk transcription error: {e}")
            return {
                "text": "",
                "language": "hi",
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }
