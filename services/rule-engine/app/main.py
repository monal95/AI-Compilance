"""
Rule Engine Service for managing compliance rules.

Features:
- CRUD operations for rules
- Rule validation and execution
- Category-based rule management
- Version control for rules
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import logging
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from rule_executor import RuleExecutor
from rule_validator import RuleValidator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Rule Engine Service",
    description="Compliance rule management and execution",
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

# Initialize components
rule_executor = RuleExecutor()
rule_validator = RuleValidator()


# Enums
class RuleType(str, Enum):
    REQUIRED_FIELD = "required_field"
    FORMAT_VALIDATION = "format_validation"
    RANGE_CHECK = "range_check"
    EXPIRY_CHECK = "expiry_check"
    PATTERN_MATCH = "pattern_match"
    CROSS_FIELD = "cross_field"
    CUSTOM = "custom"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RuleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


# Request/Response models
class RuleCondition(BaseModel):
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, contains, regex, exists
    value: Optional[str | int | float | bool] = None
    value_field: Optional[str] = None  # For cross-field validation


class RuleAction(BaseModel):
    type: str  # flag, warning, error, auto_fix
    message: str
    fix_value: Optional[str] = None


class RuleBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    rule_type: RuleType
    category: str = Field(..., min_length=2, max_length=50)
    severity: Severity = Severity.MEDIUM
    conditions: list[RuleCondition]
    actions: list[RuleAction]
    tags: list[str] = []
    applicable_to: list[str] = []  # Product categories this rule applies to
    status: RuleStatus = RuleStatus.DRAFT


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    rule_type: Optional[RuleType] = None
    category: Optional[str] = None
    severity: Optional[Severity] = None
    conditions: Optional[list[RuleCondition]] = None
    actions: Optional[list[RuleAction]] = None
    tags: Optional[list[str]] = None
    applicable_to: Optional[list[str]] = None
    status: Optional[RuleStatus] = None


class RuleResponse(RuleBase):
    id: str
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: str = "system"


class ExecuteRuleRequest(BaseModel):
    rule_id: Optional[str] = None
    rule_ids: Optional[list[str]] = None
    category: Optional[str] = None
    data: dict  # Product data to validate


class ExecuteRuleResponse(BaseModel):
    total_rules: int
    passed: int
    failed: int
    warnings: int
    results: list[dict]


# In-memory rule store (would be MongoDB in production)
rules_db: dict[str, dict] = {}
rule_counter = 0


def get_next_id() -> str:
    global rule_counter
    rule_counter += 1
    return f"rule_{rule_counter:06d}"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rule-engine"}


@app.post("/rules", response_model=RuleResponse)
async def create_rule(rule: RuleCreate):
    """Create a new compliance rule."""
    try:
        # Validate rule
        validation = rule_validator.validate_rule(rule.model_dump())
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['errors'])
        
        rule_id = get_next_id()
        now = datetime.utcnow()
        
        rule_dict = rule.model_dump()
        rule_dict.update({
            'id': rule_id,
            'version': 1,
            'created_at': now,
            'updated_at': now,
            'created_by': 'system',
        })
        
        rules_db[rule_id] = rule_dict
        logger.info(f"Created rule: {rule_id}")
        
        return RuleResponse(**rule_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rules", response_model=list[RuleResponse])
async def list_rules(
    category: Optional[str] = None,
    status: Optional[RuleStatus] = None,
    severity: Optional[Severity] = None,
    rule_type: Optional[RuleType] = None,
    tag: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List rules with optional filters."""
    filtered = []
    
    for rule in rules_db.values():
        if category and rule.get('category') != category:
            continue
        if status and rule.get('status') != status.value:
            continue
        if severity and rule.get('severity') != severity.value:
            continue
        if rule_type and rule.get('rule_type') != rule_type.value:
            continue
        if tag and tag not in rule.get('tags', []):
            continue
        filtered.append(rule)
    
    # Sort by created_at desc
    filtered.sort(key=lambda x: x['created_at'], reverse=True)
    
    return [RuleResponse(**r) for r in filtered[skip:skip + limit]]


@app.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str):
    """Get a specific rule by ID."""
    if rule_id not in rules_db:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return RuleResponse(**rules_db[rule_id])


@app.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: str, update: RuleUpdate):
    """Update an existing rule."""
    if rule_id not in rules_db:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule = rules_db[rule_id]
    update_data = update.model_dump(exclude_unset=True)
    
    if update_data:
        # Validate updated rule
        merged = {**rule, **update_data}
        validation = rule_validator.validate_rule(merged)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['errors'])
        
        rule.update(update_data)
        rule['version'] += 1
        rule['updated_at'] = datetime.utcnow()
        
        logger.info(f"Updated rule: {rule_id} to version {rule['version']}")
    
    return RuleResponse(**rule)


@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete a rule."""
    if rule_id not in rules_db:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    del rules_db[rule_id]
    logger.info(f"Deleted rule: {rule_id}")
    
    return {"message": "Rule deleted", "id": rule_id}


@app.post("/rules/{rule_id}/activate")
async def activate_rule(rule_id: str):
    """Activate a rule."""
    if rule_id not in rules_db:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rules_db[rule_id]['status'] = RuleStatus.ACTIVE.value
    rules_db[rule_id]['updated_at'] = datetime.utcnow()
    
    return {"message": "Rule activated", "id": rule_id}


@app.post("/rules/{rule_id}/deactivate")
async def deactivate_rule(rule_id: str):
    """Deactivate a rule."""
    if rule_id not in rules_db:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rules_db[rule_id]['status'] = RuleStatus.INACTIVE.value
    rules_db[rule_id]['updated_at'] = datetime.utcnow()
    
    return {"message": "Rule deactivated", "id": rule_id}


@app.post("/rules/execute", response_model=ExecuteRuleResponse)
async def execute_rules(request: ExecuteRuleRequest):
    """
    Execute rules against product data.
    
    Can execute:
    - A specific rule by rule_id
    - Multiple rules by rule_ids
    - All active rules for a category
    """
    try:
        rules_to_execute = []
        
        if request.rule_id:
            if request.rule_id in rules_db:
                rules_to_execute.append(rules_db[request.rule_id])
        
        elif request.rule_ids:
            for rid in request.rule_ids:
                if rid in rules_db:
                    rules_to_execute.append(rules_db[rid])
        
        elif request.category:
            for rule in rules_db.values():
                if (rule.get('status') == RuleStatus.ACTIVE.value and 
                    (rule.get('category') == request.category or 
                     request.category in rule.get('applicable_to', []))):
                    rules_to_execute.append(rule)
        
        else:
            # Execute all active rules
            rules_to_execute = [
                r for r in rules_db.values()
                if r.get('status') == RuleStatus.ACTIVE.value
            ]
        
        if not rules_to_execute:
            return ExecuteRuleResponse(
                total_rules=0,
                passed=0,
                failed=0,
                warnings=0,
                results=[]
            )
        
        # Execute rules
        results = []
        passed = 0
        failed = 0
        warnings = 0
        
        for rule in rules_to_execute:
            result = rule_executor.execute(rule, request.data)
            results.append(result)
            
            if result['status'] == 'passed':
                passed += 1
            elif result['status'] == 'failed':
                failed += 1
            elif result['status'] == 'warning':
                warnings += 1
        
        return ExecuteRuleResponse(
            total_rules=len(rules_to_execute),
            passed=passed,
            failed=failed,
            warnings=warnings,
            results=results
        )
    
    except Exception as e:
        logger.error(f"Rule execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rules/categories/list")
async def list_categories():
    """Get list of rule categories."""
    categories = set()
    for rule in rules_db.values():
        if rule.get('category'):
            categories.add(rule['category'])
    
    return {"categories": sorted(categories)}


@app.get("/rules/stats")
async def get_rule_stats():
    """Get rule statistics."""
    stats = {
        'total': len(rules_db),
        'by_status': {},
        'by_severity': {},
        'by_type': {},
        'by_category': {},
    }
    
    for rule in rules_db.values():
        # By status
        status = rule.get('status', 'unknown')
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # By severity
        severity = rule.get('severity', 'unknown')
        stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        # By type
        rule_type = rule.get('rule_type', 'unknown')
        stats['by_type'][rule_type] = stats['by_type'].get(rule_type, 0) + 1
        
        # By category
        category = rule.get('category', 'unknown')
        stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
    
    return stats


# Initialize with default rules
def init_default_rules():
    """Initialize with basic compliance rules."""
    default_rules = [
        {
            'name': 'FSSAI Number Required',
            'description': 'All food products must display a valid 14-digit FSSAI license number',
            'rule_type': RuleType.REQUIRED_FIELD.value,
            'category': 'food_safety',
            'severity': Severity.CRITICAL.value,
            'conditions': [
                {'field': 'fssai', 'operator': 'exists', 'value': True}
            ],
            'actions': [
                {'type': 'error', 'message': 'FSSAI license number is missing'}
            ],
            'tags': ['fssai', 'mandatory'],
            'applicable_to': ['food', 'beverages'],
            'status': RuleStatus.ACTIVE.value,
        },
        {
            'name': 'FSSAI Format Validation',
            'description': 'FSSAI number must be exactly 14 digits',
            'rule_type': RuleType.FORMAT_VALIDATION.value,
            'category': 'food_safety',
            'severity': Severity.HIGH.value,
            'conditions': [
                {'field': 'fssai', 'operator': 'regex', 'value': r'^\d{14}$'}
            ],
            'actions': [
                {'type': 'error', 'message': 'FSSAI number format is invalid'}
            ],
            'tags': ['fssai', 'format'],
            'applicable_to': ['food', 'beverages'],
            'status': RuleStatus.ACTIVE.value,
        },
        {
            'name': 'MRP Required',
            'description': 'All products must display Maximum Retail Price',
            'rule_type': RuleType.REQUIRED_FIELD.value,
            'category': 'pricing',
            'severity': Severity.CRITICAL.value,
            'conditions': [
                {'field': 'mrp', 'operator': 'exists', 'value': True}
            ],
            'actions': [
                {'type': 'error', 'message': 'MRP is missing'}
            ],
            'tags': ['mrp', 'mandatory'],
            'applicable_to': ['all'],
            'status': RuleStatus.ACTIVE.value,
        },
        {
            'name': 'Expiry Date Required',
            'description': 'Food products must display expiry or best before date',
            'rule_type': RuleType.REQUIRED_FIELD.value,
            'category': 'food_safety',
            'severity': Severity.CRITICAL.value,
            'conditions': [
                {'field': 'expiry_date', 'operator': 'exists', 'value': True}
            ],
            'actions': [
                {'type': 'error', 'message': 'Expiry date is missing'}
            ],
            'tags': ['expiry', 'mandatory'],
            'applicable_to': ['food', 'beverages', 'medicine'],
            'status': RuleStatus.ACTIVE.value,
        },
        {
            'name': 'Net Weight Required',
            'description': 'Products must display net weight or quantity',
            'rule_type': RuleType.REQUIRED_FIELD.value,
            'category': 'packaging',
            'severity': Severity.HIGH.value,
            'conditions': [
                {'field': 'net_weight', 'operator': 'exists', 'value': True}
            ],
            'actions': [
                {'type': 'error', 'message': 'Net weight/quantity is missing'}
            ],
            'tags': ['weight', 'mandatory'],
            'applicable_to': ['food', 'beverages'],
            'status': RuleStatus.ACTIVE.value,
        },
    ]
    
    for rule_data in default_rules:
        rule_id = get_next_id()
        now = datetime.utcnow()
        rule_data.update({
            'id': rule_id,
            'version': 1,
            'created_at': now,
            'updated_at': now,
            'created_by': 'system',
        })
        rules_db[rule_id] = rule_data
    
    logger.info(f"Initialized {len(default_rules)} default rules")


@app.on_event("startup")
async def startup():
    """Initialize default rules on startup."""
    init_default_rules()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
