# AI Legal Metrology Compliance Intelligence Cloud

Microservices-style, AI-driven compliance platform for e-commerce product listings with OCR + NLP + rules + RAG + LLM.

## 1) Project Folder Structure

```text
AI Compilance/
├── backend/
│   ├── __init__.py
│   ├── .env.example
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── requirements.txt
│   ├── legal_rules/
│   │   ├── rules.json
│   │   └── legal_corpus.txt
│   └── services/
│       ├── __init__.py
│       ├── ingestion_service.py
│       ├── ocr_service.py
│       ├── nlp_service.py
│       ├── rule_engine.py
│       ├── rag_service.py
│       ├── llm_service.py
│       ├── compliance_engine.py
│       ├── reporting_service.py
│       └── llm_prompt_template.txt
├── frontend/
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── vercel.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js
│       ├── styles.css
│       ├── components/
│       │   ├── ProductForm.jsx
│       │   ├── ComplianceResultCard.jsx
│       │   └── AdminMetrics.jsx
│       └── pages/
│           ├── SellerDashboard.jsx
│           └── AdminDashboard.jsx
├── render.yaml
├── .gitignore
└── README.md
```

## 2) Backend Service Responsibilities

- `ingestion_service.py`: merges form + OCR + packaging text, parses batch CSV.
- `ocr_service.py`: Tesseract OCR (`eng+hin`) + text cleanup.
- `nlp_service.py`: extracts MRP, quantity, manufacturer, country + normalizes units.
- `rule_engine.py`: loads `rules.json`, deducts penalties, returns violations.
- `rag_service.py`: chunks legal corpus, builds FAISS index, retrieves top 3 clauses.
- `llm_service.py`: generates explanation/corrections/risk summary from context.
- `compliance_engine.py`: orchestrates all services and computes risk class.
- `reporting_service.py`: stores reports in MongoDB (fallback in-memory), CSV export.

### New URL Audit Pipeline Modules (Web Scrape + OCR)

- `scraper_service.py`: BeautifulSoup-based scraper for product title, description, specification table, and image URLs.
- `image_ocr_extraction_service.py`: downloads scraped product images and extracts text via OCR.
- `field_identification_service.py`: regex + NLP-style field extraction for mandatory declarations.
- `validation_service.py`: configurable legal metrology validation engine using `backend/legal_rules/audit_rules.json`.
- `url_audit_service.py`: orchestration module to run scrape → OCR → field identification → rule validation.

## 3) API Endpoints

- `POST /scan-product` (multipart form: seller_id, product_name, description, packaging_text, image)
- `POST /batch-scan` (CSV upload)
- `GET /reports?risk_level=Compliant|Moderate Risk|High Risk`
- `GET /reports/export` (CSV download)
- `GET /product/{id}`
- `GET /health`

### URL Audit + Dashboard Endpoints

- `POST /audit/url` (JSON body: `url`, `seller_id`)
- `GET /audit/reports?risk_level=Compliant|Moderate Risk|High Risk`
- `GET /audit/reports/{product_id}`
- `GET /audit/stats`
- `GET /audit/export/csv`
- `GET /audit/export/pdf`

## 4) Example Rules + Corpus

- Rules file: `backend/legal_rules/rules.json`
- Corpus file: `backend/legal_rules/legal_corpus.txt`

Both are already included and can be expanded safely for production.

## 5) Local Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 20+
- MongoDB (optional, fallback available)
- Tesseract OCR installed (Windows path example in `.env.example`)

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
cd ..
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open frontend at `http://localhost:5173`.

## 6) Batch CSV Input Format

Use headers:

```csv
seller_id,product_name,description,packaging_text
seller-001,Turmeric Powder,"Spice powder","MRP Rs 120 Net Wt 500g Manufacturer: ABC Foods Made in India"
```

## 7) Deployment Instructions (Render + Vercel)

### Render (Backend)

1. Push repository to GitHub.
2. In Render, create Blueprint deployment using `render.yaml`.
3. Set environment variables:
   - `GROQ_API_KEY`
   - `GROQ_MODEL` (optional, default: `llama-3.1-8b-instant`)
   - `MONGODB_URL`
   - `MONGODB_DB`
   - `TESSERACT_CMD` (optional if runtime includes default path)
4. Deploy service.

### Vercel (Frontend)

1. Import `frontend` as Vercel project.
2. Framework preset: `Vite`.
3. Set env var `VITE_API_BASE_URL` to Render backend URL.
4. Deploy.

## 8) Sample LLM Prompt Template

See `backend/services/llm_prompt_template.txt`.

## 9) Hackathon-to-Production Upgrade Path

- Replace in-memory fallback with strict MongoDB dependency + indexes.
- Add async task queue (Celery/RQ) for heavy OCR and batch jobs.
- Add auth (JWT + RBAC for seller/admin).
- Add observability (OpenTelemetry + Prometheus + Grafana).
- Version rule packs and legal corpus with admin management UI.
- Add automated regression tests and clause-grounded explanation validation.
