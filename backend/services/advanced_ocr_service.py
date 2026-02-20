"""
Advanced OCR Microservice with Bounding Box Region Segmentation

Production-ready service for AI-powered Legal Metrology Compliance Monitoring.
Uses region-based OCR for improved accuracy and structured field extraction.

Features:
- Advanced image preprocessing (grayscale, blur, thresholding, morphological ops)
- Bounding box detection using contour analysis
- Region-wise OCR with confidence scoring
- Structured compliance field extraction (MRP, Net Qty, Dates, etc.)
- Confidence aggregation and quality flagging
"""

import re
import logging
import os
import shutil
from io import BytesIO
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration & Constants
# ============================================================================

WINDOWS_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Tesseract-OCR\tesseract.exe",
    r"C:\tesseract\tesseract.exe",
]

# Minimum confidence threshold for OCR results
MIN_CONFIDENCE_THRESHOLD = 60
LOW_CONFIDENCE_THRESHOLD = 65

# Image preprocessing constants
TARGET_WIDTH = 1200  # Target width for consistent resolution
MIN_CONTOUR_AREA = 100  # Minimum area for text region detection
MAX_CONTOUR_AREA_RATIO = 0.8  # Max ratio of image area for a single contour
MIN_ASPECT_RATIO = 0.1  # Minimum width/height ratio for text regions
MAX_ASPECT_RATIO = 15.0  # Maximum width/height ratio for text regions


class ConfidenceLevel(str, Enum):
    """Confidence level classification for OCR results"""
    HIGH = "HIGH_CONFIDENCE"
    MEDIUM = "MEDIUM_CONFIDENCE"
    LOW = "LOW_CONFIDENCE"
    VERY_LOW = "VERY_LOW_CONFIDENCE"


class ProductCategory(str, Enum):
    """Product categories for compliance field extraction"""
    FOOD = "food"
    ELECTRONICS = "electronics"
    COSMETICS = "cosmetics"
    GENERIC = "generic"


# ============================================================================
# Pydantic Models for API Response
# ============================================================================

class TextRegion(BaseModel):
    """Represents a detected text region with OCR results"""
    x: int
    y: int
    width: int
    height: int
    text: str
    confidence: float
    region_index: int


class ComplianceFields(BaseModel):
    """Structured compliance fields extracted from product labels"""
    mrp: Optional[str] = None
    net_quantity: Optional[str] = None
    manufacture_date: Optional[str] = None
    expiry_date: Optional[str] = None
    country_of_origin: Optional[str] = None
    manufacturer: Optional[str] = None
    importer: Optional[str] = None
    consumer_care: Optional[str] = None
    batch_number: Optional[str] = None
    fssai_license: Optional[str] = None
    bis_certification: Optional[str] = None


class OCRProcessingResult(BaseModel):
    """Complete OCR processing result with structured fields"""
    # Structured fields
    mrp: Optional[str] = None
    net_quantity: Optional[str] = None
    manufacture_date: Optional[str] = None
    expiry_date: Optional[str] = None
    country_of_origin: Optional[str] = None
    manufacturer: Optional[str] = None
    importer: Optional[str] = None
    consumer_care: Optional[str] = None
    batch_number: Optional[str] = None
    fssai_license: Optional[str] = None
    bis_certification: Optional[str] = None
    
    # Confidence metrics
    confidence_score: float = Field(ge=0, le=1)
    confidence_level: ConfidenceLevel
    region_confidences: List[float] = Field(default_factory=list)
    
    # Raw data
    raw_text_regions: List[TextRegion] = Field(default_factory=list)
    combined_text: str = ""
    
    # Processing metadata
    total_regions_detected: int = 0
    regions_processed: int = 0
    low_confidence_regions: int = 0
    processing_time_ms: float = 0
    image_dimensions: Tuple[int, int] = (0, 0)
    
    # Flags
    needs_review: bool = False
    error: Optional[str] = None


class OCRRequest(BaseModel):
    """Request model for OCR processing"""
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    category: Optional[ProductCategory] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/product-label.jpg",
                "category": "food"
            }
        }


# ============================================================================
# Helper Functions
# ============================================================================

def find_tesseract_path() -> Optional[str]:
    """Auto-detect Tesseract installation path."""
    tesseract_in_path = shutil.which("tesseract")
    if tesseract_in_path:
        return tesseract_in_path
    
    for path in WINDOWS_TESSERACT_PATHS:
        if os.path.isfile(path):
            return path
    
    return None


@dataclass
class BoundingBox:
    """Represents a bounding box for a text region"""
    x: int
    y: int
    width: int
    height: int
    area: int = field(init=False)
    
    def __post_init__(self):
        self.area = self.width * self.height
    
    @property
    def center_y(self) -> int:
        return self.y + self.height // 2
    
    @property
    def center_x(self) -> int:
        return self.x + self.width // 2


# ============================================================================
# Advanced OCR Microservice
# ============================================================================

class AdvancedOCRService:
    """
    Production-ready OCR microservice with bounding-box-based region segmentation.
    
    Pipeline:
    1. Image preprocessing (resize, grayscale, blur, threshold, morphology)
    2. Bounding box detection (contour-based)
    3. Region-wise OCR with confidence scoring
    4. Structured field extraction using regex patterns
    5. Confidence aggregation and quality flagging
    """
    
    def __init__(self):
        self._configure_tesseract()
        self._compile_regex_patterns()
    
    def _configure_tesseract(self):
        """Configure Tesseract OCR path"""
        tesseract_path = find_tesseract_path()
        
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"Advanced OCR Service initialized with Tesseract at: {tesseract_path}")
        else:
            logger.warning("Tesseract OCR not found. OCR features will be disabled.")
    
    def _compile_regex_patterns(self):
        """Pre-compile regex patterns for field extraction"""
        self.patterns = {
            # MRP patterns - ₹, Rs., MRP with various formats
            'mrp': re.compile(
                r'(?:MRP|M\.R\.P\.?|Price|PRICE)[\s:₹.]*[₹Rs.]*\s*([0-9,]+(?:\.[0-9]{1,2})?)|'
                r'[₹][\s]*([0-9,]+(?:\.[0-9]{1,2})?)|'
                r'Rs\.?\s*([0-9,]+(?:\.[0-9]{1,2})?)',
                re.IGNORECASE
            ),
            
            # Net quantity - weight/volume units
            'net_quantity': re.compile(
                r'(?:Net\s*(?:Wt\.?|Weight|Qty\.?|Quantity|Contents?)|Contents?)[\s:]*'
                r'([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|gms|kg|kgs|ml|mL|l|L|ltr|litre|liters?|oz|lb)s?)|'
                r'([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|gms|kg|kgs|ml|mL|l|L|ltr|litre|liters?))\b',
                re.IGNORECASE
            ),
            
            # Date patterns (manufacture/expiry)
            'date': re.compile(
                r'([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})|'  # DD/MM/YYYY or MM/DD/YYYY
                r'([0-9]{1,2}[\/\-][0-9]{2,4})|'  # MM/YYYY
                r'([A-Za-z]{3,9}[\s,]*[0-9]{1,2}[,]?\s*[0-9]{2,4})|'  # Month DD, YYYY
                r'([0-9]{1,2}[\s\-]*[A-Za-z]{3,9}[\s,]*[0-9]{2,4})',  # DD Month YYYY
                re.IGNORECASE
            ),
            
            # Manufacture date keywords
            'mfg_date': re.compile(
                r'(?:Mfg\.?|Mfd\.?|Manufacturing|Manufactured|Packed|Packing|Pkg\.?)[\s:]*(?:Date)?[\s:]*'
                r'([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|'
                r'[0-9]{1,2}[\/\-][0-9]{2,4}|'
                r'[A-Za-z]{3,9}[\s,]*[0-9]{1,2}[,]?\s*[0-9]{2,4}|'
                r'[0-9]{1,2}[\s\-]*[A-Za-z]{3,9}[\s,]*[0-9]{2,4})',
                re.IGNORECASE
            ),
            
            # Expiry date keywords
            'exp_date': re.compile(
                r'(?:Exp\.?|Expiry|Expires?|Best\s*Before|BB|Use\s*By|Use\s*Before)[\s:]*(?:Date)?[\s:]*'
                r'([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|'
                r'[0-9]{1,2}[\/\-][0-9]{2,4}|'
                r'[A-Za-z]{3,9}[\s,]*[0-9]{1,2}[,]?\s*[0-9]{2,4}|'
                r'[0-9]{1,2}[\s\-]*[A-Za-z]{3,9}[\s,]*[0-9]{2,4}|'
                r'[0-9]+\s*(?:months?|days?|years?)\s*(?:from\s*(?:mfg|manufacturing|packing))?)',
                re.IGNORECASE
            ),
            
            # Country of origin
            'country': re.compile(
                r'(?:Country\s*of\s*Origin|Made\s*in|Product\s*of|Manufactured\s*in|Origin)[\s:]*'
                r'([A-Za-z]+(?:\s+[A-Za-z]+)?)',
                re.IGNORECASE
            ),
            
            # Manufacturer/Importer details
            'manufacturer': re.compile(
                r'(?:Mfg\.?\s*(?:by)?|Manufactured\s*by|Packed\s*by|Packer|Marketer|Marketed\s*by)[\s:]*'
                r'([A-Za-z0-9][A-Za-z0-9\s,\.&\-]+(?:Ltd\.?|Pvt\.?|Inc\.?|LLC|Co\.?|Corporation|Industries)?)',
                re.IGNORECASE
            ),
            
            'importer': re.compile(
                r'(?:Imported\s*by|Importer)[\s:]*'
                r'([A-Za-z0-9][A-Za-z0-9\s,\.&\-]+(?:Ltd\.?|Pvt\.?|Inc\.?|LLC|Co\.?)?)',
                re.IGNORECASE
            ),
            
            # Consumer care / Contact
            'consumer_care': re.compile(
                r'(?:Consumer\s*Care|Customer\s*Care|Helpline|Contact|Toll\s*Free)[\s:]*'
                r'([0-9\-\+\s\(\)]{8,20})|'
                r'(?:1800[\-\s]*[0-9\-\s]{6,12})',
                re.IGNORECASE
            ),
            
            # Batch number
            'batch': re.compile(
                r'(?:Batch|Lot|B\.?\s*No\.?|L\.?\s*No\.?)[\s:]*([A-Za-z0-9\-\/]{4,20})',
                re.IGNORECASE
            ),
            
            # FSSAI License (14 digits)
            'fssai': re.compile(
                r'(?:FSSAI|Lic\.?\s*No\.?|License\s*No\.?)[\s:]*([0-9]{10,14})|'
                r'\b([0-9]{14})\b',
                re.IGNORECASE
            ),
            
            # BIS Certification
            'bis': re.compile(
                r'(?:BIS|ISI|IS[\s:]*[0-9]+)[\s:]*([A-Za-z0-9\-\/]+)|'
                r'(?:R-[0-9]{7,})',
                re.IGNORECASE
            ),
        }
    
    # ========================================================================
    # Image Preprocessing Pipeline
    # ========================================================================
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply comprehensive preprocessing to improve OCR accuracy.
        
        Steps:
        1. Resize for consistent resolution
        2. Convert to grayscale
        3. Apply Gaussian blur for noise reduction
        4. Apply adaptive thresholding
        5. Apply morphological operations
        
        Args:
            image: Input image as numpy array (BGR format from cv2)
            
        Returns:
            Preprocessed image optimized for text detection
        """
        # Step 1: Resize for consistent resolution
        image = self._resize_image(image)
        
        # Step 2: Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Step 3: Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Step 4: Apply adaptive thresholding
        # Using Gaussian method for better handling of varying illumination
        thresh = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Block size
            2    # Constant subtracted from mean
        )
        
        # Step 5: Morphological operations to clean up the image
        # Create a small kernel for noise removal
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        
        # Opening removes small noise
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Closing fills small holes in text
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        return cleaned
    
    def _resize_image(self, image: np.ndarray) -> np.ndarray:
        """Resize image to target width while maintaining aspect ratio"""
        height, width = image.shape[:2]
        
        if width < TARGET_WIDTH:
            scale = TARGET_WIDTH / width
            new_width = TARGET_WIDTH
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        elif width > TARGET_WIDTH * 2:
            # Downscale very large images
            scale = TARGET_WIDTH / width
            new_width = TARGET_WIDTH
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return image
    
    def preprocess_for_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image specifically for bounding box detection.
        Uses different parameters optimized for edge/contour detection.
        """
        # Resize first
        image = self._resize_image(image)
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply bilateral filter - preserves edges while removing noise
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(bilateral)
        
        return enhanced
    
    # ========================================================================
    # Bounding Box Detection
    # ========================================================================
    
    def detect_text_regions(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Detect text regions using contour-based detection.
        
        Method:
        1. Preprocess image for detection
        2. Apply Canny edge detection
        3. Find contours
        4. Filter contours by area and aspect ratio
        5. Sort bounding boxes top-to-bottom, left-to-right
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of BoundingBox objects sorted for reading order
        """
        # Get image dimensions
        height, width = image.shape[:2]
        image_area = height * width
        
        # Preprocess for detection
        processed = self.preprocess_for_detection(image)
        
        # Apply Canny edge detection
        edges = cv2.Canny(processed, 50, 150)
        
        # Dilate edges to connect nearby text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bounding_boxes: List[BoundingBox] = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            # Filter by area
            if area < MIN_CONTOUR_AREA:
                continue
            if area > image_area * MAX_CONTOUR_AREA_RATIO:
                continue
            
            # Filter by aspect ratio (text regions are typically wider than tall)
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
                continue
            
            # Add padding around detected region
            padding = 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(width - x, w + 2 * padding)
            h = min(height - y, h + 2 * padding)
            
            bounding_boxes.append(BoundingBox(x=x, y=y, width=w, height=h))
        
        # If no boxes detected, try alternative method
        if not bounding_boxes:
            bounding_boxes = self._detect_text_regions_mser(image)
        
        # Sort boxes: top-to-bottom, then left-to-right
        bounding_boxes = self._sort_bounding_boxes(bounding_boxes)
        
        logger.info(f"Detected {len(bounding_boxes)} text regions")
        return bounding_boxes
    
    def _detect_text_regions_mser(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Alternative text detection using MSER (Maximally Stable Extremal Regions).
        Used as fallback when contour detection fails.
        """
        height, width = image.shape[:2]
        
        # Preprocess
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Create MSER detector
        mser = cv2.MSER_create()
        mser.setMinArea(60)
        mser.setMaxArea(int(width * height * 0.3))
        
        # Detect regions
        regions, _ = mser.detectRegions(gray)
        
        bounding_boxes: List[BoundingBox] = []
        
        for region in regions:
            x, y, w, h = cv2.boundingRect(region)
            
            # Filter small/large regions
            area = w * h
            if area < MIN_CONTOUR_AREA or area > width * height * MAX_CONTOUR_AREA_RATIO:
                continue
            
            bounding_boxes.append(BoundingBox(x=x, y=y, width=w, height=h))
        
        # Merge overlapping boxes
        bounding_boxes = self._merge_overlapping_boxes(bounding_boxes)
        
        return bounding_boxes
    
    def _merge_overlapping_boxes(self, boxes: List[BoundingBox], overlap_thresh: float = 0.5) -> List[BoundingBox]:
        """Merge overlapping bounding boxes to reduce fragmentation"""
        if not boxes:
            return boxes
        
        # Convert to numpy array for NMS-like processing
        rects = np.array([[b.x, b.y, b.x + b.width, b.y + b.height] for b in boxes])
        
        merged = []
        used = set()
        
        for i, box in enumerate(boxes):
            if i in used:
                continue
            
            # Find overlapping boxes
            current_rect = [box.x, box.y, box.x + box.width, box.y + box.height]
            
            for j, other_box in enumerate(boxes):
                if j <= i or j in used:
                    continue
                
                other_rect = [other_box.x, other_box.y, 
                             other_box.x + other_box.width, other_box.y + other_box.height]
                
                # Calculate intersection
                x1 = max(current_rect[0], other_rect[0])
                y1 = max(current_rect[1], other_rect[1])
                x2 = min(current_rect[2], other_rect[2])
                y2 = min(current_rect[3], other_rect[3])
                
                if x1 < x2 and y1 < y2:
                    intersection = (x2 - x1) * (y2 - y1)
                    area1 = (current_rect[2] - current_rect[0]) * (current_rect[3] - current_rect[1])
                    area2 = (other_rect[2] - other_rect[0]) * (other_rect[3] - other_rect[1])
                    min_area = min(area1, area2)
                    
                    if intersection / min_area > overlap_thresh:
                        # Merge boxes
                        current_rect[0] = min(current_rect[0], other_rect[0])
                        current_rect[1] = min(current_rect[1], other_rect[1])
                        current_rect[2] = max(current_rect[2], other_rect[2])
                        current_rect[3] = max(current_rect[3], other_rect[3])
                        used.add(j)
            
            merged.append(BoundingBox(
                x=current_rect[0],
                y=current_rect[1],
                width=current_rect[2] - current_rect[0],
                height=current_rect[3] - current_rect[1]
            ))
            used.add(i)
        
        return merged
    
    def _sort_bounding_boxes(self, boxes: List[BoundingBox]) -> List[BoundingBox]:
        """Sort bounding boxes in reading order (top-to-bottom, left-to-right)"""
        if not boxes:
            return boxes
        
        # Calculate average height for row grouping
        avg_height = sum(b.height for b in boxes) / len(boxes)
        row_threshold = avg_height * 0.5
        
        # Group boxes into rows
        sorted_boxes = sorted(boxes, key=lambda b: b.y)
        rows: List[List[BoundingBox]] = []
        current_row: List[BoundingBox] = []
        current_y = sorted_boxes[0].y if sorted_boxes else 0
        
        for box in sorted_boxes:
            if abs(box.center_y - current_y) < row_threshold and current_row:
                current_row.append(box)
            else:
                if current_row:
                    rows.append(current_row)
                current_row = [box]
                current_y = box.center_y
        
        if current_row:
            rows.append(current_row)
        
        # Sort each row left-to-right
        result = []
        for row in rows:
            row.sort(key=lambda b: b.x)
            result.extend(row)
        
        return result
    
    # ========================================================================
    # Region-wise OCR
    # ========================================================================
    
    def extract_text_from_region(
        self, 
        image: np.ndarray, 
        bbox: BoundingBox
    ) -> Tuple[str, float, List[Dict]]:
        """
        Perform OCR on a specific region of the image.
        
        Args:
            image: Full image as numpy array
            bbox: Bounding box defining the region
            
        Returns:
            Tuple of (extracted_text, average_confidence, word_details)
        """
        # Crop the region
        cropped = image[bbox.y:bbox.y + bbox.height, bbox.x:bbox.x + bbox.width]
        
        # Preprocess the cropped region
        processed = self.preprocess_image(cropped)
        
        # Convert to PIL for pytesseract
        pil_image = Image.fromarray(processed)
        
        try:
            # Get detailed OCR data
            ocr_data = pytesseract.image_to_data(
                pil_image, 
                output_type=pytesseract.Output.DICT,
                lang='eng+hin',
                config='--psm 6'  # Assume uniform block of text
            )
        except Exception as e:
            logger.warning(f"OCR failed for region: {e}")
            return "", 0.0, []
        
        # Filter and aggregate results
        words = []
        confidences = []
        
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            conf = float(ocr_data['conf'][i])
            
            # Filter out empty text and low confidence
            if not text or conf < MIN_CONFIDENCE_THRESHOLD:
                continue
            
            words.append({
                'text': text,
                'confidence': conf,
                'x': bbox.x + ocr_data['left'][i],
                'y': bbox.y + ocr_data['top'][i],
                'width': ocr_data['width'][i],
                'height': ocr_data['height'][i]
            })
            confidences.append(conf)
        
        # Combine text
        extracted_text = ' '.join(w['text'] for w in words)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return extracted_text, avg_confidence, words
    
    def perform_region_wise_ocr(
        self, 
        image: np.ndarray, 
        bounding_boxes: List[BoundingBox]
    ) -> Tuple[List[TextRegion], float]:
        """
        Perform OCR on all detected regions.
        
        Args:
            image: Full image as numpy array
            bounding_boxes: List of detected text regions
            
        Returns:
            Tuple of (list of TextRegion results, overall confidence)
        """
        regions: List[TextRegion] = []
        all_confidences: List[float] = []
        
        for idx, bbox in enumerate(bounding_boxes):
            text, confidence, _ = self.extract_text_from_region(image, bbox)
            
            if text:  # Only include regions with extracted text
                regions.append(TextRegion(
                    x=bbox.x,
                    y=bbox.y,
                    width=bbox.width,
                    height=bbox.height,
                    text=text,
                    confidence=confidence / 100.0,  # Normalize to 0-1
                    region_index=idx
                ))
                all_confidences.append(confidence)
        
        # Calculate overall confidence
        overall_confidence = (
            sum(all_confidences) / len(all_confidences) / 100.0 
            if all_confidences else 0.0
        )
        
        logger.info(f"Extracted text from {len(regions)} regions, overall confidence: {overall_confidence:.2f}")
        return regions, overall_confidence
    
    # ========================================================================
    # Structured Field Extraction
    # ========================================================================
    
    def extract_compliance_fields(
        self, 
        text_regions: List[TextRegion],
        combined_text: str,
        category: Optional[ProductCategory] = None
    ) -> ComplianceFields:
        """
        Extract structured compliance fields from OCR results.
        
        Uses regex patterns to identify and extract:
        - MRP
        - Net Quantity
        - Manufacture Date
        - Expiry Date
        - Country of Origin
        - Manufacturer details
        - Consumer care contact
        - Batch number
        - FSSAI License (for food)
        - BIS Certification (for electronics)
        
        Args:
            text_regions: List of text regions with OCR results
            combined_text: All extracted text combined
            category: Optional product category for targeted extraction
            
        Returns:
            ComplianceFields with extracted values
        """
        fields = ComplianceFields()
        
        # Combine all text for global pattern matching
        full_text = combined_text or ' '.join(r.text for r in text_regions)
        
        # Extract MRP
        mrp_match = self.patterns['mrp'].search(full_text)
        if mrp_match:
            # Get the first non-None group
            mrp_value = next((g for g in mrp_match.groups() if g), None)
            if mrp_value:
                fields.mrp = f"₹{mrp_value.replace(',', '')}"
        
        # Extract Net Quantity
        qty_match = self.patterns['net_quantity'].search(full_text)
        if qty_match:
            qty_value = next((g for g in qty_match.groups() if g), None)
            if qty_value:
                fields.net_quantity = qty_value
        
        # Extract Manufacture Date
        mfg_match = self.patterns['mfg_date'].search(full_text)
        if mfg_match:
            fields.manufacture_date = mfg_match.group(1)
        
        # Extract Expiry Date
        exp_match = self.patterns['exp_date'].search(full_text)
        if exp_match:
            fields.expiry_date = exp_match.group(1)
        
        # If no specific dates found, try generic date extraction
        if not fields.manufacture_date and not fields.expiry_date:
            date_matches = self.patterns['date'].findall(full_text)
            if len(date_matches) >= 2:
                # Assume first date is manufacture, second is expiry
                fields.manufacture_date = next((d for d in date_matches[0] if d), None)
                fields.expiry_date = next((d for d in date_matches[1] if d), None)
            elif len(date_matches) == 1:
                # Single date - likely expiry for food products
                date_val = next((d for d in date_matches[0] if d), None)
                if category == ProductCategory.FOOD:
                    fields.expiry_date = date_val
                else:
                    fields.manufacture_date = date_val
        
        # Extract Country of Origin
        country_match = self.patterns['country'].search(full_text)
        if country_match:
            fields.country_of_origin = country_match.group(1).strip()
        
        # Extract Manufacturer
        mfr_match = self.patterns['manufacturer'].search(full_text)
        if mfr_match:
            fields.manufacturer = mfr_match.group(1).strip()
        
        # Extract Importer
        imp_match = self.patterns['importer'].search(full_text)
        if imp_match:
            fields.importer = imp_match.group(1).strip()
        
        # Extract Consumer Care
        care_match = self.patterns['consumer_care'].search(full_text)
        if care_match:
            contact = next((g for g in care_match.groups() if g), None)
            if contact:
                fields.consumer_care = contact.strip()
        
        # Extract Batch Number
        batch_match = self.patterns['batch'].search(full_text)
        if batch_match:
            fields.batch_number = batch_match.group(1)
        
        # Extract FSSAI License (primarily for food)
        if category == ProductCategory.FOOD or category is None:
            fssai_match = self.patterns['fssai'].search(full_text)
            if fssai_match:
                fssai_val = next((g for g in fssai_match.groups() if g), None)
                if fssai_val and len(fssai_val) >= 10:
                    fields.fssai_license = fssai_val
        
        # Extract BIS Certification (primarily for electronics)
        if category == ProductCategory.ELECTRONICS or category is None:
            bis_match = self.patterns['bis'].search(full_text)
            if bis_match:
                bis_val = bis_match.group(1) if bis_match.lastindex else bis_match.group(0)
                fields.bis_certification = bis_val
        
        logger.info(f"Extracted fields: MRP={fields.mrp}, Qty={fields.net_quantity}, "
                   f"Mfg={fields.manufacture_date}, Exp={fields.expiry_date}")
        
        return fields
    
    # ========================================================================
    # Confidence Aggregation
    # ========================================================================
    
    def calculate_confidence_metrics(
        self, 
        text_regions: List[TextRegion]
    ) -> Tuple[float, ConfidenceLevel, List[float], int]:
        """
        Calculate confidence metrics and flag low-confidence extractions.
        
        Args:
            text_regions: List of text regions with confidence scores
            
        Returns:
            Tuple of (overall_confidence, confidence_level, region_confidences, low_conf_count)
        """
        if not text_regions:
            return 0.0, ConfidenceLevel.VERY_LOW, [], 0
        
        region_confidences = [r.confidence for r in text_regions]
        overall_confidence = sum(region_confidences) / len(region_confidences)
        
        # Count low confidence regions
        low_conf_count = sum(1 for c in region_confidences if c < LOW_CONFIDENCE_THRESHOLD / 100.0)
        
        # Determine confidence level
        if overall_confidence >= 0.85:
            level = ConfidenceLevel.HIGH
        elif overall_confidence >= 0.70:
            level = ConfidenceLevel.MEDIUM
        elif overall_confidence >= 0.50:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.VERY_LOW
        
        return overall_confidence, level, region_confidences, low_conf_count
    
    # ========================================================================
    # Main Processing Pipeline
    # ========================================================================
    
    def process_image(
        self, 
        image_data: bytes,
        category: Optional[ProductCategory] = None
    ) -> OCRProcessingResult:
        """
        Main OCR processing pipeline.
        
        Pipeline:
        1. Load and preprocess image
        2. Detect text regions (bounding boxes)
        3. Perform region-wise OCR
        4. Extract structured compliance fields
        5. Calculate confidence metrics
        
        Args:
            image_data: Raw image bytes
            category: Optional product category
            
        Returns:
            OCRProcessingResult with all extracted data
        """
        import time
        start_time = time.time()
        
        try:
            # Load image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return OCRProcessingResult(
                    confidence_score=0.0,
                    confidence_level=ConfidenceLevel.VERY_LOW,
                    error="Failed to decode image"
                )
            
            height, width = image.shape[:2]
            
            # Step 1: Detect text regions
            bounding_boxes = self.detect_text_regions(image)
            
            # If no regions detected, fall back to full-image OCR
            if not bounding_boxes:
                logger.warning("No text regions detected, using full-image OCR")
                bounding_boxes = [BoundingBox(x=0, y=0, width=width, height=height)]
            
            # Step 2: Perform region-wise OCR
            text_regions, overall_conf = self.perform_region_wise_ocr(image, bounding_boxes)
            
            # Step 3: Combine all text
            combined_text = ' '.join(r.text for r in text_regions)
            
            # Step 4: Extract compliance fields
            fields = self.extract_compliance_fields(text_regions, combined_text, category)
            
            # Step 5: Calculate confidence metrics
            confidence, level, region_confs, low_conf_count = self.calculate_confidence_metrics(text_regions)
            
            # Determine if review is needed
            needs_review = level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return OCRProcessingResult(
                # Structured fields
                mrp=fields.mrp,
                net_quantity=fields.net_quantity,
                manufacture_date=fields.manufacture_date,
                expiry_date=fields.expiry_date,
                country_of_origin=fields.country_of_origin,
                manufacturer=fields.manufacturer,
                importer=fields.importer,
                consumer_care=fields.consumer_care,
                batch_number=fields.batch_number,
                fssai_license=fields.fssai_license,
                bis_certification=fields.bis_certification,
                
                # Confidence metrics
                confidence_score=round(confidence, 4),
                confidence_level=level,
                region_confidences=region_confs,
                
                # Raw data
                raw_text_regions=text_regions,
                combined_text=combined_text,
                
                # Metadata
                total_regions_detected=len(bounding_boxes),
                regions_processed=len(text_regions),
                low_confidence_regions=low_conf_count,
                processing_time_ms=round(processing_time, 2),
                image_dimensions=(width, height),
                
                # Flags
                needs_review=needs_review
            )
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}", exc_info=True)
            return OCRProcessingResult(
                confidence_score=0.0,
                confidence_level=ConfidenceLevel.VERY_LOW,
                error=str(e)
            )
    
    async def process_image_url(
        self, 
        image_url: str,
        category: Optional[ProductCategory] = None
    ) -> OCRProcessingResult:
        """
        Process an image from URL.
        
        Args:
            image_url: URL of the image to process
            category: Optional product category
            
        Returns:
            OCRProcessingResult
        """
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "image/*,*/*;q=0.8",
                }
                async with session.get(image_url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        return OCRProcessingResult(
                            confidence_score=0.0,
                            confidence_level=ConfidenceLevel.VERY_LOW,
                            error=f"Failed to fetch image: HTTP {response.status}"
                        )
                    
                    image_data = await response.read()
                    return self.process_image(image_data, category)
                    
        except Exception as e:
            logger.error(f"Failed to fetch image from URL: {e}")
            return OCRProcessingResult(
                confidence_score=0.0,
                confidence_level=ConfidenceLevel.VERY_LOW,
                error=f"Failed to fetch image: {str(e)}"
            )
    
    def process_image_path(
        self, 
        image_path: str,
        category: Optional[ProductCategory] = None
    ) -> OCRProcessingResult:
        """
        Process an image from local file path.
        
        Args:
            image_path: Path to the image file
            category: Optional product category
            
        Returns:
            OCRProcessingResult
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return self.process_image(image_data, category)
        except FileNotFoundError:
            return OCRProcessingResult(
                confidence_score=0.0,
                confidence_level=ConfidenceLevel.VERY_LOW,
                error=f"Image file not found: {image_path}"
            )
        except Exception as e:
            return OCRProcessingResult(
                confidence_score=0.0,
                confidence_level=ConfidenceLevel.VERY_LOW,
                error=f"Failed to read image: {str(e)}"
            )


# ============================================================================
# Singleton Instance
# ============================================================================

# Create a singleton instance for use across the application
_advanced_ocr_service: Optional[AdvancedOCRService] = None


def get_advanced_ocr_service() -> AdvancedOCRService:
    """Get or create the singleton AdvancedOCRService instance"""
    global _advanced_ocr_service
    if _advanced_ocr_service is None:
        _advanced_ocr_service = AdvancedOCRService()
    return _advanced_ocr_service
