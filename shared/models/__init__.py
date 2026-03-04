"""Shared Pydantic models for the compliance monitoring system."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# Enums
class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ProductCategory(str, Enum):
    FOOD = "food"
    ELECTRONICS = "electronics"
    COSMETICS = "cosmetics"
    GENERIC = "generic"


class Marketplace(str, Enum):
    AMAZON = "amazon"
    FLIPKART = "flipkart"
    MEESHO = "meesho"
    OTHER = "other"


class CrawlStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ViolationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleType(str, Enum):
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"


# Base Models
class BaseDocument(BaseModel):
    """Base model with common fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Product Models
class ScrapedData(BaseModel):
    """Data extracted from web scraping."""
    description: Optional[str] = None
    specifications: dict[str, str] = Field(default_factory=dict)
    images: list[str] = Field(default_factory=list)
    raw_html: Optional[str] = None
    raw_text: Optional[str] = None


class ExtractedFields(BaseModel):
    """Normalized fields extracted from product data."""
    # Universal fields
    mrp: Optional[str] = None
    selling_price: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturer_address: Optional[str] = None
    importer_address: Optional[str] = None
    country_of_origin: Optional[str] = None
    net_quantity: Optional[str] = None
    common_generic_name: Optional[str] = None
    consumer_care_info: Optional[str] = None
    date_of_manufacture: Optional[str] = None
    
    # Food-specific
    fssai_license: Optional[str] = None
    expiry_date: Optional[str] = None
    ingredients: Optional[str] = None
    nutritional_info: Optional[str] = None
    allergen_info: Optional[str] = None
    veg_nonveg_symbol: Optional[str] = None
    batch_number: Optional[str] = None
    storage_instructions: Optional[str] = None
    
    # Electronics-specific
    bis_certification: Optional[str] = None
    model_number: Optional[str] = None
    warranty_period: Optional[str] = None
    power_rating: Optional[str] = None
    voltage_frequency: Optional[str] = None
    energy_rating: Optional[str] = None
    serial_number: Optional[str] = None
    safety_instructions: Optional[str] = None
    
    # Cosmetics-specific
    usage_instructions: Optional[str] = None
    warnings: Optional[str] = None
    cruelty_free: Optional[str] = None


class OCRData(BaseModel):
    """Data extracted from OCR processing."""
    raw_text: str = ""
    confidence: float = 0.0
    language: str = "en"
    processed_images: list[str] = Field(default_factory=list)
    regions: list[dict[str, Any]] = Field(default_factory=list)


class Product(BaseDocument):
    """Product document model."""
    product_id: str
    url: str
    marketplace: Marketplace = Marketplace.OTHER
    title: Optional[str] = None
    category: ProductCategory = ProductCategory.GENERIC
    scraped_data: ScrapedData = Field(default_factory=ScrapedData)
    extracted_fields: ExtractedFields = Field(default_factory=ExtractedFields)
    ocr_data: OCRData = Field(default_factory=OCRData)
    crawl_status: CrawlStatus = CrawlStatus.PENDING


# Violation Models
class Violation(BaseModel):
    """Compliance violation details."""
    code: str
    field: str
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    message: str
    penalty: int = 0
    legal_reference: Optional[str] = None


class MissingFields(BaseModel):
    """Missing field categorization."""
    mandatory: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    """Detailed compliance score breakdown."""
    mandatory_fields_score: float = 0.0
    optional_fields_score: float = 0.0
    format_compliance_score: float = 0.0
    weighted_total: float = 0.0


# Audit Models
class Audit(BaseDocument):
    """Audit result document model."""
    audit_id: str
    product_id: str
    seller_id: str
    compliance_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    violations: list[Violation] = Field(default_factory=list)
    missing_fields: MissingFields = Field(default_factory=MissingFields)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    audited_by: str = "system"


# Rule Models
class RuleValidation(BaseModel):
    """Rule validation configuration."""
    regex: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    format: Optional[str] = None
    allowed_values: list[str] = Field(default_factory=list)


class RulePenalty(BaseModel):
    """Rule penalty configuration."""
    amount: int = 0
    currency: str = "INR"


class RuleCondition(BaseModel):
    """Conditional rule evaluation."""
    field: str
    operator: str  # eq, ne, in, contains, regex
    value: Any


class Rule(BaseDocument):
    """Compliance rule document model."""
    rule_id: str
    category: ProductCategory
    name: str
    description: Optional[str] = None
    field: str
    type: RuleType = RuleType.MANDATORY
    validation: RuleValidation = Field(default_factory=RuleValidation)
    penalty: RulePenalty = Field(default_factory=RulePenalty)
    legal_reference: Optional[str] = None
    weight: int = 1
    active: bool = True
    conditions: list[RuleCondition] = Field(default_factory=list)
    version: int = 1


# Crawl Queue Models
class CrawlJob(BaseDocument):
    """Crawl queue job model."""
    url: str
    priority: int = 1
    status: CrawlStatus = CrawlStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    seller_id: Optional[str] = None
    category: Optional[ProductCategory] = None
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error: Optional[str] = None


# API Request/Response Models
class AuditURLRequest(BaseModel):
    """Request model for URL audit."""
    url: str
    seller_id: str = "default"
    category: Optional[ProductCategory] = None


class BulkAuditRequest(BaseModel):
    """Request model for bulk URL audit."""
    urls: list[str]
    seller_id: str = "default"
    category: Optional[ProductCategory] = None


class AuditResponse(BaseModel):
    """Response model for audit result."""
    status: str
    audit_id: str
    product_id: str
    compliance_score: int
    risk_level: RiskLevel
    violations: list[Violation]
    extracted_fields: ExtractedFields


class AnalyticsSummary(BaseModel):
    """Analytics summary response."""
    total_audits: int
    compliant_count: int
    non_compliant_count: int
    compliance_rate: float
    risk_distribution: dict[str, int]
    category_stats: dict[str, dict[str, Any]]
    violation_trends: list[dict[str, Any]]
