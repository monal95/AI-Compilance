# AI Legal Metrology Compliance Intelligence Cloud

Enterprise-grade, microservices-based compliance platform for e-commerce product listings with automated web crawling, multi-language OCR, NLP-based field identification, configurable rule engine, and real-time reporting.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API Gateway (nginx)                              │
│                                  Port 80                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
       ┌──────────────┬───────────────┼───────────────┬──────────────┐
       │              │               │               │              │
       ▼              ▼               ▼               ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Crawler   │ │    OCR      │ │    NLP      │ │    Rule     │ │  Reporting  │
│   Service   │ │  Service    │ │  Service    │ │   Engine    │ │   Service   │
│   :8001     │ │   :8002     │ │   :8003     │ │   :8005     │ │   :8006     │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
       │              │               │               │              │
       └──────────────┴───────────────┼───────────────┴──────────────┘
                                      │
                            ┌─────────────────┐
                            │   Compliance    │
                            │    Engine       │
                            │    :8004        │
                            └─────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
            ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
            │   MongoDB   │   │    Redis    │   │ Prometheus  │
            │   :27017    │   │    :6379    │   │   :9090     │
            └─────────────┘   └─────────────┘   └─────────────┘
```

## Project Structure

```
AI-Compliance/
├── services/
│   ├── crawler-service/      # Web scraping with rate limiting
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   └── async_fetcher.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── ocr-service/          # Multi-language OCR with OpenCV
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── preprocessor.py
│   │   │   ├── ocr_engine.py
│   │   │   └── field_extractor.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── nlp-service/          # Entity extraction & pattern matching
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── entity_extractor.py
│   │   │   ├── text_normalizer.py
│   │   │   └── pattern_matcher.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── rule-engine/          # MongoDB-based rule management
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── rule_executor.py
│   │   │   └── rule_validator.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── compliance-engine/    # Orchestration service
│   │   ├── app/
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── reporting-service/    # Dashboard & report generation
│       ├── app/
│       │   └── main.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── shared/                   # Shared libraries
│   ├── models/
│   │   └── __init__.py       # Pydantic models
│   ├── database/
│   │   ├── mongodb.py        # MongoDB async client
│   │   └── redis_client.py   # Redis client
│   └── utils/
│       └── logger.py         # Centralized logging
│
├── docker/                   # Docker configurations
│   ├── nginx.conf            # API Gateway config
│   ├── mongo-init.js         # MongoDB initialization
│   └── prometheus.yml        # Monitoring config
│
├── docs/
│   └── ARCHITECTURE.md       # Detailed architecture docs
│
├── backend/                  # Legacy monolithic backend
├── frontend/                 # React frontend
├── docker-compose.yml        # Container orchestration
└── .env.example              # Environment template
```

## Microservices

### 1. Crawler Service (Port 8001)

Automated web crawling with rate limiting and retry logic.

**Endpoints:**

- `POST /crawl` - Crawl single URL
- `POST /crawl/bulk` - Crawl multiple URLs
- `GET /crawl/status/{job_id}` - Check crawl job status

**Features:**

- User agent rotation
- Rate limiting (configurable)
- Retry with exponential backoff
- Redis-based job queue

### 2. OCR Service (Port 8002)

Multi-language OCR with OpenCV preprocessing.

**Endpoints:**

- `POST /ocr/process` - Process single image
- `POST /ocr/batch` - Process multiple images
- `GET /ocr/languages` - List supported languages

**Supported Languages:**

- English (eng)
- Hindi (hin)
- Tamil (tam)
- Telugu (tel)
- Kannada (kan)
- Marathi (mar)
- Bengali (ben)
- Gujarati (guj)

**Preprocessing Pipeline:**

1. Grayscale conversion
2. Noise reduction (Gaussian blur)
3. Adaptive thresholding
4. Deskewing
5. Border removal

### 3. NLP Service (Port 8003)

Entity extraction and text normalization.

**Endpoints:**

- `POST /nlp/extract-entities` - Extract entities from text
- `POST /nlp/normalize` - Normalize text
- `POST /nlp/analyze` - Full NLP analysis

**Capabilities:**

- MRP extraction (multiple formats)
- Quantity/weight normalization
- Manufacturer identification
- Country of origin detection
- Date parsing (manufacturing/expiry)
- FSSAI license detection
- Pattern matching for compliance fields

### 4. Rule Engine (Port 8005)

MongoDB-based configurable compliance rules.

**Endpoints:**

- `GET /rules` - List all rules
- `POST /rules` - Create new rule
- `GET /rules/{rule_id}` - Get rule details
- `PUT /rules/{rule_id}` - Update rule
- `DELETE /rules/{rule_id}` - Delete rule
- `POST /rules/execute` - Execute rules against data
- `GET /rules/stats` - Rule statistics

**Supported Operators:**

- Comparison: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`
- String: `contains`, `not_contains`, `starts_with`, `ends_with`, `matches_regex`
- Existence: `exists`, `not_exists`, `is_empty`, `is_not_empty`
- Collection: `in`, `not_in`, `length_eq`, `length_gt`, `length_lt`
- Type: `is_type`, `is_numeric`, `is_date`
- Range: `between`, `not_between`

### 5. Compliance Engine (Port 8004)

Orchestrates all services for compliance audits.

**Endpoints:**

- `POST /compliance/audit/text` - Audit text data
- `POST /compliance/audit/image` - Audit image(s)
- `GET /compliance/audit/{audit_id}` - Get audit results
- `GET /compliance/health` - Health check

**Workflow:**

1. Receive audit request
2. If image: Call OCR service
3. Call NLP service for entity extraction
4. Call Rule Engine for compliance check
5. Calculate compliance score
6. Store results in MongoDB
7. Return audit report

### 6. Reporting Service (Port 8006)

Dashboard analytics and report generation.

**Endpoints:**

- `GET /reports/dashboard` - Dashboard statistics
- `POST /reports/generate` - Generate report (PDF/Excel/CSV)
- `GET /reports/trends` - Compliance trends
- `GET /reports/download/{report_id}` - Download report

**Report Formats:**

- PDF (with charts and tables)
- Excel (.xlsx with multiple sheets)
- CSV (raw data export)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM recommended

### 1. Clone and Configure

```bash
git clone <repository-url>
cd AI-Compliance
cp .env.example .env
# Edit .env with your settings
```

### 2. Start All Services

```bash
# Build and start all containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
curl http://localhost/health
```

### 3. Access Services

| Service     | URL                   |
| ----------- | --------------------- |
| API Gateway | http://localhost      |
| Crawler     | http://localhost:8001 |
| OCR         | http://localhost:8002 |
| NLP         | http://localhost:8003 |
| Compliance  | http://localhost:8004 |
| Rule Engine | http://localhost:8005 |
| Reporting   | http://localhost:8006 |
| MongoDB     | localhost:27017       |
| Redis       | localhost:6379        |
| Prometheus  | http://localhost:9090 |
| Grafana     | http://localhost:3001 |

## API Examples

### Crawl a Product URL

```bash
curl -X POST http://localhost/api/crawler/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/product/123"}'
```

### Process Image with OCR

```bash
curl -X POST http://localhost/api/ocr/process \
  -F "image=@product_label.jpg" \
  -F "languages=eng,hin"
```

### Run Compliance Audit

```bash
curl -X POST http://localhost/api/compliance/audit/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "MRP Rs 299 Net Weight 500g Made in India",
    "category": "food",
    "seller_id": "seller-001"
  }'
```

### Generate Report

```bash
curl -X POST http://localhost/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "format": "pdf",
    "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
    "filters": {"risk_level": "high"}
  }'
```

## Configuration

### Environment Variables

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=compliance_db

# Redis
REDIS_URL=redis://localhost:6379

# Service URLs (for inter-service communication)
CRAWLER_SERVICE_URL=http://crawler-service:8001
OCR_SERVICE_URL=http://ocr-service:8002
NLP_SERVICE_URL=http://nlp-service:8003
RULE_ENGINE_URL=http://rule-engine:8005

# OCR Settings
TESSERACT_CMD=/usr/bin/tesseract
DEFAULT_OCR_LANGUAGES=eng,hin

# Crawler Settings
CRAWLER_RATE_LIMIT=2
CRAWLER_MAX_RETRIES=3
CRAWLER_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
```

## Development

### Run Individual Service

```bash
cd services/ocr-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific service tests
pytest services/ocr-service/tests/
```

### Add New Rule

```bash
curl -X POST http://localhost/api/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MRP Required",
    "description": "Product must have MRP declared",
    "category": "food",
    "field": "mrp",
    "operator": "exists",
    "severity": "high",
    "penalty_points": 25
  }'
```

## Monitoring

### Prometheus Metrics

All services expose `/metrics` endpoint with:

- Request count and latency
- Error rates
- Service-specific metrics (OCR processing time, rule execution count, etc.)

### Grafana Dashboards

Pre-configured dashboards available at http://localhost:3001:

- Service Health Overview
- Compliance Audit Trends
- OCR Processing Statistics
- Rule Engine Analytics

## Legacy Backend

The original monolithic backend is preserved in `backend/` for reference and gradual migration. It provides:

- Form-based product scanning
- URL audit pipeline
- Basic reporting

Access via: `uvicorn backend.main:app --reload`

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>
```

### MongoDB Connection Issues

```bash
# Check MongoDB is running
docker-compose ps mongodb

# Connect to MongoDB shell
docker exec -it mongodb mongosh
```

### OCR Quality Issues

- Ensure image resolution is at least 300 DPI
- Check supported languages are installed
- Try different preprocessing options

## License

MIT License - See LICENSE file for details.
