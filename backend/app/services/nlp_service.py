import re
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self):
        self.nlp_hi = None
        self.nlp_en = None
        self._init_spacy()
        
        # Custom patterns for common survey fields
        self.patterns = {
            "age": [
                r"(\d+)\s*(?:साल|वर्ष|years?|yr|साल|वर्ष)",
                r"(?:उम्र|age|आयु)\s*(\d+)",
                r"मैं\s*(\d+)\s*(?:का|की|के)\s*हूँ?",
                r"(\d+)\s*(?:बरस|साल)\s*(?:का|की|के)",
            ],
            "income": [
                r"(\d+(?:,\d+)*)\s*(?:रुपए|रुपये|rupees?|rs|₹)",
                r"(?:कमाई|income|आय|तनख्वाह|पैसा)\s*(\d+(?:,\d+)*)",
                r"महीने\s*में\s*(\d+(?:,\d+)*)",
                r"(\d+(?:,\d+)*)\s*(?:प्रति|per)\s*(?:महीना|month)",
            ],
            "occupation": [
                r"(?:काम|job|work|नौकरी|धंधा)\s*(.+?)(?:\s+|$)",
                r"(?:व्यवसाय|business|पेशा)\s*(.+?)(?:\s+|$)",
                r"मैं\s*(.+?)\s*(?:करता|करती)\s*हूँ?",
                r"(\w+)\s*(?:का|के)\s*काम\s*करता",
            ],
            "location": [
                r"(?:रहता|रहती|रहते)\s*(?:हूँ|हैं)\s*(.+?)(?:\s+में|$)",
                r"(?:घर|निवास|address)\s*(.+?)(?:\s+|$)",
                r"(.+?)\s*(?:गांव|शहर|जिला|village|city|district)",
                r"मैं\s*(.+?)\s*(?:में|से)\s*हूँ",
            ],
            "name": [
                r"(?:नाम|name)\s*(.+?)(?:\s+है|$)",
                r"मैं\s*(.+?)\s*हूँ",
                r"मेरा\s*नाम\s*(.+?)(?:\s+है|$)",
                r"(.+?)\s*(?:नाम|कहलाता|कहलाती)\s*(?:है|हूँ)",
            ]
        }
    
    def _init_spacy(self):
        """Initialize spaCy models"""
        try:
            import spacy
            
            # Try loading Hindi model (will fail - that's okay)
            try:
                self.nlp_hi = spacy.load("hi_core_news_sm")
                logger.info("✅ Hindi spaCy model loaded")
            except:
                logger.warning("⚠️ Hindi spaCy model not found - using English fallback")
                self.nlp_hi = None  # Set to None, will use English
            
            # Load English model as fallback
            try:
                self.nlp_en = spacy.load("en_core_web_sm")
                logger.info("✅ English spaCy model loaded")
            except:
                logger.error("❌ English spaCy model not found")
                self.nlp_en = None
                
        except ImportError:
            logger.error("❌ spaCy not installed")
            self.nlp_hi = None
            self.nlp_en = None

    
    async def extract_fields(self, text: str, question_id: str = None) -> Dict:
        """Extract structured data from natural language text"""
        try:
            if not text or not text.strip():
                return {
                    "extracted_data": {},
                    "confidence": 0.0,
                    "success": False,
                    "error": "Empty text provided"
                }
            
            text = text.strip()
            
            # Determine language
            lang = self._detect_language(text)
            nlp = self.nlp_hi if lang == "hi" and self.nlp_hi else self.nlp_en
            
            # Extract using spaCy if available
            entities = {}
            if nlp:
                doc = nlp(text)
                entities = self._extract_entities(doc)
            
            # Extract using custom patterns
            pattern_matches = self._extract_with_patterns(text)
            
            # Combine results (pattern matches take priority)
            extracted_data = {**entities, **pattern_matches}
            
            # Calculate overall confidence
            confidence = self._calculate_extraction_confidence(
                text, extracted_data, question_id
            )
            
            # Clean and validate extracted data
            cleaned_data = self._clean_extracted_data(extracted_data)
            
            return {
                "extracted_data": cleaned_data,
                "confidence": confidence,
                "text_processed": text,
                "language": lang,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Field extraction error: {e}")
            return {
                "extracted_data": {},
                "confidence": 0.0,
                "error": str(e),
                "success": False
            }
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on script"""
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if hindi_chars > latin_chars:
            return "hi"
        return "en"
    
    def _extract_entities(self, doc) -> Dict:
        """Extract named entities using spaCy"""
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) <= 3:
                entities["name"] = ent.text.strip()
            elif ent.label_ in ["GPE", "LOC"]:
                if "location" not in entities:
                    entities["location"] = []
                if isinstance(entities["location"], list):
                    entities["location"].append(ent.text.strip())
                else:
                    entities["location"] = [entities["location"], ent.text.strip()]
            elif ent.label_ in ["MONEY", "CURRENCY"]:
                money_val = self._normalize_money(ent.text)
                if money_val:
                    entities["income"] = money_val
            elif ent.label_ in ["DATE", "TIME"]:
                entities["date"] = ent.text.strip()
        
        # Clean location if it's a list
        if "location" in entities and isinstance(entities["location"], list):
            if len(entities["location"]) == 1:
                entities["location"] = entities["location"][0]
            else:
                entities["location"] = ", ".join(entities["location"])
        
        return entities
    
    def _extract_with_patterns(self, text: str) -> Dict:
        """Extract using regex patterns"""
        extracted = {}
        
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    match_text = matches[0].strip()
                    
                    if field == "age":
                        try:
                            age_val = int(match_text)
                            if 5 <= age_val <= 120:  # Reasonable age range
                                extracted[field] = age_val
                        except:
                            continue
                            
                    elif field == "income":
                        income_val = self._normalize_money(match_text)
                        if income_val and income_val > 0:
                            extracted[field] = income_val
                            
                    elif field in ["name", "occupation", "location"]:
                        # Clean the extracted text
                        cleaned = self._clean_text_field(match_text)
                        if cleaned and len(cleaned.split()) <= 10:  # Reasonable length
                            extracted[field] = cleaned
                    
                    break  # Stop after first successful match for this field
        
        return extracted
    
    def _clean_text_field(self, text: str) -> str:
        """Clean extracted text fields"""
        # Remove extra whitespace and common noise words
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove trailing punctuation
        text = re.sub(r'[।,.\-!?]+$', '', text)
        
        # Remove common filler words at the start/end
        noise_patterns = [
            r'^(?:मैं\s+|है\s+|का\s+|की\s+|के\s+|हूँ\s*)',
            r'\s*(?:है|हूँ|करता|करती|हैं)$'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _normalize_money(self, money_text: str) -> Optional[int]:
        """Normalize money mentions to integer"""
        if not money_text:
            return None
            
        # Remove currency symbols and extract numbers
        cleaned = re.sub(r'[^\d,]', '', str(money_text))
        cleaned = cleaned.replace(',', '')
        
        try:
            value = int(cleaned)
            # Reasonable income range (monthly in INR)
            if 1000 <= value <= 10000000:  # 1K to 1Crore
                return value
        except:
            pass
        
        return None
    
    def _calculate_extraction_confidence(self, text: str, 
                                       extracted: Dict, question_id: str = None) -> float:
        """Calculate confidence score for extraction"""
        confidence_factors = []
        
        # Base confidence based on extraction success
        if extracted:
            confidence_factors.append(0.7)
        else:
            return 0.1
        
        # Text length factor (more text usually means better extraction)
        word_count = len(text.split())
        if word_count >= 3:
            confidence_factors.append(0.8)
        elif word_count >= 2:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)
        
        # Field-specific confidence
        for field, value in extracted.items():
            if field == "age" and isinstance(value, int):
                confidence_factors.append(0.9)
            elif field == "income" and isinstance(value, int):
                confidence_factors.append(0.8)
            elif field in ["name", "location", "occupation"] and isinstance(value, str):
                if len(value.split()) <= 5:  # Reasonable length
                    confidence_factors.append(0.8)
                else:
                    confidence_factors.append(0.6)
        
        # Question-specific boost
        if question_id:
            if question_id == "age" and "age" in extracted:
                confidence_factors.append(0.9)
            elif question_id == "income" and "income" in extracted:
                confidence_factors.append(0.9)
            elif question_id == "name" and "name" in extracted:
                confidence_factors.append(0.9)
        
        # Calculate final confidence
        if confidence_factors:
            return min(1.0, sum(confidence_factors) / len(confidence_factors))
        return 0.1
    
    def _clean_extracted_data(self, data: Dict) -> Dict:
        """Clean and validate extracted data"""
        cleaned = {}
        
        for key, value in data.items():
            if value is None:
                continue
                
            if key == "age" and isinstance(value, int):
                if 5 <= value <= 120:
                    cleaned[key] = value
                    
            elif key == "income" and isinstance(value, int):
                if value > 0:
                    cleaned[key] = value
                    
            elif key in ["name", "location", "occupation"]:
                if isinstance(value, str):
                    clean_val = value.strip()
                    if clean_val and len(clean_val.split()) <= 10:
                        cleaned[key] = clean_val
                        
            else:
                cleaned[key] = value
        
        return cleaned
    
    async def validate_extraction(self, extracted_data: Dict, 
                                question_type: str) -> Dict:
        """Validate extracted data against expected question type"""
        validation_result = {
            "is_valid": True,
            "confidence": 1.0,
            "errors": []
        }
        
        if question_type == "age" and "age" in extracted_data:
            age = extracted_data["age"]
            if not isinstance(age, int) or not (5 <= age <= 120):
                validation_result["is_valid"] = False
                validation_result["errors"].append("Age must be between 5 and 120")
                validation_result["confidence"] = 0.1
        
        elif question_type == "income" and "income" in extracted_data:
            income = extracted_data["income"]
            if not isinstance(income, int) or income <= 0:
                validation_result["is_valid"] = False
                validation_result["errors"].append("Income must be a positive number")
                validation_result["confidence"] = 0.1
        
        elif question_type == "name" and "name" in extracted_data:
            name = extracted_data["name"]
            if not isinstance(name, str) or len(name.strip()) < 2:
                validation_result["is_valid"] = False
                validation_result["errors"].append("Name must be at least 2 characters")
                validation_result["confidence"] = 0.1
        
        return validation_result
