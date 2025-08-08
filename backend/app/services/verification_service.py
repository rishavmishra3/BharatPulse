import cv2
import numpy as np
from typing import Dict, Optional
import face_recognition
import hashlib
import base64

class VerificationService:
    def __init__(self):
        self.known_encodings = []
        self.known_ids = []
        
    async def verify_respondent(self, image_data: bytes, 
                              respondent_id: str = None) -> Dict:
        """Verify respondent using face recognition"""
        try:
            # Decode image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face encodings
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if not face_encodings:
                return {
                    "verified": False,
                    "confidence": 0.0,
                    "error": "No face detected"
                }
            
            # Use first face encoding
            face_encoding = face_encodings[0]
            
            if respondent_id and self.known_encodings:
                # Check against known faces
                matches = face_recognition.compare_faces(
                    self.known_encodings, face_encoding
                )
                face_distances = face_recognition.face_distance(
                    self.known_encodings, face_encoding
                )
                
                if matches and min(face_distances) < 0.4:  # Good match threshold
                    best_match_index = np.argmin(face_distances)
                    confidence = 1.0 - face_distances[best_match_index]
                    
                    return {
                        "verified": True,
                        "confidence": confidence,
                        "matched_id": self.known_ids[best_match_index],
                        "is_duplicate": True
                    }
            
            # New respondent - store encoding
            respondent_hash = self._generate_respondent_hash(face_encoding)
            self.known_encodings.append(face_encoding)
            self.known_ids.append(respondent_id or respondent_hash)
            
            return {
                "verified": True,
                "confidence": 0.9,
                "respondent_hash": respondent_hash,
                "is_duplicate": False
            }
            
        except Exception as e:
            return {
                "verified": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _generate_respondent_hash(self, face_encoding: np.ndarray) -> str:
        """Generate unique hash for face encoding"""
        # Convert encoding to string and hash
        encoding_str = str(face_encoding.tolist())
        return hashlib.sha256(encoding_str.encode()).hexdigest()[:16]
    
    async def voice_verification(self, audio_data: bytes, 
                               respondent_id: str = None) -> Dict:
        """Basic voice verification using audio features"""
        try:
            # This is a simplified implementation
            # In production, use proper speaker recognition
            
            # Extract basic audio features (placeholder)
            audio_hash = hashlib.sha256(audio_data).hexdigest()[:16]
            
            return {
                "verified": True,
                "confidence": 0.7,
                "voice_hash": audio_hash,
                "method": "audio_fingerprint"
            }
            
        except Exception as e:
            return {
                "verified": False,
                "confidence": 0.0,
                "error": str(e)
            }
