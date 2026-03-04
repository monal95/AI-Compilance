"""
NLP Service for entity extraction and text normalization.

Handles:
- Named entity recognition for product compliance
- Text normalization and cleaning
- Pattern matching for regulatory fields
- Multi-language text processing
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from entity_extractor import EntityExtractor
from text_normalizer import TextNormalizer
from pattern_matcher import PatternMatcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NLP Service",
    description="Entity extraction and text normalization for product compliance",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
entity_extractor = EntityExtractor()
normalizer = TextNormalizer()
pattern_matcher = PatternMatcher()


# Request/Response models
class TextRequest(BaseModel):
    text: str
    language: str = "english"


class EntityResponse(BaseModel):
    entities: dict
    normalized_text: str
    confidence: float


class NormalizeRequest(BaseModel):
    text: str
    language: str = "english"
    remove_special_chars: bool = True
    lowercase: bool = False


class PatternMatchRequest(BaseModel):
    text: str
    patterns: Optional[list[str]] = None
    extract_all: bool = True


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nlp-service"}


@app.post("/nlp/extract-entities", response_model=EntityResponse)
async def extract_entities(request: TextRequest):
    """
    Extract compliance-related entities from text.
    
    Returns:
    - FSSAI numbers
    - Dates (manufacturing, expiry)
    - Prices (MRP)
    - Weights/Quantities
    - Addresses
    - Contact information
    """
    try:
        # Normalize text first
        normalized = normalizer.normalize(
            request.text, 
            language=request.language
        )
        
        # Extract entities
        entities = entity_extractor.extract_all(normalized)
        
        # Calculate average confidence
        confidences = []
        for entity_type, entity_data in entities.items():
            if entity_data and isinstance(entity_data, dict) and 'confidence' in entity_data:
                conf_value = entity_data['confidence']
                if conf_value == 'high':
                    confidences.append(0.9)
                elif conf_value == 'medium':
                    confidences.append(0.7)
                else:
                    confidences.append(0.5)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        return EntityResponse(
            entities=entities,
            normalized_text=normalized,
            confidence=avg_confidence
        )
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nlp/normalize")
async def normalize_text(request: NormalizeRequest):
    """Normalize and clean text."""
    try:
        result = normalizer.normalize(
            request.text,
            language=request.language,
            remove_special_chars=request.remove_special_chars,
            lowercase=request.lowercase
        )
        
        return {
            "original": request.text,
            "normalized": result,
            "changes_made": normalizer.get_changes_summary()
        }
    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nlp/match-patterns")
async def match_patterns(request: PatternMatchRequest):
    """
    Match predefined or custom regex patterns in text.
    
    If extract_all is True, uses predefined compliance patterns.
    Otherwise, uses the patterns provided in the request.
    """
    try:
        if request.extract_all:
            matches = pattern_matcher.match_all_patterns(request.text)
        else:
            if not request.patterns:
                raise HTTPException(
                    status_code=400, 
                    detail="Patterns required when extract_all is False"
                )
            matches = pattern_matcher.match_custom_patterns(
                request.text, 
                request.patterns
            )
        
        return {
            "text": request.text,
            "matches": matches,
            "patterns_matched": sum(1 for m in matches.values() if m)
        }
    except Exception as e:
        logger.error(f"Pattern matching failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nlp/analyze")
async def analyze_text(request: TextRequest):
    """
    Comprehensive text analysis combining all NLP features.
    
    Returns normalized text, extracted entities, and pattern matches.
    """
    try:
        # Normalize
        normalized = normalizer.normalize(request.text, request.language)
        
        # Extract entities
        entities = entity_extractor.extract_all(normalized)
        
        # Pattern matches
        patterns = pattern_matcher.match_all_patterns(normalized)
        
        # Calculate completeness
        total_fields = 8
        fields_found = sum(1 for e in entities.values() if e is not None)
        completeness = (fields_found / total_fields) * 100
        
        return {
            "original_text": request.text,
            "normalized_text": normalized,
            "language": request.language,
            "entities": entities,
            "pattern_matches": patterns,
            "analysis": {
                "completeness_score": round(completeness, 1),
                "fields_found": fields_found,
                "fields_missing": total_fields - fields_found,
                "word_count": len(normalized.split()),
                "char_count": len(normalized),
            }
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nlp/supported-languages")
async def get_supported_languages():
    """Get list of supported languages."""
    return {
        "languages": normalizer.SUPPORTED_LANGUAGES,
        "default": "english"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
