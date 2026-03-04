"""
Compliance Engine Service - Orchestrates compliance checking.

Features:
- Orchestrates OCR + NLP + Rule Engine
- Calculates compliance scores
- Detects violations
- Generates compliance reports
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import logging
import httpx
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Compliance Engine Service",
    description="Orchestrates compliance checking and scoring",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs (configurable via env)
OCR_SERVICE_URL = "http://localhost:8002"
NLP_SERVICE_URL = "http://localhost:8003"
RULE_ENGINE_URL = "http://localhost:8005"


# Enums
class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    COMPLIANT = "compliant"


class AuditStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Models
class ProductData(BaseModel):
    name: str
    url: Optional[str] = None
    category: str = "general"
    extracted_text: Optional[str] = None
    fields: Optional[dict] = None
    metadata: Optional[dict] = None


class ImageAuditRequest(BaseModel):
    image_data: str  # Base64 encoded
    product_name: str
    category: str = "food"
    languages: list[str] = ["eng", "hin"]


class TextAuditRequest(BaseModel):
    text: str
    product_name: str
    category: str = "food"


class UrlAuditRequest(BaseModel):
    url: str
    product_name: Optional[str] = None
    category: str = "food"


class ViolationDetail(BaseModel):
    rule_id: str
    rule_name: str
    severity: str
    message: str
    field: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None


class ComplianceReport(BaseModel):
    audit_id: str
    product_name: str
    category: str
    status: AuditStatus
    risk_level: RiskLevel
    compliance_score: float
    total_rules_checked: int
    rules_passed: int
    rules_failed: int
    violations: list[ViolationDetail]
    extracted_fields: dict
    recommendations: list[str]
    created_at: datetime
    processing_time_ms: int


# In-memory audit store
audits_db: dict[str, dict] = {}
audit_counter = 0


def get_next_audit_id() -> str:
    global audit_counter
    audit_counter += 1
    return f"audit_{audit_counter:08d}"


def calculate_risk_level(compliance_score: float, critical_violations: int) -> RiskLevel:
    """Calculate risk level based on score and violations."""
    if critical_violations > 0:
        return RiskLevel.CRITICAL
    if compliance_score >= 90:
        return RiskLevel.COMPLIANT
    if compliance_score >= 70:
        return RiskLevel.LOW
    if compliance_score >= 50:
        return RiskLevel.MEDIUM
    if compliance_score >= 30:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


def generate_recommendations(violations: list[dict], fields: dict) -> list[str]:
    """Generate actionable recommendations based on violations."""
    recommendations = []
    
    # Check for missing FSSAI
    if not fields.get('fssai'):
        recommendations.append(
            "CRITICAL: Add FSSAI license number (14 digits) prominently on product packaging"
        )
    
    # Check for missing MRP
    if not fields.get('mrp'):
        recommendations.append(
            "CRITICAL: Display Maximum Retail Price (MRP) with 'Rs.' or '₹' symbol"
        )
    
    # Check for missing expiry
    if not fields.get('expiry_date'):
        recommendations.append(
            "HIGH: Add expiry date or 'Best Before' date in DD/MM/YYYY format"
        )
    
    # Check for missing manufacturing date
    if not fields.get('manufacturing_date'):
        recommendations.append(
            "MEDIUM: Include manufacturing date (Mfg Date or MFD)"
        )
    
    # Check for missing net weight
    if not fields.get('net_weight'):
        recommendations.append(
            "HIGH: Display net weight/quantity with appropriate unit (g, kg, ml, L)"
        )
    
    # Check for missing country of origin
    if not fields.get('country'):
        recommendations.append(
            "MEDIUM: Add 'Country of Origin' or 'Made in' information"
        )
    
    # Add generic recommendations based on violations
    for v in violations[:3]:  # Top 3 violations
        if v.get('message') and v['message'] not in recommendations:
            recommendations.append(f"FIX: {v['message']}")
    
    return recommendations


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "compliance-engine"}


@app.post("/compliance/audit/text", response_model=ComplianceReport)
async def audit_text(request: TextAuditRequest):
    """
    Audit product text for compliance.
    
    1. Normalize text via NLP service
    2. Extract entities
    3. Run rules against extracted data
    4. Calculate compliance score
    5. Generate report
    """
    start_time = datetime.utcnow()
    audit_id = get_next_audit_id()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: NLP Analysis
            nlp_response = await client.post(
                f"{NLP_SERVICE_URL}/nlp/analyze",
                json={"text": request.text, "language": "english"}
            )
            
            if nlp_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"NLP service error: {nlp_response.text}"
                )
            
            nlp_data = nlp_response.json()
            entities = nlp_data.get('entities', {})
            
            # Step 2: Execute rules
            rule_data = {
                'fssai': entities.get('fssai', {}).get('value') if entities.get('fssai') else None,
                'mrp': entities.get('price', {}).get('value') if entities.get('price') else None,
                'expiry_date': entities.get('dates', {}).get('expiry_date', {}).get('parsed') if entities.get('dates', {}).get('expiry_date') else None,
                'manufacturing_date': entities.get('dates', {}).get('manufacturing_date', {}).get('parsed') if entities.get('dates', {}).get('manufacturing_date') else None,
                'net_weight': entities.get('weight', {}).get('value') if entities.get('weight') else None,
                'batch': entities.get('batch', {}).get('value') if entities.get('batch') else None,
                'country': entities.get('country', {}).get('value') if entities.get('country') else None,
            }
            
            rules_response = await client.post(
                f"{RULE_ENGINE_URL}/rules/execute",
                json={"category": request.category, "data": rule_data}
            )
            
            if rules_response.status_code != 200:
                # Continue even if rule engine is unavailable
                logger.warning(f"Rule engine error: {rules_response.text}")
                rules_data = {"total_rules": 0, "passed": 0, "failed": 0, "results": []}
            else:
                rules_data = rules_response.json()
            
            # Step 3: Calculate compliance score
            total_rules = rules_data.get('total_rules', 0)
            passed = rules_data.get('passed', 0)
            failed = rules_data.get('failed', 0)
            
            if total_rules > 0:
                compliance_score = (passed / total_rules) * 100
            else:
                # Calculate based on extracted fields
                extracted_count = sum(1 for v in rule_data.values() if v)
                compliance_score = (extracted_count / 7) * 100  # 7 key fields
            
            # Step 4: Extract violations
            violations = []
            critical_count = 0
            
            for result in rules_data.get('results', []):
                if result.get('status') == 'failed':
                    severity = result.get('severity', 'medium')
                    if severity == 'critical':
                        critical_count += 1
                    
                    for msg in result.get('messages', []):
                        violations.append(ViolationDetail(
                            rule_id=result.get('rule_id', ''),
                            rule_name=result.get('rule_name', ''),
                            severity=severity,
                            message=msg,
                        ))
            
            # Step 5: Generate report
            risk_level = calculate_risk_level(compliance_score, critical_count)
            recommendations = generate_recommendations(
                [v.model_dump() for v in violations],
                rule_data
            )
            
            end_time = datetime.utcnow()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            report = ComplianceReport(
                audit_id=audit_id,
                product_name=request.product_name,
                category=request.category,
                status=AuditStatus.COMPLETED,
                risk_level=risk_level,
                compliance_score=round(compliance_score, 1),
                total_rules_checked=total_rules,
                rules_passed=passed,
                rules_failed=failed,
                violations=violations,
                extracted_fields=rule_data,
                recommendations=recommendations,
                created_at=start_time,
                processing_time_ms=processing_time,
            )
            
            # Store audit
            audits_db[audit_id] = report.model_dump()
            
            return report
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compliance/audit/image", response_model=ComplianceReport)
async def audit_image(request: ImageAuditRequest):
    """
    Audit product image for compliance.
    
    1. Send image to OCR service
    2. Extract text and fields
    3. Run NLP analysis
    4. Execute compliance rules
    5. Generate report
    """
    start_time = datetime.utcnow()
    audit_id = get_next_audit_id()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: OCR Processing
            import base64
            image_bytes = base64.b64decode(request.image_data)
            
            ocr_response = await client.post(
                f"{OCR_SERVICE_URL}/ocr/process",
                files={"file": ("image.jpg", image_bytes, "image/jpeg")},
                data={"languages": ",".join(request.languages)}
            )
            
            if ocr_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"OCR service error: {ocr_response.text}"
                )
            
            ocr_data = ocr_response.json()
            extracted_text = ocr_data.get('text', '')
            extracted_fields = ocr_data.get('fields', {})
            
            # Step 2: Additional NLP analysis
            nlp_response = await client.post(
                f"{NLP_SERVICE_URL}/nlp/analyze",
                json={"text": extracted_text, "language": "english"}
            )
            
            if nlp_response.status_code == 200:
                nlp_data = nlp_response.json()
                entities = nlp_data.get('entities', {})
                # Merge with OCR extracted fields
                for key, value in entities.items():
                    if value and key not in extracted_fields:
                        extracted_fields[key] = value
            
            # Step 3: Prepare data for rule engine
            rule_data = {
                'fssai': extracted_fields.get('fssai', {}).get('value') if isinstance(extracted_fields.get('fssai'), dict) else extracted_fields.get('fssai'),
                'mrp': extracted_fields.get('mrp', {}).get('value') if isinstance(extracted_fields.get('mrp'), dict) else extracted_fields.get('mrp'),
                'expiry_date': extracted_fields.get('dates', {}).get('expiry_date', {}).get('parsed') if extracted_fields.get('dates') else None,
                'manufacturing_date': extracted_fields.get('dates', {}).get('manufacturing_date', {}).get('parsed') if extracted_fields.get('dates') else None,
                'net_weight': extracted_fields.get('net_weight', {}).get('value') if isinstance(extracted_fields.get('net_weight'), dict) else extracted_fields.get('net_weight'),
                'batch': extracted_fields.get('batch_number', {}).get('value') if isinstance(extracted_fields.get('batch_number'), dict) else extracted_fields.get('batch_number'),
                'country': extracted_fields.get('country_of_origin', {}).get('value') if isinstance(extracted_fields.get('country_of_origin'), dict) else extracted_fields.get('country_of_origin'),
            }
            
            # Step 4: Execute rules
            rules_response = await client.post(
                f"{RULE_ENGINE_URL}/rules/execute",
                json={"category": request.category, "data": rule_data}
            )
            
            if rules_response.status_code == 200:
                rules_data = rules_response.json()
            else:
                rules_data = {"total_rules": 0, "passed": 0, "failed": 0, "results": []}
            
            # Step 5: Calculate compliance
            total_rules = rules_data.get('total_rules', 0)
            passed = rules_data.get('passed', 0)
            failed = rules_data.get('failed', 0)
            
            if total_rules > 0:
                compliance_score = (passed / total_rules) * 100
            else:
                extracted_count = sum(1 for v in rule_data.values() if v)
                compliance_score = (extracted_count / 7) * 100
            
            # Extract violations
            violations = []
            critical_count = 0
            
            for result in rules_data.get('results', []):
                if result.get('status') == 'failed':
                    severity = result.get('severity', 'medium')
                    if severity == 'critical':
                        critical_count += 1
                    
                    for msg in result.get('messages', []):
                        violations.append(ViolationDetail(
                            rule_id=result.get('rule_id', ''),
                            rule_name=result.get('rule_name', ''),
                            severity=severity,
                            message=msg,
                        ))
            
            # Generate report
            risk_level = calculate_risk_level(compliance_score, critical_count)
            recommendations = generate_recommendations(
                [v.model_dump() for v in violations],
                rule_data
            )
            
            end_time = datetime.utcnow()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            report = ComplianceReport(
                audit_id=audit_id,
                product_name=request.product_name,
                category=request.category,
                status=AuditStatus.COMPLETED,
                risk_level=risk_level,
                compliance_score=round(compliance_score, 1),
                total_rules_checked=total_rules,
                rules_passed=passed,
                rules_failed=failed,
                violations=violations,
                extracted_fields=rule_data,
                recommendations=recommendations,
                created_at=start_time,
                processing_time_ms=processing_time,
            )
            
            audits_db[audit_id] = report.model_dump()
            
            return report
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except Exception as e:
        logger.error(f"Image audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compliance/audit/{audit_id}")
async def get_audit(audit_id: str):
    """Get audit report by ID."""
    if audit_id not in audits_db:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    return audits_db[audit_id]


@app.get("/compliance/audits")
async def list_audits(
    skip: int = 0,
    limit: int = 20,
    risk_level: Optional[RiskLevel] = None,
):
    """List recent audits."""
    audits = list(audits_db.values())
    
    if risk_level:
        audits = [a for a in audits if a.get('risk_level') == risk_level.value]
    
    # Sort by created_at desc
    audits.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return {
        "total": len(audits),
        "audits": audits[skip:skip + limit]
    }


@app.get("/compliance/stats")
async def get_compliance_stats():
    """Get compliance statistics."""
    audits = list(audits_db.values())
    
    if not audits:
        return {
            "total_audits": 0,
            "average_score": 0,
            "by_risk_level": {},
            "by_category": {},
        }
    
    scores = [a.get('compliance_score', 0) for a in audits]
    avg_score = sum(scores) / len(scores)
    
    by_risk = {}
    by_category = {}
    
    for audit in audits:
        risk = audit.get('risk_level', 'unknown')
        by_risk[risk] = by_risk.get(risk, 0) + 1
        
        cat = audit.get('category', 'unknown')
        by_category[cat] = by_category.get(cat, 0) + 1
    
    return {
        "total_audits": len(audits),
        "average_score": round(avg_score, 1),
        "by_risk_level": by_risk,
        "by_category": by_category,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
