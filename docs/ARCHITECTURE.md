# Enterprise Product Compliance Monitoring System - Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL LAYER                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │   React     │  │   Mobile    │  │  Streamlit  │  │    External Integrations    │ │
│  │  Dashboard  │  │    App      │  │  Analytics  │  │  (Flipkart, Amazon APIs)    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────────┬──────────────┘ │
└─────────┼────────────────┼────────────────┼────────────────────────┼────────────────┘
          │                │                │                        │
          ▼                ▼                ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (FastAPI)                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Rate Limiting  • Authentication  • Request Routing  • Load Balancing      │   │
│  │  • API Versioning • CORS Handler   • Request Validation • Response Caching   │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          ▼                             ▼                             ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   CRAWLER SERVICE   │   │    OCR SERVICE      │   │   NLP SERVICE       │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │ Scrapy Engine │  │   │  │ Tesseract OCR │  │   │  │ spaCy/NLTK    │  │
│  │ Async Fetcher │  │   │  │ OpenCV Preproc│  │   │  │ Regex Engine  │  │
│  │ URL Queue     │  │   │  │ Multi-Lang    │  │   │  │ Entity Extract│  │
│  │ Rate Limiter  │  │   │  │ Support       │  │   │  │ Normalizer    │  │
│  └───────────────┘  │   │  └───────────────┘  │   │  └───────────────┘  │
│  Port: 8001         │   │  Port: 8002         │   │  Port: 8003         │
└─────────┬───────────┘   └─────────┬───────────┘   └─────────┬───────────┘
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          MESSAGE QUEUE (Redis/RabbitMQ)                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │ crawl_queue  │ │  ocr_queue   │ │  nlp_queue   │ │ compliance_q │                │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────────┐
          ▼                         ▼                             ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│  COMPLIANCE ENGINE  │   │  RULE ENGINE        │   │  REPORTING SERVICE  │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │ Score Calc    │  │   │  │ Rule Loader   │  │   │  │ PDF Generator │  │
│  │ Risk Classifier│ │   │  │ Category Rules│  │   │  │ CSV Exporter  │  │
│  │ Violation Det │  │   │  │ Dynamic Valid │  │   │  │ Analytics     │  │
│  │ Penalty Calc  │  │   │  │ Rule CRUD     │  │   │  │ Dashboards    │  │
│  └───────────────┘  │   │  └───────────────┘  │   │  └───────────────┘  │
│  Port: 8004         │   │  Port: 8005         │   │  Port: 8006         │
└─────────┬───────────┘   └─────────┬───────────┘   └─────────┬───────────┘
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                   │
│  │     MongoDB      │  │      Redis       │  │   MinIO/S3       │                   │
│  │  • Products      │  │  • Cache         │  │  • Images        │                   │
│  │  • Audits        │  │  • Sessions      │  │  • Reports       │                   │
│  │  • Rules         │  │  • Rate Limits   │  │  • Raw HTML      │                   │
│  │  • Users         │  │  • Queue State   │  │  • OCR Results   │                   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Microservices Architecture

### Service Communication Pattern

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SYNCHRONOUS COMMUNICATION                         │
│                                                                      │
│   Client ──HTTP/REST──► API Gateway ──HTTP──► Microservice          │
│                              │                                       │
│                    Response ◄┘                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   ASYNCHRONOUS COMMUNICATION                         │
│                                                                      │
│   Service A ──publish──► Message Queue ──consume──► Service B       │
│       │                       │                          │          │
│       │                  (Redis/RabbitMQ)                │          │
│       │                       │                          │          │
│       └───────────callback────┴──────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

## Folder Structure

```
AI-Compliance/
├── docker-compose.yml              # Orchestration
├── docker-compose.prod.yml         # Production overrides
├── .env.example                    # Environment template
├── Makefile                        # Build automation
│
├── services/                       # Microservices
│   ├── api-gateway/               # Main API Gateway
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py            # FastAPI app
│   │   │   ├── config.py          # Settings
│   │   │   ├── middleware/
│   │   │   │   ├── auth.py
│   │   │   │   ├── rate_limit.py
│   │   │   │   └── logging.py
│   │   │   ├── routes/
│   │   │   │   ├── audit.py
│   │   │   │   ├── reports.py
│   │   │   │   ├── rules.py
│   │   │   │   └── health.py
│   │   │   └── models/
│   │   │       └── schemas.py
│   │   └── tests/
│   │
│   ├── crawler-service/           # Web Crawling
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── scrapy_crawler/
│   │   │   │   ├── spiders/
│   │   │   │   │   ├── amazon_spider.py
│   │   │   │   │   ├── flipkart_spider.py
│   │   │   │   │   └── generic_spider.py
│   │   │   │   ├── pipelines.py
│   │   │   │   ├── middlewares.py
│   │   │   │   └── settings.py
│   │   │   ├── async_fetcher.py
│   │   │   └── url_queue.py
│   │   └── tests/
│   │
│   ├── ocr-service/               # Image Processing & OCR
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── preprocessor.py    # OpenCV preprocessing
│   │   │   ├── ocr_engine.py      # Tesseract wrapper
│   │   │   ├── multi_lang.py      # Multi-language support
│   │   │   └── field_extractor.py
│   │   └── tests/
│   │
│   ├── nlp-service/               # NLP Processing
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── entity_extractor.py
│   │   │   ├── normalizer.py
│   │   │   ├── regex_patterns.py
│   │   │   └── field_mapper.py
│   │   └── tests/
│   │
│   ├── compliance-engine/         # Compliance Scoring
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── scorer.py
│   │   │   ├── risk_classifier.py
│   │   │   ├── violation_detector.py
│   │   │   └── penalty_calculator.py
│   │   └── tests/
│   │
│   ├── rule-engine/               # Dynamic Rules
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── rule_loader.py
│   │   │   ├── rule_validator.py
│   │   │   ├── category_rules.py
│   │   │   └── rule_crud.py
│   │   └── tests/
│   │
│   └── reporting-service/         # Reports & Analytics
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── pdf_generator.py
│       │   ├── csv_exporter.py
│       │   ├── analytics.py
│       │   └── dashboard_data.py
│       └── tests/
│
├── shared/                        # Shared Libraries
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py
│   │   ├── audit.py
│   │   ├── rule.py
│   │   └── violation.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── mongodb.py
│   │   └── redis_client.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── validators.py
│
├── frontend/                      # React Dashboard
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
│
├── streamlit-dashboard/           # Analytics Dashboard
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
│
├── infrastructure/                # DevOps
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── deployments/
│   │   ├── services/
│   │   ├── configmaps/
│   │   └── secrets/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── modules/
│   └── scripts/
│       ├── deploy.sh
│       └── backup.sh
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    ├── DEPLOYMENT.md
    └── diagrams/
```

## Database Schema (MongoDB)

### Collections

#### 1. `products`
```javascript
{
  "_id": ObjectId,
  "product_id": "uuid",
  "url": "https://...",
  "marketplace": "amazon|flipkart|other",
  "title": "Product Name",
  "category": "food|electronics|cosmetics|generic",
  "scraped_data": {
    "description": "...",
    "specifications": {},
    "images": ["url1", "url2"],
    "raw_html": "..."
  },
  "extracted_fields": {
    "mrp": "₹999",
    "selling_price": "₹799",
    "manufacturer": "...",
    "country_of_origin": "India",
    "net_quantity": "500g",
    // Category-specific fields
  },
  "ocr_data": {
    "raw_text": "...",
    "confidence": 0.95,
    "language": "en",
    "processed_images": ["s3://..."]
  },
  "created_at": ISODate,
  "updated_at": ISODate,
  "crawl_status": "pending|completed|failed"
}
```

#### 2. `audits`
```javascript
{
  "_id": ObjectId,
  "audit_id": "uuid",
  "product_id": "ref:products",
  "seller_id": "seller-001",
  "compliance_score": 75,
  "risk_level": "LOW|MEDIUM|HIGH",
  "violations": [
    {
      "code": "MISSING_MRP",
      "field": "mrp",
      "severity": "high",
      "message": "MRP declaration missing",
      "penalty": 25000,
      "legal_reference": "Section 18(1)"
    }
  ],
  "missing_fields": {
    "mandatory": ["fssai_license"],
    "optional": ["batch_number"]
  },
  "score_breakdown": {
    "mandatory_fields": 60,
    "optional_fields": 80,
    "format_compliance": 90,
    "weighted_total": 75
  },
  "created_at": ISODate,
  "audited_by": "system|user_id"
}
```

#### 3. `rules`
```javascript
{
  "_id": ObjectId,
  "rule_id": "uuid",
  "category": "food|electronics|cosmetics|generic",
  "name": "FSSAI License Required",
  "description": "...",
  "field": "fssai_license",
  "type": "mandatory|optional|conditional",
  "validation": {
    "regex": "^[0-9]{14}$",
    "min_length": 14,
    "max_length": 14,
    "format": "numeric"
  },
  "penalty": {
    "amount": 25000,
    "currency": "INR"
  },
  "legal_reference": "FSSAI Act 2006, Section 31",
  "weight": 10,
  "active": true,
  "conditions": [
    {"field": "category", "operator": "eq", "value": "food"}
  ],
  "created_at": ISODate,
  "updated_at": ISODate,
  "version": 1
}
```

#### 4. `crawl_queue`
```javascript
{
  "_id": ObjectId,
  "url": "https://...",
  "priority": 1,
  "status": "pending|processing|completed|failed",
  "retry_count": 0,
  "max_retries": 3,
  "seller_id": "...",
  "category": "...",
  "scheduled_at": ISODate,
  "processed_at": ISODate,
  "error": "..."
}
```

## API Endpoints

### API Gateway (Port 8000)

#### Audit Endpoints
```
POST   /api/v1/audit/url              # Audit single URL
POST   /api/v1/audit/bulk             # Bulk URL audit
POST   /api/v1/audit/image            # Audit product image
GET    /api/v1/audit/{audit_id}       # Get audit result
GET    /api/v1/audits                 # List audits (paginated)
DELETE /api/v1/audit/{audit_id}       # Delete audit
```

#### Product Endpoints
```
GET    /api/v1/products               # List products
GET    /api/v1/products/{id}          # Get product
POST   /api/v1/products/search        # Search products
```

#### Rule Engine Endpoints
```
GET    /api/v1/rules                  # List all rules
GET    /api/v1/rules/{category}       # Get category rules
POST   /api/v1/rules                  # Create rule
PUT    /api/v1/rules/{rule_id}        # Update rule
DELETE /api/v1/rules/{rule_id}        # Delete rule
POST   /api/v1/rules/validate         # Validate rule config
```

#### Report Endpoints
```
GET    /api/v1/reports/summary        # Dashboard summary
GET    /api/v1/reports/analytics      # Analytics data
GET    /api/v1/reports/export/csv     # Export CSV
GET    /api/v1/reports/export/pdf     # Export PDF
GET    /api/v1/reports/violations     # Violation trends
```

#### Health & Admin
```
GET    /health                        # Health check
GET    /api/v1/admin/stats            # System statistics
GET    /api/v1/admin/queue            # Queue status
```

## Deployment Strategy

### Docker Compose (Development)
```yaml
version: '3.8'
services:
  api-gateway:
    build: ./services/api-gateway
    ports: ["8000:8000"]
    depends_on: [mongodb, redis]
    
  crawler-service:
    build: ./services/crawler-service
    ports: ["8001:8001"]
    
  ocr-service:
    build: ./services/ocr-service
    ports: ["8002:8002"]
    
  nlp-service:
    build: ./services/nlp-service
    ports: ["8003:8003"]
    
  compliance-engine:
    build: ./services/compliance-engine
    ports: ["8004:8004"]
    
  rule-engine:
    build: ./services/rule-engine
    ports: ["8005:8005"]
    
  reporting-service:
    build: ./services/reporting-service
    ports: ["8006:8006"]
    
  mongodb:
    image: mongo:7
    volumes: [mongo_data:/data/db]
    
  redis:
    image: redis:7-alpine
```

### Kubernetes (Production)
- Horizontal Pod Autoscaler for each service
- Ingress controller for routing
- ConfigMaps for configuration
- Secrets for credentials
- PersistentVolumeClaims for storage

### Cloud Deployment Options

#### AWS
- ECS/EKS for containers
- DocumentDB for MongoDB
- ElastiCache for Redis
- S3 for file storage
- CloudFront for CDN
- ALB for load balancing

#### Azure
- AKS for Kubernetes
- Cosmos DB for MongoDB
- Azure Cache for Redis
- Blob Storage for files
- Azure CDN
- Application Gateway

#### GCP
- GKE for Kubernetes
- Cloud MongoDB Atlas
- Memorystore for Redis
- Cloud Storage for files
- Cloud CDN
- Cloud Load Balancing

## Scalability Considerations

### Horizontal Scaling
```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ API Gateway   │   │ API Gateway   │   │ API Gateway   │
│   Pod 1       │   │   Pod 2       │   │   Pod 3       │
└───────────────┘   └───────────────┘   └───────────────┘
```

### Auto-scaling Triggers
- CPU utilization > 70%
- Memory utilization > 80%
- Request queue depth > 100
- Response latency > 2s

### Caching Strategy
1. **Response Caching**: Cache frequent API responses (5min TTL)
2. **Rule Caching**: Cache compliance rules (1hr TTL)
3. **OCR Results**: Cache processed images (24hr TTL)
4. **Product Data**: Cache scraped data (1hr TTL)

### Rate Limiting
- Per-user: 100 requests/minute
- Per-IP: 200 requests/minute
- Bulk operations: 10 requests/minute
