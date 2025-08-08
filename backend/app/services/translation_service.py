from transformers import MarianMTModel, MarianTokenizer
import json
import re
from typing import Dict, Optional

class TranslationService:
    def __init__(self):
        # Load dialect mappings
        with open("data/dialect_mappings.json", "r", encoding="utf-8") as f:
            self.dialect_mappings = json.load(f)
            
        # Load MarianMT models
        self.models = {}
        self.tokenizers = {}
        
        # Load Hindi-English model
        model_name = "Helsinki-NLP/opus-mt-hi-en"
        self.models["hi-en"] = MarianMTModel.from_pretrained(model_name)
        self.tokenizers["hi-en"] = MarianTokenizer.from_pretrained(model_name)
    
    def map_dialect_to_standard(self, text: str, source_dialect: str) -> str:
        """Map dialectal words to standard Hindi/English"""
        mapped_text = text
        
        if source_dialect in self.dialect_mappings:
            dialect_dict = self.dialect_mappings[source_dialect]
            
            for dialect_word, standard_word in dialect_dict.items():
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(dialect_word) + r'\b'
                mapped_text = re.sub(pattern, standard_word, mapped_text, flags=re.IGNORECASE)
        
        return mapped_text
    
    async def translate_to_standard(self, text: str, source_lang: str, target_lang: str = "hi") -> Dict:
        """Translate text to standard language"""
        try:
            # First map dialect to standard
            if source_lang in ["bhojpuri", "marwari", "awadhi"]:
                mapped_text = self.map_dialect_to_standard(text, source_lang)
            else:
                mapped_text = text
            
            # If already in target language, return as-is
            if source_lang == target_lang:
                return {
                    "original": text,
                    "translated": mapped_text,
                    "confidence": 0.9,
                    "method": "dialect_mapping"
                }
            
            # Use neural translation if model available
            model_key = f"{source_lang}-{target_lang}"
            if model_key in self.models:
                translated = await self._neural_translate(mapped_text, model_key)
                return {
                    "original": text,
                    "translated": translated,
                    "confidence": 0.8,
                    "method": "neural"
                }
            
            # Fallback to dictionary-based translation
            return {
                "original": text,
                "translated": mapped_text,
                "confidence": 0.6,
                "method": "dictionary"
            }
            
        except Exception as e:
            return {
                "original": text,
                "translated": text,
                "confidence": 0.1,
                "error": str(e)
            }
    
    async def _neural_translate(self, text: str, model_key: str) -> str:
        """Perform neural translation"""
        model = self.models[model_key]
        tokenizer = self.tokenizers[model_key]
        
        # Tokenize and translate
        tokens = tokenizer.encode(text, return_tensors="pt")
        translated_tokens = model.generate(tokens, max_length=100)
        translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
        
        return translated_text
