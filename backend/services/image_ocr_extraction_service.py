import logging
import requests
from requests import exceptions as request_exceptions
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from backend.services.ocr_service import OCRService

logger = logging.getLogger(__name__)


class ImageOCRExtractionService:
    def __init__(self) -> None:
        self.ocr_service = OCRService()
        self.session = requests.Session()
        # Use same headers as scraper to avoid bot detection
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.amazon.in/",
                "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
            }
        )

    def _process_single_image(self, image_url: str) -> Optional[str]:
        """Download and OCR a single image. Returns extracted text or None."""
        try:
            logger.info(f"Downloading image: {image_url[:80]}...")
            try:
                response = self.session.get(image_url, timeout=20)
            except request_exceptions.SSLError:
                response = self.session.get(image_url, timeout=20, verify=False)
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "")
            content_length = len(response.content)
            
            # Skip if not an image or too small (redirect pages)
            if "image" not in content_type.lower() and content_length < 1000:
                logger.warning(f"Skipping non-image response: {content_type}, {content_length} bytes")
                return None
            
            # Skip very small responses (likely error pages or placeholders)
            if content_length < 500:
                logger.warning(f"Skipping tiny response: {content_length} bytes")
                return None
                
            logger.info(f"Downloaded {content_length} bytes, extracting text...")
            ocr_text = self.ocr_service.extract_text(response.content)
            if ocr_text and len(ocr_text.strip()) > 5:  # Only keep meaningful text
                logger.info(f"Extracted {len(ocr_text)} chars from image")
                return ocr_text
            return None
        except Exception as e:
            logger.warning(f"Failed to process image {image_url[:50]}: {e}")
            return None

    def extract_from_image_urls(self, image_urls: list[str], max_images: int = 20) -> str:
        """Extract text from multiple image URLs using parallel processing.
        
        Args:
            image_urls: List of image URLs to process
            max_images: Maximum number of images to process (default: 20)
        
        Returns:
            Combined OCR text from all processed images
        """
        if not image_urls:
            return ""
        
        # Deduplicate URLs while preserving order
        seen = set()
        unique_urls = []
        for url in image_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        # Limit to max_images
        urls_to_process = unique_urls[:max_images]
        logger.info(f"Processing {len(urls_to_process)} images (from {len(image_urls)} total)")
        
        texts: list[str] = []
        
        # Use ThreadPoolExecutor for parallel image processing
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self._process_single_image, url): url 
                for url in urls_to_process
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result:
                        texts.append(result)
                except Exception as e:
                    logger.warning(f"Image processing failed for {url[:50]}: {e}")

        combined = "\n".join(texts).strip()
        logger.info(f"Total OCR text extracted: {len(combined)} chars from {len(texts)} images")
        return combined
