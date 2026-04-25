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

## Getting Started

### Prerequisites (All Modes)

- Python 3.8+ (for backend development)
- Node.js 16+ (for frontend)
- Git
- Optional: Docker & Docker Compose (for containerized setup)

---

## Backend Setup (Uvicorn Development Mode)

Run the backend standalone for development without Docker services.

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd AI-Compilance
```

### Step 2: Create Python Virtual Environment

```bash
# Windows
python -m venv .venv-2
.\.venv-2\Scripts\activate

# macOS/Linux
python3 -m venv .venv-2
source .venv-2/bin/activate
```

### Step 3: Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 4: Set Environment Variables

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "your-openai-api-key"
$env:MONGODB_URL = "mongodb://localhost:27017"

# macOS/Linux
export OPENAI_API_KEY="your-openai-api-key"
export MONGODB_URL="mongodb://localhost:27017"
```

### Step 5: Run the Backend Server

```bash
# Run from project root (not from backend/ directory)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**Backend will be available at:** http://127.0.0.1:8000

**Swagger API Docs:** http://127.0.0.1:8000/docs

### Notes

- The `--reload` flag enables auto-reload on file changes
- If you need database support, MongoDB must be running (see Docker section below)
- For full audit functionality, ensure MongoDB and Redis are accessible

---

## Frontend Setup (React Development Mode)

Run the frontend React development server.

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Install Frontend Dependencies

```bash
npm install
```

### Step 3: Configure Backend URL (Optional)

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

(If not set, defaults to `http://localhost:8000`)

### Step 4: Run the Dev Server

```bash
npm run dev
```

**Frontend will be available at:** http://localhost:5173

### Build for Production

```bash
npm run build
```

The optimized build will be in `frontend/dist/`

---

## Docker Setup (Complete Stack)

Run the entire application stack with Docker containers.

### Step 1: Clone and Configure

```bash
git clone <repository-url>
cd AI-Compilance
cp .env.example .env
# Edit .env with your settings (optional)
```

### Step 2: Start All Services

```bash
# Build and start all containers
docker-compose up -d

# View logs in real-time
docker-compose logs -f

# Check service health
curl http://localhost/health
```

### Step 3: Access Services

| Service             | URL                        |
| ------------------- | -------------------------- |
| **Frontend**        | http://localhost:5173      |
| **Backend API**     | http://localhost:8000      |
| **API Docs**        | http://localhost:8000/docs |
| API Gateway (nginx) | http://localhost           |
| Crawler Service     | http://localhost:8001      |
| OCR Service         | http://localhost:8002      |
| NLP Service         | http://localhost:8003      |
| Compliance Engine   | http://localhost:8004      |
| Rule Engine         | http://localhost:8005      |
| Reporting Service   | http://localhost:8006      |
| MongoDB             | localhost:27017            |
| Redis               | localhost:6379             |
| Prometheus          | http://localhost:9090      |
| Grafana             | http://localhost:3001      |

### Stop All Services

```bash
docker-compose down

# Remove volumes (clean database)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f mongodb
```

### Run Individual Service with Docker

````bash
# Start only specific services
docker-compose up -d mongodb redis
docker-compose up -d backend

# Restart a service
docker-compose restart backend

## Configuration Reference

### Environment Variables

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=compliance_db

# Redis
REDIS_URL=redis://localhost:6379

# OpenAI
OPENAI_API_KEY=your-api-key-here

# Service URLs (for inter-service communication in Docker)
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
````

Copy `.env.example` to `.env` and update values as needed.

## Development Guide

### Running Microservices Individually (Docker)

```bash
# Start a specific microservice
cd services/ocr-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

### Testing

```bash
# Run all tests
pytest

# Run specific service tests
pytest services/ocr-service/tests/

# Run with coverage
pytest --cov=backend tests/
```

### API Examples

#### Add New Rule

```bash
curl -X POST http://localhost:8000/audit/rules \
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

#### Crawl a Product URL

```bash
curl -X POST http://localhost:8000/audit/url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/product/123",
    "seller_id": "seller-001",
    "category": "food"
  }'
```

#### Process Image with OCR

```bash
curl -X POST http://localhost:8000/audit/ocr \
  -F "image=@product_label.jpg" \
  -F "seller_id=seller-001"
```

#### Get Audit Statistics

```bash
curl http://localhost:8000/audit/stats
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

## Architecture Notes

### Legacy Backend

The original monolithic backend is preserved in the `backend/` directory for reference and gradual migration. It provides:

- Form-based product scanning
- URL audit pipeline
- Category-based auditing
- Basic reporting

This is being gradually refactored into microservices. For development, run it with:

```bash
# From project root
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

See the [Backend Setup](#backend-setup-uvicorn-development-mode) section above for full instructions.

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
