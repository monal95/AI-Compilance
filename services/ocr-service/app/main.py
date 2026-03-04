"""
OCR Service - Image Processing & Multi-Language OCR Microservice

Provides:
- OpenCV preprocessing (denoise, grayscale, thresholding)
- Multi-language OCR support (English + Indian languages)
- Field extraction from product images
"""
import uuid
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
import base64

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(__file__).replace("services/ocr-service/app/main.py", ""))

from shared.utils.logger import setup_logging, get_logger

# Import local modules
from preprocessor import ImagePreprocessor
from ocr_engine import OCREngine
from field_extractor import FieldExtractor

# Setup logging
setup_logging("ocr-service", level="INFO")
logger = get_logger(__name__)


# Request/Response Models
class OCRRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    languages: list[str] = Field(default=["eng"])
    preprocess: bool = True
    extract_fields: bool = True
    category: Optional[str] = None


class OCRRegion(BaseModel):
    text: str
    confidence: float
    bbox: list[int]  # [x, y, width, height]


class OCRResponse(BaseModel):
    request_id: str
    status: str
    raw_text: str
    confidence: float
    languages_detected: list[str]
    regions: list[OCRRegion]
    extracted_fields: dict
    processing_time_ms: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting OCR Service...")
    logger.info("OCR Service started successfully")
    yield
    logger.info("Shutting down OCR Service...")


app = FastAPI(
    title="OCR Service",
    description="Image processing and multi-language OCR microservice",
    version="1.0.0",
    lifespan=lifespan,
)


# Service instances
preprocessor = ImagePreprocessor()
ocr_engine = OCREngine()
field_extractor = FieldExtractor()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "service": "ocr-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "tesseract_available": ocr_engine.is_available(),
        "supported_languages": ocr_engine.get_supported_languages(),
    }


@app.post("/ocr/process", response_model=OCRResponse)
async def process_ocr(
    image: UploadFile = File(None),
    image_url: str = Form(None),
    image_base64: str = Form(None),
    languages: str = Form("eng"),
    preprocess: bool = Form(True),
    extract_fields: bool = Form(True),
    category: str = Form(None),
):
    """
    Process an image for OCR extraction.
    
    Supports:
    - File upload
    - Image URL
    - Base64 encoded image
    
    Languages supported:
    - eng: English
    - hin: Hindi
    - tam: Tamil
    - tel: Telugu
    - kan: Kannada
    - mar: Marathi
    - ben: Bengali
    """
    import time
    start_time = time.time()
    
    request_id = str(uuid.uuid4())
    
    # Get image bytes
    image_bytes = None
    
    if image:
        image_bytes = await image.read()
    elif image_url:
        image_bytes = await ocr_engine.fetch_image_from_url(image_url)
    elif image_base64:
        image_bytes = base64.b64decode(image_base64)
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide image file, URL, or base64 encoded image"
        )
    
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Failed to load image")
    
    # Parse languages
    lang_list = [lang.strip() for lang in languages.split(",")]
    
    try:
        # Preprocess image
        if preprocess:
            processed_images = preprocessor.preprocess(image_bytes)
        else:
            processed_images = [image_bytes]
        
        # Run OCR on all preprocessed versions
        best_result = None
        best_confidence = 0
        
        for processed in processed_images:
            result = ocr_engine.extract_text(processed, lang_list)
            if result["confidence"] > best_confidence:
                best_confidence = result["confidence"]
                best_result = result
        
        # Extract fields if requested
        extracted_fields = {}
        if extract_fields and best_result:
            extracted_fields = field_extractor.extract_fields(
                best_result["text"],
                category=category,
            )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return OCRResponse(
            request_id=request_id,
            status="success",
            raw_text=best_result["text"] if best_result else "",
            confidence=best_confidence,
            languages_detected=best_result.get("languages", lang_list) if best_result else [],
            regions=best_result.get("regions", []) if best_result else [],
            extracted_fields=extracted_fields,
            processing_time_ms=processing_time,
        )
    
    except Exception as e:
        logger.error(f"OCR processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@app.post("/ocr/batch")
async def batch_ocr(
    images: list[UploadFile] = File(...),
    languages: str = Form("eng"),
    preprocess: bool = Form(True),
    category: str = Form(None),
):
    """
    Process multiple images for OCR extraction.
    """
    results = []
    
    for image in images:
        try:
            image_bytes = await image.read()
            
            # Parse languages
            lang_list = [lang.strip() for lang in languages.split(",")]
            
            # Preprocess
            if preprocess:
                processed_images = preprocessor.preprocess(image_bytes)
            else:
                processed_images = [image_bytes]
            
            # OCR
            best_result = None
            best_confidence = 0
            
            for processed in processed_images:
                result = ocr_engine.extract_text(processed, lang_list)
                if result["confidence"] > best_confidence:
                    best_confidence = result["confidence"]
                    best_result = result
            
            # Extract fields
            extracted_fields = field_extractor.extract_fields(
                best_result["text"] if best_result else "",
                category=category,
            )
            
            results.append({
                "filename": image.filename,
                "status": "success",
                "text": best_result["text"] if best_result else "",
                "confidence": best_confidence,
                "fields": extracted_fields,
            })
        
        except Exception as e:
            results.append({
                "filename": image.filename,
                "status": "failed",
                "error": str(e),
            })
    
    return {
        "total": len(images),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "results": results,
    }


@app.get("/ocr/languages")
async def list_supported_languages():
    """List all supported OCR languages."""
    return {
        "languages": ocr_engine.get_supported_languages(),
        "default": "eng",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
