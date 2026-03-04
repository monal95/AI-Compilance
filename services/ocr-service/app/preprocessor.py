"""
Image Preprocessor using OpenCV for improved OCR accuracy.

Provides multiple preprocessing techniques:
- Grayscale conversion
- Noise removal
- Thresholding (adaptive, Otsu)
- Deskewing
- Contrast enhancement
- Edge detection
"""
import logging
from typing import Optional
import io

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Image preprocessing pipeline for OCR optimization."""
    
    def __init__(self):
        self.target_dpi = 300
        self.max_dimension = 4000
    
    def load_image(self, image_bytes: bytes) -> np.ndarray:
        """Load image from bytes to OpenCV format."""
        try:
            # First try with PIL for wider format support
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if pil_image.mode == "RGBA":
                pil_image = pil_image.convert("RGB")
            elif pil_image.mode == "P":
                pil_image = pil_image.convert("RGB")
            elif pil_image.mode == "L":
                # Already grayscale
                return np.array(pil_image)
            
            # Convert to numpy array (RGB)
            image = np.array(pil_image)
            
            # Convert RGB to BGR for OpenCV
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            return image
        
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            # Fallback to OpenCV direct decode
            nparr = np.frombuffer(image_bytes, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    def to_bytes(self, image: np.ndarray, format: str = "PNG") -> bytes:
        """Convert OpenCV image to bytes."""
        if format.upper() == "PNG":
            _, buffer = cv2.imencode(".png", image)
        else:
            _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return buffer.tobytes()
    
    def resize_if_needed(self, image: np.ndarray) -> np.ndarray:
        """Resize image if too large while maintaining aspect ratio."""
        height, width = image.shape[:2]
        
        if max(height, width) > self.max_dimension:
            scale = self.max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        return image
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale."""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def remove_noise(self, image: np.ndarray) -> np.ndarray:
        """Remove noise using Non-Local Means Denoising."""
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
    
    def adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding."""
        gray = self.to_grayscale(image)
        return cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
    
    def otsu_threshold(self, image: np.ndarray) -> np.ndarray:
        """Apply Otsu's thresholding."""
        gray = self.to_grayscale(image)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast using CLAHE."""
        if len(image.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge and convert back
            lab = cv2.merge([l, a, b])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image)
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """Deskew image by detecting text angle."""
        gray = self.to_grayscale(image)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines using HoughLines
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is None:
            return image
        
        # Calculate average angle
        angles = []
        for line in lines[:20]:  # Use first 20 lines
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            if abs(angle) < 45:  # Filter out vertical lines
                angles.append(angle)
        
        if not angles:
            return image
        
        avg_angle = np.median(angles)
        
        # Only deskew if angle is significant
        if abs(avg_angle) < 0.5:
            return image
        
        logger.info(f"Deskewing image by {avg_angle:.2f} degrees")
        
        # Rotate image
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        matrix = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
        
        # Calculate new dimensions to avoid clipping
        cos = np.abs(matrix[0, 0])
        sin = np.abs(matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))
        
        # Adjust rotation matrix
        matrix[0, 2] += (new_width / 2) - center[0]
        matrix[1, 2] += (new_height / 2) - center[1]
        
        return cv2.warpAffine(
            image, matrix, (new_width, new_height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
    
    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """Sharpen image using unsharp mask."""
        gaussian = cv2.GaussianBlur(image, (0, 0), 3)
        return cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
    
    def remove_shadows(self, image: np.ndarray) -> np.ndarray:
        """Remove shadows from image."""
        if len(image.shape) == 2:
            # Grayscale
            dilated = cv2.dilate(image, np.ones((7, 7), np.uint8))
            background = cv2.medianBlur(dilated, 21)
            diff = 255 - cv2.absdiff(image, background)
            return cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
        else:
            # Color image - process each channel
            rgb_planes = cv2.split(image)
            result_planes = []
            
            for plane in rgb_planes:
                dilated = cv2.dilate(plane, np.ones((7, 7), np.uint8))
                background = cv2.medianBlur(dilated, 21)
                diff = 255 - cv2.absdiff(plane, background)
                norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
                result_planes.append(norm)
            
            return cv2.merge(result_planes)
    
    def preprocess(
        self,
        image_bytes: bytes,
        techniques: Optional[list[str]] = None,
    ) -> list[bytes]:
        """
        Apply preprocessing pipeline and return multiple versions.
        
        Default techniques applied:
        1. Original (resized if needed)
        2. Grayscale + contrast enhanced
        3. Adaptive threshold
        4. Otsu threshold
        5. Denoised + deskewed
        
        Returns multiple preprocessed versions for OCR to try.
        """
        image = self.load_image(image_bytes)
        image = self.resize_if_needed(image)
        
        results = []
        
        try:
            # Version 1: Original (may be already good quality)
            results.append(self.to_bytes(image))
            
            # Version 2: Grayscale with contrast enhancement
            gray = self.to_grayscale(image)
            enhanced = self.enhance_contrast(gray)
            results.append(self.to_bytes(enhanced))
            
            # Version 3: Adaptive threshold
            adaptive = self.adaptive_threshold(image)
            results.append(self.to_bytes(adaptive))
            
            # Version 4: Otsu threshold
            otsu = self.otsu_threshold(image)
            results.append(self.to_bytes(otsu))
            
            # Version 5: Full pipeline - denoise, deskew, sharpen
            denoised = self.remove_noise(image)
            deskewed = self.deskew(denoised)
            sharpened = self.sharpen(deskewed)
            gray_final = self.to_grayscale(sharpened)
            enhanced_final = self.enhance_contrast(gray_final)
            results.append(self.to_bytes(enhanced_final))
            
            # Version 6: Shadow removal (for product photos with uneven lighting)
            shadow_removed = self.remove_shadows(gray)
            results.append(self.to_bytes(shadow_removed))
            
        except Exception as e:
            logger.warning(f"Some preprocessing steps failed: {e}")
        
        logger.info(f"Created {len(results)} preprocessed image versions")
        return results
