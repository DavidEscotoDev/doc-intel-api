# Document Intelligence API

AI-powered document analysis API built with FastAPI. Upload PDFs, images, or Office documents → get structured summaries, key points, entities, sentiment, and topics via Claude.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure (optional - defaults work for local dev)
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Run
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/documents/upload` | Upload a document (PDF, DOCX, TXT, PNG, JPG, TIFF) |
| `POST /api/v1/process/analyze` | Queue document for AI analysis |
| `GET /api/v1/process/status/{id}` | Check processing status |
| `GET /api/v1/query/documents` | List your documents (paginated) |
| `GET /api/v1/query/documents/{id}` | Get full analysis results |
| `GET /api/v1/query/stats` | Usage statistics |
| `POST /api/v1/auth/keys` | Create new API key (requires existing key) |

### Example

```bash
# 1. Create API key (first one via env or admin)
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Authorization: Bearer di_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "rate_limit": 60}'

# 2. Upload document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer di_your_key" \
  -F "file=@report.pdf"

# 3. Trigger analysis
curl -X POST http://localhost:8000/api/v1/process/analyze \
  -H "Authorization: Bearer di_your_key" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "uuid-from-upload"}'

# 4. Get results
curl -X GET http://localhost:8000/api/v1/query/documents/{id} \
  -H "Authorization: Bearer di_your_key"
```

### Sample Response

```json
{
  "id": "uuid",
  "document_id": "uuid",
  "summary": "Executive summary of the document...",
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "entities": ["Acme Corp", "John Doe", "Q3 2024"],
  "sentiment": "positive",
  "topics": ["financial-report", "quarterly-results"],
  "tokens_used": 1234,
  "model_version": "claude-3-5-sonnet-20241022",
  "processing_time_ms": 2450,
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Upload    │────▶│  Extract    │────▶│   Analyze   │
│  (FastAPI)  │     │  (PyMuPDF,  │     │  (Claude    │
│             │     │  python-    │     │   Sonnet    │
│             │     │  docx,      │     │   3.5)      │
│             │     │  Tesseract) │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────┐
│              SQLite / PostgreSQL                    │
│  Documents + Analysis (JSON columns)                │
└─────────────────────────────────────────────────────┘
```

**Key decisions:**
- **Async throughout** — FastAPI + SQLAlchemy 2.0 + asyncpg/aiosqlite
- **Background processing** — `BackgroundTasks` for non-blocking analysis
- **API key auth** — bcrypt-hashed keys, per-key rate limits, expiration support
- **File validation** — MIME type + magic bytes + size limits (50MB)
- **Structured logging** — structlog with JSON output in production
- **Prometheus metrics** — `/metrics` endpoint for monitoring

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI 0.109 |
| Database | SQLAlchemy 2.0 (async) + SQLite/PostgreSQL |
| Auth | API keys + bcrypt |
| AI | Anthropic SDK (Claude 3.5 Sonnet) |
| Extraction | PyMuPDF, python-docx, Tesseract |
| Observability | structlog + prometheus-client |
| Deployment | Docker + docker-compose |

## Project Structure

```
app/
├── main.py              # App factory + lifespan
├── config.py            # Pydantic Settings (flat, env-driven)
├── database.py          # Async engine + session management
├── exceptions.py        # 3 core exceptions
├── constants.py         # Module-level constants (no enums)
├── logging.py           # structlog configuration
├── middleware/
│   ├── auth.py          # API key verification
│   ├── rate_limit.py    # In-memory rate limiter
│   └── logging.py       # Request/response logging
├── models/
│   ├── document.py      # Document + analysis (JSON cols)
│   └── api_key.py       # API key model
├── routes/
│   ├── upload.py        # POST /documents/upload
│   ├── process.py       # POST /process/analyze, GET /status
│   ├── query.py         # GET /documents, /documents/{id}, /stats
│   ├── auth.py          # POST /auth/keys
│   └── health.py        # /health, /metrics
├── services/
│   ├── storage.py       # Local file storage
│   ├── extractor.py     # Text extraction (PDF/DOCX/IMG)
│   └── llm.py           # Claude analysis + JSON parsing
├── tasks/
│   └── processor.py     # Background analysis task
├── schemas/             # Pydantic request/response models
└── security/
    └── validation.py    # Filename + file content validation
```

## Configuration

All via environment variables (`.env`):

```env
APP_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./data.db
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
API_KEY_PREFIX=di_
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
MAX_FILE_SIZE_MB=50
LOCAL_STORAGE_PATH=./data/uploads
```

## Testing

```bash
pytest tests/ -v
# 18 tests passing (security validation, logging, auth, health)
```

## Deployment

```bash
# Build
docker build -t doc-intel-api .

# Run (with PostgreSQL)
docker-compose up -d
```

## License

MIT