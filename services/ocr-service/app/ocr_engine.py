"""
OCR Engine with multi-language support using Tesseract.

Supported languages:
- English (eng)
- Hindi (hin)
- Tamil (tam)
- Telugu (tel)
- Kannada (kan)
- Marathi (mar)
- Bengali (ben)
- Gujarati (guj)
"""
import logging
import os
from typing import Optional

import pytesseract
from PIL import Image
import io

logger = logging.getLogger(__name__)


class OCREngine:
    """Multi-language OCR engine using Tesseract."""
    
    # Language code mapping
    SUPPORTED_LANGUAGES = {
        "english": "eng",
        "hindi": "hin", 
        "tamil": "tam",
        "telugu": "tel",
        "kannada": "kan",
        "marathi": "mar",
        "bengali": "ben",
        "gujarati": "guj",
        "punjabi": "pan",
        "malayalam": "mal",
        "odia": "ori",
        "assamese": "asm",
        "sanskrit": "san",
        "urdu": "urd",
        "nepali": "nep",
    }
    
    # Indian regulatory text often contains these
    DEFAULT_LANGUAGES = ["eng", "hin"]
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR engine.
        
        Args:
            tesseract_path: Custom path to Tesseract executable (Windows)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif os.name == 'nt':  # Windows
            # Common Windows installation paths
            paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Tesseract-OCR\tesseract.exe",
            ]
            for path in paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        
        self._verify_tesseract()
        self.available_languages = self._get_available_languages()
    
    def _verify_tesseract(self):
        """Verify Tesseract is installed and accessible."""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            logger.error(f"Tesseract not found: {e}")
            raise RuntimeError(
                "Tesseract OCR is not installed or not in PATH. "
                "Please install Tesseract and ensure it's accessible."
            )
    
    def _get_available_languages(self) -> list[str]:
        """Get list of installed Tesseract languages."""
        try:
            languages = pytesseract.get_languages()
            logger.info(f"Available OCR languages: {languages}")
            return languages
        except Exception as e:
            logger.warning(f"Could not get language list: {e}")
            return ["eng"]  # Assume English is available
    
    def get_supported_languages(self) -> dict:
        """Return supported languages with their availability status."""
        return {
            name: {
                "code": code,
                "available": code in self.available_languages
            }
            for name, code in self.SUPPORTED_LANGUAGES.items()
        }
    
    def _build_language_string(self, languages: list[str]) -> str:
        """Build Tesseract language string (e.g., 'eng+hin+tam')."""
        # Filter to only available languages
        valid_langs = [
            lang for lang in languages 
            if lang in self.available_languages
        ]
        
        if not valid_langs:
            logger.warning(f"None of requested languages {languages} are available, using English")
            valid_langs = ["eng"]
        
        return "+".join(valid_langs)
    
    def extract_text(
        self,
        image_bytes: bytes,
        languages: Optional[list[str]] = None,
        psm: int = 3,
    ) -> dict:
        """
        Extract text from image.
        
        Args:
            image_bytes: Image data as bytes
            languages: List of language codes to use
            psm: Page segmentation mode (default: 3 - fully automatic)
                 PSM modes:
                 0 - Orientation and script detection only
                 1 - Automatic page segmentation with OSD
                 3 - Fully automatic (default)
                 4 - Single column of text
                 6 - Single uniform block of text
                 7 - Single text line
                 11 - Sparse text
                 13 - Raw line
        
        Returns:
            Dict with 'text', 'confidence', 'details'
        """
        if languages is None:
            languages = self.DEFAULT_LANGUAGES
        
        lang_string = self._build_language_string(languages)
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Configure Tesseract
            config = f"--psm {psm} --oem 3"
            
            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=lang_string,
                config=config
            )
            
            # Get detailed data with confidence scores
            data = pytesseract.image_to_data(
                image,
                lang=lang_string,
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence (excluding -1 values)
            confidences = [
                c for c in data['conf'] 
                if isinstance(c, (int, float)) and c >= 0
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract word-level details
            words = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    words.append({
                        'text': data['text'][i],
                        'confidence': data['conf'][i],
                        'box': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i],
                        },
                        'block': data['block_num'][i],
                        'line': data['line_num'][i],
                    })
            
            result = {
                'text': text.strip(),
                'confidence': round(avg_confidence, 2),
                'languages_used': lang_string,
                'word_count': len(words),
                'details': {
                    'words': words,
                    'blocks': max(data['block_num']) if data['block_num'] else 0,
                    'lines': max(data['line_num']) if data['line_num'] else 0,
                }
            }
            
            logger.info(
                f"OCR extracted {len(words)} words with {avg_confidence:.1f}% confidence"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise
    
    def extract_with_multiple_modes(
        self,
        image_bytes: bytes,
        languages: Optional[list[str]] = None,
    ) -> dict:
        """
        Try multiple PSM modes and return best result.
        
        Useful for images with unknown layout.
        """
        modes_to_try = [3, 6, 4, 11]  # Automatic, block, column, sparse
        best_result = None
        best_confidence = -1
        
        for psm in modes_to_try:
            try:
                result = self.extract_text(image_bytes, languages, psm=psm)
                if result['confidence'] > best_confidence and result['text']:
                    best_confidence = result['confidence']
                    best_result = result
                    best_result['psm_mode'] = psm
            except Exception as e:
                logger.debug(f"PSM mode {psm} failed: {e}")
                continue
        
        if best_result is None:
            raise RuntimeError("All OCR modes failed")
        
        logger.info(f"Best OCR result from PSM mode {best_result.get('psm_mode', 3)}")
        return best_result
    
    def detect_orientation(self, image_bytes: bytes) -> dict:
        """Detect image orientation and script."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
            return {
                'orientation': osd.get('orientation', 0),
                'rotation': osd.get('rotate', 0),
                'script': osd.get('script', 'Latin'),
                'confidence': osd.get('orientation_conf', 0),
            }
        except Exception as e:
            logger.warning(f"Orientation detection failed: {e}")
            return {
                'orientation': 0,
                'rotation': 0,
                'script': 'Unknown',
                'confidence': 0,
            }
    
    def extract_from_multiple_versions(
        self,
        image_versions: list[bytes],
        languages: Optional[list[str]] = None,
    ) -> dict:
        """
        Extract text from multiple preprocessed versions of an image.
        Returns the result with highest confidence.
        
        This is useful when combined with ImagePreprocessor.preprocess()
        which returns multiple versions of the image.
        """
        best_result = None
        best_confidence = -1
        
        for i, img_bytes in enumerate(image_versions):
            try:
                result = self.extract_text(img_bytes, languages)
                if result['confidence'] > best_confidence and result['text']:
                    best_confidence = result['confidence']
                    best_result = result
                    best_result['version_index'] = i
            except Exception as e:
                logger.debug(f"Version {i} OCR failed: {e}")
                continue
        
        if best_result is None:
            raise RuntimeError("OCR failed on all image versions")
        
        logger.info(
            f"Best OCR from version {best_result.get('version_index', 0)} "
            f"with {best_confidence:.1f}% confidence"
        )
        return best_result
