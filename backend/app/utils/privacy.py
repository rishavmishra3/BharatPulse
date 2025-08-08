import hashlib
import os
from cryptography.fernet import Fernet
from typing import Dict, Any
import re

class PrivacyService:
    def __init__(self):
        # Generate or load encryption key
        self.key = self._get_or_generate_key()
        self.cipher_suite = Fernet(self.key)
        
        # PII patterns for detection
        self.pii_patterns = {
            'phone': r'(\+91|91|0)?[-\s]?[6-9]\d{9}',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'aadhaar': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'pan': r'\b[A-Z]{5}\d{4}[A-Z]\b'
        }
    
    def _get_or_generate_key(self) -> bytes:
        """Get existing key or generate new one"""
        key_file = "encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in survey response"""
        encrypted_data = data.copy()
        
        sensitive_fields = ['name', 'phone', 'address', 'email']
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                original_value = str(encrypted_data[field])
                encrypted_value = self.cipher_suite.encrypt(
                    original_value.encode()
                ).decode()
                encrypted_data[field] = encrypted_value
        
        return encrypted_data
    
    def decrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields"""
        decrypted_data = data.copy()
        
        sensitive_fields = ['name', 'phone', 'address', 'email']
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    encrypted_value = decrypted_data[field].encode()
                    decrypted_value = self.cipher_suite.decrypt(encrypted_value).decode()
                    decrypted_data[field] = decrypted_value
                except:
                    # If decryption fails, keep original value
                    pass
        
        return decrypted_data
    
    def anonymize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize PII in survey response"""
        anonymized = response.copy()
        
        # Generate anonymous ID based on original data
        if 'name' in anonymized:
            name_hash = hashlib.sha256(
                str(anonymized['name']).encode()
            ).hexdigest()[:8]
            anonymized['respondent_id'] = f"RESP_{name_hash}"
            del anonymized['name']
        
        # Remove or hash other PII
        if 'phone' in anonymized:
            phone_hash = hashlib.sha256(
                str(anonymized['phone']).encode()
            ).hexdigest()[:6]
            anonymized['phone_hash'] = phone_hash
            del anonymized['phone']
        
        # Detect and mask PII in text responses
        for key, value in anonymized.items():
            if isinstance(value, str):
                anonymized[key] = self._mask_pii_in_text(value)
        
        return anonymized
    
    def _mask_pii_in_text(self, text: str) -> str:
        """Mask PII patterns in free text"""
        masked_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            masked_text = re.sub(pattern, f'[{pii_type.upper()}_MASKED]', masked_text)
        
        return masked_text
    
    def generate_consent_text(self, lang: str = "hi") -> str:
        """Generate consent text in specified language"""
        consent_texts = {
            "hi": """
            डेटा सुरक्षा और गोपनीयता सहमति:
            
            • आपकी जानकारी सुरक्षित रखी जाएगी
            • व्यक्तिगत पहचान छुपाई जाएगी  
            • डेटा केवल सर्वेक्षण के लिए उपयोग होगा
            • आप कभी भी अपनी सहमति वापस ले सकते हैं
            
            क्या आप इस सर्वेक्षण में भाग लेना चाहते हैं?
            """,
            
            "en": """
            Data Security and Privacy Consent:
            
            • Your information will be kept secure
            • Personal identity will be anonymized
            • Data will only be used for survey purposes  
            • You can withdraw consent anytime
            
            Do you agree to participate in this survey?
            """
        }
        
        return consent_texts.get(lang, consent_texts["en"])
