from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    COMPLIANT = "Compliant"
    MODERATE = "Moderate Risk"
    HIGH = "High Risk"


class ProductInput(BaseModel):
    seller_id: str = Field(..., description="Seller account identifier")
    product_name: str
    description: str | None = None
    packaging_text: str | None = None


class ExtractedFields(BaseModel):
    mrp: str | None = None
    quantity: str | None = None
    manufacturer: str | None = None
    country_of_origin: str | None = None


class Violation(BaseModel):
    code: str
    field: str
    message: str
    penalty: int


class ComplianceResult(BaseModel):
    product_id: str
    seller_id: str
    product_name: str
    extracted_fields: ExtractedFields
    violations: list[Violation]
    legal_clauses: list[str]
    llm_explanation: str
    suggested_correction: str
    risk_summary: str
    score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScanResponse(BaseModel):
    status: str
    result: ComplianceResult


class BatchScanResponse(BaseModel):
    status: str
    total: int
    results: list[ComplianceResult]


class DashboardMetrics(BaseModel):
    total_scanned: int
    compliant_count: int
    compliance_rate: float
    risk_distribution: dict[str, int]


class ProductRecord(BaseModel):
    id: str
    payload: dict[str, Any]


class ProductCategory(str, Enum):
    FOOD = "food"
    ELECTRONICS = "electronics"
    COSMETICS = "cosmetics"
    GENERIC = "generic"


class URLAuditRequest(BaseModel):
    url: str
    seller_id: str = "seller-001"
    category: ProductCategory | None = None  # Optional, will auto-detect if not provided


class ScrapedProductData(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None
    specifications: dict[str, str] = Field(default_factory=dict)
    image_urls: list[str] = Field(default_factory=list)
    raw_text: str = ""


class MandatoryDeclarations(BaseModel):
    # Universal fields
    manufacturer_or_importer: str | None = None
    manufacturer_address: str | None = None
    importer_address: str | None = None
    common_generic_name: str | None = None
    net_quantity: str | None = None
    net_quantity_prohibited_expressions: list[str] | None = None
    net_quantity_unit_valid: bool | None = None
    mrp_inclusive_of_taxes: str | None = None
    consumer_care_information: str | None = None
    date_of_manufacture_or_import: str | None = None
    country_of_origin: str | None = None
    
    # Food-specific fields
    fssai_license: str | None = None
    expiry_date: str | None = None
    ingredients_list: str | None = None
    nutritional_info: str | None = None
    allergen_info: str | None = None
    veg_nonveg_symbol: str | None = None
    batch_lot_number: str | None = None
    storage_instructions: str | None = None
    
    # Electronics-specific fields
    bis_certification: str | None = None
    model_number: str | None = None
    warranty_period: str | None = None
    power_rating: str | None = None
    voltage_frequency: str | None = None
    energy_rating: str | None = None
    serial_number: str | None = None
    safety_instructions: str | None = None
    
    # Cosmetics-specific fields  
    usage_instructions: str | None = None
    warnings: str | None = None
    cruelty_free: str | None = None


class URLAuditResult(BaseModel):
    product_id: str
    seller_id: str
    category: ProductCategory = ProductCategory.GENERIC
    compliance_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    scraped_data: ScrapedProductData
    ocr_text: str = ""
    identified_fields: MandatoryDeclarations
    violations: list[Violation]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class URLAuditResponse(BaseModel):
    status: str
    result: URLAuditResult
