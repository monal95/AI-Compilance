from io import BytesIO
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from backend.database import db_client
from backend.models import BatchScanResponse, ProductInput, ScanResponse, URLAuditRequest, URLAuditResponse
from backend.services.compliance_engine import ComplianceEngine
from backend.services.field_identification_service import FieldIdentificationService
from backend.services.ingestion_service import IngestionService
from backend.services.ocr_service import OCRService
from backend.services.reporting_service import ReportingService
from backend.services.url_audit_service import URLAuditService
from backend.services.validation_service import ValidationService
from backend.services.category_audit_service import (
    CategoryAuditService,
    CategoryAnalyticsService,
    ProductCategory,
)
from backend.services.advanced_ocr_service import (
    AdvancedOCRService,
    OCRProcessingResult,
    OCRRequest,
    ProductCategory as OCRProductCategory,
    get_advanced_ocr_service,
)

app = FastAPI(title="Legal Metrology Compliance Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

compliance_engine = ComplianceEngine()
ingestion_service = IngestionService()
reporting_service = ReportingService()
url_audit_service = URLAuditService()
ocr_service = OCRService()
field_identification_service = FieldIdentificationService()
validation_service = ValidationService()
category_audit_service = CategoryAuditService(max_workers=5)
advanced_ocr_service = get_advanced_ocr_service()


# Background task storage for bulk audits
bulk_audit_tasks: dict[str, dict] = {}


@app.on_event("startup")
async def on_startup() -> None:
    await db_client.connect()


@app.get("/")
async def root():
    return {
        "service": "Legal Metrology Compliance Intelligence API",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/diagnostic/ocr")
async def diagnostic_ocr():
    """Diagnostic endpoint to check OCR setup"""
    import subprocess
    
    diagnostics = {
        "tesseract_installed": False,
        "tesseract_version": None,
        "pytesseract_working": False,
        "error": None,
    }
    
    # Check if tesseract command exists
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            diagnostics["tesseract_installed"] = True
            diagnostics["tesseract_version"] = result.stdout.split("\n")[0]
    except Exception as e:
        diagnostics["error"] = f"Tesseract not found in PATH: {str(e)}"
    
    # Check if pytesseract can load
    try:
        import pytesseract
        from PIL import Image
        
        # Simple test
        img = Image.new("RGB", (100, 50), color="white")
        text = pytesseract.image_to_string(img)
        diagnostics["pytesseract_working"] = True
    except Exception as e:
        diagnostics["error"] = f"pytesseract error: {str(e)}"
    
    return diagnostics


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@app.post("/scan-product", response_model=ScanResponse)
async def scan_product(
    seller_id: str = Form(...),
    product_name: str = Form(...),
    description: str = Form(default=""),
    packaging_text: str = Form(default=""),
    image: UploadFile | None = File(default=None),
):
    payload = ProductInput(
        seller_id=seller_id,
        product_name=product_name,
        description=description,
        packaging_text=packaging_text,
    )

    image_bytes = await image.read() if image else None
    result = compliance_engine.run_scan(payload, image_bytes=image_bytes)
    await reporting_service.save_result(result)
    return ScanResponse(status="success", result=result)


@app.post("/batch-scan", response_model=BatchScanResponse)
async def batch_scan(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    raw = await file.read()
    products = ingestion_service.parse_batch_csv(raw)

    results = []
    for product in products:
        result = compliance_engine.run_scan(product)
        await reporting_service.save_result(result)
        results.append(result)

    return BatchScanResponse(status="success", total=len(results), results=results)


@app.get("/reports")
async def reports(risk_level: str | None = Query(default=None)):
    return await reporting_service.list_reports(risk_level=risk_level)


@app.get("/reports/export")
async def export_reports_csv():
    csv_content = await reporting_service.export_csv()
    return StreamingResponse(
        BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=compliance_reports.csv"},
    )


@app.post("/audit/url", response_model=URLAuditResponse)
async def audit_product_url(request: URLAuditRequest):
    try:
        # Pass category to audit service (auto-detects if not provided)
        category = request.category.value if request.category else None
        result = url_audit_service.audit(
            url=request.url, 
            seller_id=request.seller_id,
            category=category
        )
        await reporting_service.save_result(result)
        return URLAuditResponse(status="success", result=result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"URL audit failed: {exc}") from exc


@app.post("/audit/ocr")
async def ocr_extract_image(
    seller_id: str = Form(...), 
    image: UploadFile = File(...),
    category: str = Form(default=None)
):
    try:
        image_bytes = await image.read()
        extracted_text = ocr_service.extract_text(image_bytes)
        
        # Auto-detect category if not provided
        detected_category = category
        if not detected_category and extracted_text:
            detected_category = validation_service.detect_category(extracted_text)
        
        # Extract mandatory fields from OCR text with category context
        identified_fields = field_identification_service.extract_mandatory_fields(
            scraped_text="", 
            ocr_text=extracted_text,
            category=detected_category
        )
        
        # Validate with category-specific rules
        score, violations = validation_service.validate(
            fields=identified_fields,
            scraped_text="",
            ocr_text=extracted_text,
            category=detected_category
        )
        
        # Calculate confidence score based on multiple factors
        if not extracted_text:
            confidence_score = 0
        else:
            # Calculate base confidence from text characteristics
            word_count = len(extracted_text.split())
            
            # Confidence factors:
            # 1. Text length (optimal is 100-1000 words)
            if word_count >= 100:
                length_score = 100
            elif word_count >= 50:
                length_score = 80
            elif word_count >= 20:
                length_score = 60
            else:
                length_score = max(0, word_count * 2)
            
            # 2. Count how many fields were successfully identified
            field_dict = identified_fields.model_dump() if identified_fields else {}
            found_fields = sum(1 for v in field_dict.values() if v)
            total_fields = 6  # Base fields
            if detected_category == "food":
                total_fields = 14  # Food has more fields
            elif detected_category == "electronics":
                total_fields = 14
            elif detected_category == "cosmetics":
                total_fields = 12
            field_score = min(100, (found_fields / total_fields) * 100)
            
            # Combined confidence: weighted average
            confidence_score = int((length_score * 0.6 + field_score * 0.4))
        
        # Determine risk level from compliance score
        if score >= 85:
            risk_level = "Compliant"
        elif score >= 60:
            risk_level = "Moderate Risk"
        else:
            risk_level = "High Risk"
        
        return {
            "status": "success",
            "result": {
                "extracted_text": extracted_text,
                "confidence_score": confidence_score,
                "compliance_score": score,
                "risk_level": risk_level,
                "category": detected_category or "generic",
                "identified_fields": identified_fields.model_dump() if identified_fields else {},
                "violations": [v.model_dump() for v in violations],
                "seller_id": seller_id,
            }
        }
    except Exception as exc:
        import logging
        logging.error(f"OCR extraction error: {exc}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"OCR extraction failed: {str(exc)}") from exc


@app.get("/categories")
async def list_product_categories():
    """Get list of available product categories with their rule counts"""
    return {
        "status": "success",
        "categories": validation_service.get_available_categories()
    }


@app.get("/categories/{category_id}/rules")
async def get_category_rules(category_id: str):
    """Get detailed rules for a specific category"""
    summary = validation_service.get_category_summary(category_id)
    return {
        "status": "success",
        "category": summary
    }


@app.get("/audit/reports")
async def list_audit_reports(risk_level: str | None = Query(default=None)):
    return await reporting_service.list_reports(risk_level=risk_level)


@app.get("/audit/reports/{product_id}")
async def get_audit_report(product_id: str):
    report = await reporting_service.get_product(product_id)
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")
    return report


@app.get("/audit/stats")
async def get_audit_stats():
    return await reporting_service.get_dashboard_stats()


@app.get("/audit/export/csv")
async def export_audit_csv():
    csv_content = await reporting_service.export_csv()
    return StreamingResponse(
        BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_reports.csv"},
    )


@app.get("/audit/export/pdf")
async def export_audit_pdf():
    pdf_bytes = await reporting_service.export_pdf()
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=audit_reports.pdf"},
    )


@app.get("/product/{product_id}")
async def get_product(product_id: str):
    product = await reporting_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product report not found")
    return product


@app.get("/health")
async def health():
    return {"status": "ok"}


# ============================================
# Category-Based Bulk Audit Endpoints
# ============================================

@app.get("/audit/categories")
async def list_categories():
    """List available product categories for bulk audit"""
    return {
        "categories": [
            {"value": cat.value, "name": cat.name}
            for cat in ProductCategory
        ],
        "keywords": {
            cat.value: category_audit_service.get_category_keywords(cat)
            for cat in ProductCategory
            if cat != ProductCategory.CUSTOM
        }
    }


@app.post("/audit/category")
async def audit_by_category(
    background_tasks: BackgroundTasks,
    category: str = Form(...),
    max_products: int = Form(default=10),
    custom_keyword: Optional[str] = Form(default=None),
    marketplace: str = Form(default="amazon.in"),
    seller_id: str = Form(default="regulator-audit"),
):
    """
    Start a category-based bulk audit.
    Searches for products in the category and audits them in parallel.
    """
    import uuid
    
    # Map string to enum
    try:
        category_enum = ProductCategory(category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    task_id = str(uuid.uuid4())
    
    # Initialize task tracking
    bulk_audit_tasks[task_id] = {
        "status": "running",
        "category": category,
        "total": 0,
        "completed": 0,
        "failed": 0,
        "results": [],
        "errors": []
    }
    
    def run_bulk_audit():
        try:
            progress = category_audit_service.audit_by_category(
                category=category_enum,
                max_products=max_products,
                seller_id=seller_id,
                custom_keyword=custom_keyword,
                marketplace=marketplace
            )
            
            # Update task with results
            bulk_audit_tasks[task_id].update({
                "status": "completed",
                "total": progress.total,
                "completed": progress.completed,
                "failed": progress.failed,
                "results": [r.model_dump(mode="json") for r in progress.results],
                "errors": progress.errors
            })
            
            # Save results to database
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            for result in progress.results:
                loop.run_until_complete(reporting_service.save_result(result))
            loop.close()
            
        except Exception as e:
            bulk_audit_tasks[task_id].update({
                "status": "failed",
                "errors": [str(e)]
            })
    
    # Run in background
    background_tasks.add_task(run_bulk_audit)
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": f"Bulk audit started for category: {category}"
    }


@app.get("/audit/category/status/{task_id}")
async def get_bulk_audit_status(task_id: str):
    """Get the status of a bulk audit task"""
    if task_id not in bulk_audit_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return bulk_audit_tasks[task_id]


@app.post("/audit/bulk")
async def bulk_audit_urls(
    urls: list[str] = Form(...),
    seller_id: str = Form(default="regulator-audit"),
):
    """
    Audit multiple URLs in parallel.
    Synchronous endpoint - waits for all audits to complete.
    """
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    if len(urls) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 URLs per request")
    
    progress = category_audit_service.bulk_audit_urls(
        urls=urls,
        seller_id=seller_id
    )
    
    # Save results to database
    for result in progress.results:
        await reporting_service.save_result(result)
    
    return {
        "status": "completed",
        "total": progress.total,
        "completed": progress.completed,
        "failed": progress.failed,
        "results": [r.model_dump(mode="json") for r in progress.results],
        "errors": progress.errors
    }


# ============================================
# Enhanced Analytics Endpoints
# ============================================

@app.get("/analytics/summary")
async def get_analytics_summary():
    """Get comprehensive analytics summary"""
    analytics_service = CategoryAnalyticsService(db_client)
    
    stats = await reporting_service.get_dashboard_stats()
    risk_distribution = await analytics_service.get_risk_distribution()
    category_stats = await analytics_service.get_category_stats()
    violation_trends = await analytics_service.get_violation_trends()
    
    return {
        **stats,
        "risk_distribution": risk_distribution,
        "category_stats": category_stats,
        "violation_trends": violation_trends
    }


@app.get("/analytics/risk-distribution")
async def get_risk_distribution():
    """Get risk level distribution for charts"""
    analytics_service = CategoryAnalyticsService(db_client)
    return await analytics_service.get_risk_distribution()


@app.get("/analytics/category-stats")
async def get_category_statistics():
    """Get compliance statistics grouped by category"""
    analytics_service = CategoryAnalyticsService(db_client)
    return await analytics_service.get_category_stats()


@app.get("/analytics/violation-trends")
async def get_violation_trends():
    """Get most common violations with counts"""
    analytics_service = CategoryAnalyticsService(db_client)
    return await analytics_service.get_violation_trends()


@app.get("/analytics/timeline")
async def get_compliance_timeline(days: int = Query(default=30, ge=1, le=365)):
    """Get compliance scores over time for trend charts"""
    analytics_service = CategoryAnalyticsService(db_client)
    return await analytics_service.get_compliance_timeline(days=days)


# ============================================
# Advanced Filtering Endpoints
# ============================================

@app.get("/audit/reports/search")
async def search_audit_reports(
    risk_level: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    max_score: Optional[int] = Query(default=None, ge=0, le=100),
    seller_id: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Advanced search and filtering for audit reports.
    Supports filtering by risk level, category, score range, date range, and seller.
    """
    from datetime import datetime
    
    reports = await reporting_service.list_reports()
    
    # Apply filters
    filtered = []
    for report in reports:
        # Risk level filter
        if risk_level and report.get("risk_level") != risk_level:
            continue
        
        # Score range filter
        score = report.get("compliance_score", report.get("score", 0))
        if min_score is not None and score < min_score:
            continue
        if max_score is not None and score > max_score:
            continue
        
        # Seller ID filter
        if seller_id and report.get("seller_id") != seller_id:
            continue
        
        # Date range filter
        created_at = report.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            if date_from:
                from_date = datetime.fromisoformat(date_from)
                if created_at < from_date:
                    continue
            
            if date_to:
                to_date = datetime.fromisoformat(date_to)
                if created_at > to_date:
                    continue
        
        # Category filter (infer from title)
        if category:
            title = (report.get("scraped_data", {}).get("title") or 
                     report.get("product_name") or "").lower()
            if category.lower() not in title:
                continue
        
        filtered.append(report)
    
    # Sort by date (newest first)
    filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Pagination
    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": paginated
    }


# ============================================================================
# Advanced OCR Microservice API Endpoints
# ============================================================================

@app.post("/ocr/process", response_model=OCRProcessingResult, tags=["OCR"])
async def process_ocr(
    image: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    category: str | None = Form(default=None),
):
    """
    Process an image for OCR extraction using bounding-box region segmentation.
    
    This endpoint performs advanced OCR with:
    - Image preprocessing (grayscale, blur, adaptive thresholding)
    - Bounding box detection for text regions
    - Region-wise OCR with confidence scoring
    - Structured compliance field extraction (MRP, Net Qty, Dates, etc.)
    - Confidence aggregation and quality flagging
    
    Args:
        image: Image file upload (multipart/form-data)
        image_url: URL of the image to process (alternative to file upload)
        category: Product category (food, electronics, cosmetics, generic)
    
    Returns:
        OCRProcessingResult with structured fields and confidence metrics
    """
    # Validate input
    if not image and not image_url:
        raise HTTPException(
            status_code=400, 
            detail="Either 'image' file or 'image_url' must be provided"
        )
    
    # Parse category
    ocr_category = None
    if category:
        try:
            ocr_category = OCRProductCategory(category.lower())
        except ValueError:
            pass  # Use None for unknown categories
    
    # Process image
    if image:
        image_bytes = await image.read()
        result = advanced_ocr_service.process_image(image_bytes, ocr_category)
    else:
        result = await advanced_ocr_service.process_image_url(image_url, ocr_category)
    
    return result


@app.post("/ocr/process-url", response_model=OCRProcessingResult, tags=["OCR"])
async def process_ocr_url(request: OCRRequest):
    """
    Process an image from URL for OCR extraction.
    
    Alternative endpoint accepting JSON body instead of form data.
    
    Args:
        request: OCRRequest with image_url and optional category
    
    Returns:
        OCRProcessingResult with structured fields and confidence metrics
    """
    if not request.image_url and not request.image_path:
        raise HTTPException(
            status_code=400,
            detail="Either 'image_url' or 'image_path' must be provided"
        )
    
    # Convert category
    ocr_category = None
    if request.category:
        ocr_category = OCRProductCategory(request.category.value)
    
    if request.image_url:
        result = await advanced_ocr_service.process_image_url(
            request.image_url, 
            ocr_category
        )
    else:
        result = advanced_ocr_service.process_image_path(
            request.image_path,
            ocr_category
        )
    
    return result


@app.post("/ocr/batch", tags=["OCR"])
async def process_ocr_batch(
    images: list[UploadFile] = File(...),
    category: str | None = Form(default=None),
):
    """
    Process multiple images for OCR extraction.
    
    Args:
        images: List of image files to process
        category: Product category to apply to all images
    
    Returns:
        List of OCRProcessingResult for each image
    """
    # Parse category
    ocr_category = None
    if category:
        try:
            ocr_category = OCRProductCategory(category.lower())
        except ValueError:
            pass
    
    results = []
    for image in images:
        image_bytes = await image.read()
        result = advanced_ocr_service.process_image(image_bytes, ocr_category)
        results.append({
            "filename": image.filename,
            "result": result.model_dump()
        })
    
    return {
        "total": len(results),
        "results": results
    }


@app.get("/ocr/health", tags=["OCR"])
async def ocr_health_check():
    """
    Check the health status of the OCR microservice.
    
    Returns:
        Health status including Tesseract availability
    """
    import subprocess
    
    health = {
        "status": "healthy",
        "tesseract_available": False,
        "tesseract_version": None,
        "opencv_available": False,
        "opencv_version": None,
    }
    
    # Check Tesseract
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            health["tesseract_available"] = True
            health["tesseract_version"] = result.stdout.split("\n")[0]
    except Exception:
        health["status"] = "degraded"
    
    # Check OpenCV
    try:
        import cv2
        health["opencv_available"] = True
        health["opencv_version"] = cv2.__version__
    except ImportError:
        health["status"] = "degraded"
    
    return health


@app.get("/ocr/supported-fields", tags=["OCR"])
async def get_supported_fields():
    """
    Get list of compliance fields that can be extracted by the OCR service.
    
    Returns:
        List of supported fields with descriptions
    """
    return {
        "fields": [
            {"name": "mrp", "description": "Maximum Retail Price (₹)", "category": "all"},
            {"name": "net_quantity", "description": "Net weight/volume (g, kg, ml, L)", "category": "all"},
            {"name": "manufacture_date", "description": "Date of manufacture/packing", "category": "all"},
            {"name": "expiry_date", "description": "Expiry/Best before date", "category": "all"},
            {"name": "country_of_origin", "description": "Country where product was made", "category": "all"},
            {"name": "manufacturer", "description": "Manufacturer/Packer name and address", "category": "all"},
            {"name": "importer", "description": "Importer details (for imported products)", "category": "all"},
            {"name": "consumer_care", "description": "Consumer helpline/contact number", "category": "all"},
            {"name": "batch_number", "description": "Batch/Lot number", "category": "all"},
            {"name": "fssai_license", "description": "FSSAI License number (14 digits)", "category": "food"},
            {"name": "bis_certification", "description": "BIS/ISI certification number", "category": "electronics"},
        ],
        "categories": ["food", "electronics", "cosmetics", "generic"],
        "confidence_levels": [
            {"level": "HIGH_CONFIDENCE", "threshold": "≥ 85%", "action": "Auto-approve"},
            {"level": "MEDIUM_CONFIDENCE", "threshold": "70-84%", "action": "Review recommended"},
            {"level": "LOW_CONFIDENCE", "threshold": "50-69%", "action": "Manual review required"},
            {"level": "VERY_LOW_CONFIDENCE", "threshold": "< 50%", "action": "Re-capture image"},
        ]
    }

