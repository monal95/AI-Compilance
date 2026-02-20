import re
import logging
import os
import shutil
from io import BytesIO
from typing import Optional, Tuple

import pytesseract
from PIL import Image, ImageEnhance, ImageOps
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Common Tesseract installation paths on Windows
WINDOWS_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Tesseract-OCR\tesseract.exe",
    r"C:\tesseract\tesseract.exe",
]


def find_tesseract_path() -> Optional[str]:
    """Auto-detect Tesseract installation path."""
    # First check if it's in PATH
    tesseract_in_path = shutil.which("tesseract")
    if tesseract_in_path:
        return tesseract_in_path
    
    # Check common Windows installation paths
    for path in WINDOWS_TESSERACT_PATHS:
        if os.path.isfile(path):
            return path
    
    return None


class OCRSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    tesseract_cmd: Optional[str] = None


def clean_ocr_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


class OCRService:
    def __init__(self) -> None:
        settings = OCRSettings()
        
        # Use env var if set, otherwise auto-detect
        tesseract_path = settings.tesseract_cmd or find_tesseract_path()
        
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"Tesseract configured at: {tesseract_path}")
        else:
            logger.warning("Tesseract OCR not found. OCR features will be disabled.")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy"""
        try:
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Resize if too small (improves OCR accuracy)
            width, height = image.size
            if width < 300 or height < 300:
                scale_factor = max(300 / width, 300 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            image = ImageOps.grayscale(image)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Enhance brightness
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            return image
        except Exception as e:
            logger.warning(f"Error during image preprocessing: {e}")
            return image

    def extract_text(self, image_bytes: bytes) -> str:
        try:
            image = Image.open(BytesIO(image_bytes))
        except Exception as e:
            logger.error(f"Error opening image: {e}")
            return ""

        try:
            # Preprocess the image
            image = self._preprocess_image(image)
            
            # Extract text using Tesseract
            raw_text = pytesseract.image_to_string(image, lang="eng+hin")
            cleaned_text = clean_ocr_text(raw_text)
            
            if not cleaned_text:
                logger.warning("OCR extracted empty text from image")
            else:
                logger.info(f"OCR successfully extracted {len(cleaned_text)} characters")
            
            return cleaned_text
            
        except pytesseract.pytesseract.TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR not found. Please install it from https://github.com/UB-Mannheim/tesseract/wiki")
            return ""
        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")
            return ""
