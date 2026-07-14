# Document Intelligence API

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/DavidEscotoDev/doc-intel-api)
[![CI](https://github.com/DavidEscotoDev/doc-intel-api/actions/workflows/ci.yml/badge.svg)](https://github.com/DavidEscotoDev/doc-intel-api/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/DavidEscotoDev/coverage-badge/raw/main/doc-intel-api.json)](https://github.com/DavidEscotoDev/doc-intel-api/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**TL;DR** — Production-ready FastAPI service that extracts text from PDFs, images, and Office docs, then uses Claude 3.5 Sonnet to return structured analysis (summary, key points, entities, sentiment, topics). Built for real-world use: async processing, API keys with rate limits, structured logging, Prometheus metrics, Docker deployment.

![Demo](docs/demo.gif)  <!-- TODO: Record demo GIF showing upload → analyze → results flow -->

## Live Demo

**API Docs**: [https://doc-intel-api.onrender.com/docs](https://doc-intel-api.onrender.com/docs)  (Render free tier, cold start ~30s)

## Tech Stack

| Category | Technology |
|----------|------------|
| API Framework | FastAPI 0.109 |
| Database | SQLAlchemy 2.0 (async) + PostgreSQL |
| Auth | API Keys + bcrypt |
| AI/ML | Anthropic SDK (Claude 3.5 Sonnet) |
| Extraction | PyMuPDF, python-docx, Tesseract OCR |
| Observability | structlog (JSON), Prometheus metrics |
| Container | Docker multi-stage, non-root |

## Quick Start (≤5 commands)

```bash
git clone https://github.com/DavidEscotoDev/doc-intel-api.git
cd doc-intel-api
cp .env.example .env  # Add ANTHROPIC_API_KEY
docker-compose up --build
# Open http://localhost:8000/docs
```

## What I Learned

- **Production safety patterns**: bcrypt-hashed API keys, per-key rate limiting, file validation (MIME + magic bytes), path traversal prevention, non-root Docker user, graceful shutdown
- **Observability-first design**: Structured JSON logging with correlation IDs, Prometheus metrics (latency, throughput, errors, token usage), health endpoints for liveness/readiness probes

---

## Architecture

```mermaid
graph TD
    Client[Client] -->|"Upload"| UploadAPI["POST /api/v1/documents/upload"]
    Client -->|"Analyze"| ProcessAPI["POST /api/v1/process/analyze"]
    Client -->|"Status"| StatusAPI["GET /api/v1/process/status/{id}"]
    Client -->|"Query"| QueryAPI["GET /api/v1/query/documents/{id}"]

    UploadAPI --> Storage[(Local Storage)]
    UploadAPI --> Database[(PostgreSQL)]

    ProcessAPI --> Queue[Background Task]
    Queue --> Extractor[Text Extractor]
    Extractor -->|"PyMuPDF / python-docx / Tesseract"| Storage
    Extractor --> LLM[Claude 3.5 Sonnet]
    LLM --> Database

    StatusAPI --> Database
    QueryAPI --> Database
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload document (multipart/form-data) |
| `POST` | `/api/v1/process/analyze` | Queue document for analysis |
| `GET` | `/api/v1/process/status/{id}` | Get processing status |
| `GET` | `/api/v1/query/documents` | List documents (paginated) |
| `GET` | `/api/v1/query/documents/{id}` | Get full analysis results |
| `GET` | `/api/v1/query/stats` | Usage statistics |
| `POST` | `/api/v1/auth/keys` | Create new API key |
| `GET` | `/health` | Health check (DB + service) |
| `GET` | `/metrics` | Prometheus metrics |

## Example Usage

### Create API Key
```bash
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Authorization: Bearer di_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "rate_limit": 60}'
```

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer di_abc123..." \
  -F "file=@report.pdf"
```

### Trigger Analysis
```bash
curl -X POST http://localhost:8000/api/v1/process/analyze \
  -H "Authorization: Bearer di_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"document_id": "uuid-from-upload"}'
```

### Get Results
```bash
curl -X GET http://localhost:8000/api/v1/query/documents/{id} \
  -H "Authorization: Bearer di_abc123..."
```

Response:
```json
{
  "id": "uuid",
  "document_id": "uuid",
  "summary": "Executive summary...",
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "entities": ["Acme Corp", "John Doe", "Q3 2024"],
  "sentiment": "positive",
  "topics": ["financial-report", "quarterly-results"],
  "tokens_used": 1234,
  "model_version": "claude-3-5-sonnet-20241022",
  "processing_time_ms": 2450,
  "created_at": "2024-01-15T10:35:00Z"
}
```

## Configuration

All settings via environment variables (`.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/production) | `development` |
| `DATABASE_URL` | PostgreSQL connection string | `sqlite+aiosqlite:///:memory:` |
| `ANTHROPIC_API_KEY` | Anthropic API key | **Required** |
| `ANTHROPIC_MODEL` | Model to use | `claude-3-5-sonnet-20241022` |
| `API_KEY_PREFIX` | Prefix for generated keys | `di_` |
| `RATE_LIMIT_REQUESTS` | Requests per window | `10` |
| `RATE_LIMIT_WINDOW` | Window in seconds | `60` |
| `MAX_FILE_SIZE_MB` | Max upload size | `50` |
| `LOCAL_STORAGE_PATH` | Upload directory | `/app/data/uploads` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Project Structure

```
app/
├── main.py                 # FastAPI factory, lifespan, middleware
├── config.py               # Pydantic Settings (env-driven)
├── database.py             # Async SQLAlchemy engine/session
├── exceptions.py           # AppException hierarchy
├── logging.py              # structlog configuration
├── constants.py            # Module-level constants
├── middleware/
│   ├── auth.py             # API key verification
│   ├── rate_limit.py       # In-memory rate limiter
│   └── logging.py          # Request/response logging
├── models/
│   ├── document.py         # Document + analysis (JSON cols)
│   └── api_key.py          # API key with bcrypt hash
├── routes/
│   ├── upload.py           # POST /documents/upload
│   ├── process.py          # POST /process/analyze, GET /status
│   ├── query.py            # GET /documents, /documents/{id}, /stats
│   ├── auth.py             # POST /auth/keys
│   └── health.py           # GET /health, /metrics
├── services/
│   ├── storage.py          # Local file storage
│   ├── extractor.py        # Text extraction (PDF/DOCX/IMG)
│   └── llm.py              # Anthropic client + JSON parsing
├── tasks/
│   └── processor.py        # Background analysis pipeline
├── schemas/                # Pydantic request/response models
└── security/
    └── validation.py       # Filename + content validation
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing
```

## Deployment

### Render (Free Tier) — Recommended
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/DavidEscotoDev/doc-intel-api)

1. Click button above or connect repo manually
2. Select Blueprint (`render.yaml`)
3. Add `ANTHROPIC_API_KEY` in Environment tab
4. Deploy — live at `https://doc-intel-api.onrender.com`

### Docker
```bash
docker build -t doc-intel-api .
docker run -p 8000:8000 --env-file .env doc-intel-api
```

### Kubernetes
Helm chart available in `deploy/helm/`

## Security

- API keys bcrypt-hashed (never stored in plaintext)
- Per-key rate limiting (configurable)
- File validation: MIME type, magic bytes, size limits
- Filename sanitization (path traversal prevention)
- Non-root Docker user
- Security headers via middleware
- CORS configurable per environment

## Monitoring

- **Health**: `GET /health` (liveness + readiness)
- **Metrics**: `GET /metrics` (Prometheus format)
- **Logs**: Structured JSON with correlation IDs
- **Tracing**: Correlation ID propagated through middleware

## License

MIT License — see [LICENSE](LICENSE)

## Author

**David Escoto** — 16-year-old backend developer building production systems and AI infrastructure. Seeking internships to learn software engineering best practices on real teams.

[GitHub](https://github.com/DavidEscotoDev) • [LinkedIn](https://www.linkedin.com/in/david-escoto-estrada-1ab5633b9/) • Email: davidescoto.dev@gmail.com