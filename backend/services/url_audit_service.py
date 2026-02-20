import uuid
import logging
from typing import Optional

from backend.models import RiskLevel, URLAuditResult, ProductCategory
from backend.services.field_identification_service import FieldIdentificationService
from backend.services.image_ocr_extraction_service import ImageOCRExtractionService
from backend.services.scraper_service import ScraperService
from backend.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class URLAuditService:
    def __init__(self) -> None:
        self.scraper_service = ScraperService()
        self.image_ocr_service = ImageOCRExtractionService()
        self.field_identification_service = FieldIdentificationService()
        self.validation_service = ValidationService()

    def classify_risk(self, score: int) -> RiskLevel:
        if score >= 85:
            return RiskLevel.COMPLIANT
        if score >= 60:
            return RiskLevel.MODERATE
        return RiskLevel.HIGH

    def audit(
        self, 
        url: str, 
        seller_id: str,
        category: Optional[str] = None
    ) -> URLAuditResult:
        """
        Audit a product URL for Legal Metrology compliance.
        
        Args:
            url: Product URL to audit
            seller_id: Seller identifier
            category: Optional product category (food, electronics, cosmetics)
                     If not provided, will be auto-detected
        
        Returns:
            URLAuditResult with compliance score and violations
        """
        scraped = self.scraper_service.fetch_product_data(url)
        ocr_text = self.image_ocr_service.extract_from_image_urls(scraped.image_urls)

        specs_text = "\n".join(f"{key}: {value}" for key, value in scraped.specifications.items())
        scraped_text = "\n".join(
            [
                scraped.title or "",
                scraped.description or "",
                specs_text,
                scraped.raw_text,
            ]
        )

        # Auto-detect category if not provided
        detected_category = category
        if not detected_category:
            detected_category = self.validation_service.detect_category(
                f"{scraped_text}\n{ocr_text}"
            )
            logger.info(f"Auto-detected category: {detected_category}")
        
        # Convert to ProductCategory enum value
        try:
            product_category = ProductCategory(detected_category.lower())
        except ValueError:
            product_category = ProductCategory.GENERIC

        # Extract fields with category context
        identified_fields = self.field_identification_service.extract_mandatory_fields(
            scraped_text=scraped_text,
            ocr_text=ocr_text,
            category=detected_category,
        )

        # Validate with category-specific rules
        score, violations = self.validation_service.validate(
            fields=identified_fields,
            scraped_text=scraped_text,
            ocr_text=ocr_text,
            category=detected_category,
        )

        return URLAuditResult(
            product_id=str(uuid.uuid4()),
            seller_id=seller_id,
            category=product_category,
            compliance_score=score,
            risk_level=self.classify_risk(score),
            scraped_data=scraped,
            ocr_text=ocr_text,
            identified_fields=identified_fields,
            violations=violations,
        )
