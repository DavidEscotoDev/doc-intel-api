# Document Intelligence API

> **Production-grade async FastAPI service for AI-powered document analysis with Azure-native integrations.**

[![CI](https://github.com/yourusername/docintel-api/workflows/CI/badge.svg)](https://github.com/yourusername/docintel-api/actions)
[![Coverage](https://codecov.io/gh/yourusername/docintel-api/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/docintel-api)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

The Document Intelligence API is a production-ready, async-first service that extracts text from documents (PDF, DOCX, TXT, images) and analyzes them using Anthropic's Claude 3.5 Sonnet. Built with FastAPI, SQLAlchemy 2.0, and PostgreSQL, it demonstrates senior-level engineering practices suitable for Microsoft/Azure cloud environments.

### Key Features

- **Async-first architecture**: FastAPI + SQLAlchemy 2.0 async + asyncpg for high concurrency
- **Azure-native**: Blob Storage, Key Vault, Monitor/OpenTelemetry, Container Apps ready
- **Comprehensive observability**: Structured JSON logging, distributed tracing, Prometheus metrics, health probes
- **Security-first**: bcrypt-hashed API keys, rate limiting, input validation, magic byte checking, security headers
- **Background processing**: Document analysis via FastAPI BackgroundTasks (migrates to Azure Service Bus)
- **85%+ test coverage**: Unit + integration tests with pytest, httpx, pytest-asyncio

## Architecture

```mermaid
graph TB
    Client -->|HTTPS| API[FastAPI API]
    API -->|Async| DB[(PostgreSQL)]
    API -->|Store| Blob[Azure Blob Storage]
    API -->|Secrets| KV[Azure Key Vault]
    API -->|Trace| OTel[OpenTelemetry]
    OTel -->|Metrics| Prom[Prometheus]
    OTel -->|Traces| AM[Azure Monitor]
    API -->|Background| Tasks[BackgroundTasks]
    Tasks -->|Extract| Extract[TextExtractor]
    Tasks -->|Analyze| LLM[Claude 3.5 Sonnet]
    Tasks -->|Save| DB
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| API Framework | FastAPI 0.109 |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 async + asyncpg |
| Migrations | Alembic |
| AI/ML | Anthropic Claude 3.5 Sonnet |
| Storage | Azure Blob Storage / Local filesystem |
| Secrets | Azure Key Vault |
| Observability | OpenTelemetry, Prometheus, Azure Monitor, structlog |
| Auth | API Keys (bcrypt) + Rate Limiting (in-memory/Redis) |
| Containerization | Docker multi-stage, non-root |
| CI/CD | GitHub Actions (ruff, mypy, pytest, Docker) |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16 (or use Docker Compose)
- Anthropic API key

### Local Development

```bash
# Clone and enter
git clone https://github.com/yourusername/docintel-api.git
cd docintel-api

# Copy environment template
cp .env.example .env
# Edit .env with your Anthropic API key

# Start services
docker compose up -d

# Run database migrations
docker compose exec app alembic upgrade head

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
# Metrics at http://localhost:8000/metrics
```

### Manual Setup (without Docker)

```bash
# Install dependencies
pip install -e .[dev]

# Set environment variables
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/docintel
export ANTHROPIC_API_KEY=sk-ant-...
export APP_ENV=development

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

All settings via environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `ANTHROPIC_MODEL` | Model to use | `claude-3-5-sonnet-20241022` |
| `STORAGE_PROVIDER` | `local` or `azure_blob` | `local` |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob connection | Required if `azure_blob` |
| `AZURE_KEY_VAULT_URL` | Key Vault URL | Optional |
| `AZURE_MONITOR_CONNECTION_STRING` | App Insights connection | Optional |
| `API_KEY_PREFIX` | API key prefix | `di_` |
| `RATE_LIMIT_REQUESTS` | Requests per window | `10` |
| `RATE_LIMIT_WINDOW` | Window in seconds | `60` |
| `MAX_FILE_SIZE_MB` | Max upload size | `50` |

## API Reference

Base URL: `/api/v1`

### Authentication

All endpoints require `Authorization: Bearer <api_key>` header.

```bash
curl -H "Authorization: Bearer di_xxx" https://api.example.com/api/v1/health
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (DB, version, env) |
| `GET` | `/health/live` | Kubernetes liveness probe |
| `GET` | `/health/ready` | Kubernetes readiness probe |
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/documents/upload` | Upload document (multipart) |
| `GET` | `/documents/list` | List documents (paginated) |
| `POST` | `/process/analyze` | Queue document for analysis |
| `GET` | `/process/status/{id}` | Get processing status |
| `GET` | `/query/documents` | List documents with analysis |
| `GET` | `/query/documents/{id}` | Get full analysis results |
| `GET` | `/query/stats` | Usage statistics |
| `POST` | `/auth/keys` | Create new API key |
| `GET` | `/auth/keys` | List all API keys |
| `GET` | `/auth/keys/{id}` | Get API key details |
| `DELETE` | `/auth/keys/{id}` | Revoke API key |

### Example: Upload & Analyze

```bash
# 1. Upload document
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer di_your_key" \
  -F "file=@document.pdf"

# Response: {"id": "uuid", "filename": "document.pdf", "status": "uploaded", ...}

# 2. Queue for analysis
curl -X POST "http://localhost:8000/api/v1/process/analyze" \
  -H "Authorization: Bearer di_your_key" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "uuid-from-step-1"}'

# Response: {"id": "uuid", "status": "processing", "progress": 0}

# 3. Check status
curl "http://localhost:8000/api/v1/process/status/uuid" \
  -H "Authorization: Bearer di_your_key"

# 4. Get results when completed
curl "http://localhost:8000/api/v1/query/documents/uuid" \
  -H "Authorization: Bearer di_your_key"
```

### Example Response

```json
{
  "id": "analysis-uuid",
  "document_id": "doc-uuid",
  "summary": "This document describes...",
  "key_points": ["Point 1", "Point 2"],
  "entities": ["Entity 1", "Entity 2"],
  "sentiment": "positive",
  "topics": ["Topic 1"],
  "tokens_used": 1250,
  "model_version": "claude-3-5-sonnet-20241022",
  "processing_time_ms": 3420,
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Deployment

### Render.com (via `render.yaml`)

```bash
# Connect repo to Render, it will auto-deploy from render.yaml
# Set ANTHROPIC_API_KEY, AZURE_STORAGE_CONNECTION_STRING as secret env vars
```

### Azure Container Apps (via Bicep)

```bash
# Deploy infrastructure
az deployment sub create \
  --location eastus \
  --template-file infra/bicep/main.bicep \
  --parameters environmentName=prod

# Build and push image
az acr build --registry myregistry --image docintel-api:v1 .

# Deploy to Container Apps
az containerapp update --name docintel-api --resource-group my-rg --image myregistry.azurecr.io/docintel-api:v1
```

### Kubernetes (Helm)

```bash
# Add chart repo and install
helm repo add docintel https://charts.example.com
helm install docintel docintel/docintel-api \
  --set image.repository=myregistry/docintel-api \
  --set image.tag=v1.0.0 \
  --set env.ANTHROPIC_API_KEY=sk-ant-...
```

## Observability

### Metrics (Prometheus)

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request latency |
| `documents_uploaded_total` | Counter | Documents uploaded by status |
| `documents_processed_total` | Counter | Documents processed by status |
| `document_processing_duration_seconds` | Histogram | Processing duration |
| `llm_tokens_used_total` | Counter | LLM tokens consumed |
| `llm_request_duration_seconds` | Histogram | LLM request latency |

### Dashboards

- **Grafana**: Import `docs/grafana-dashboard.json`
- **Azure Monitor**: Built-in Application Insights views

### Health Checks

```bash
# Liveness (process alive)
curl http://localhost:8000/health/live

# Readiness (DB reachable)
curl http://localhost:8000/health/ready

# Full health
curl http://localhost:8000/health
```

## Testing

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term-missing --cov-fail-under=85

# Run specific test module
pytest tests/test_routes_upload.py -v

# Run with PostgreSQL (integration)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/docintel pytest

# Lint & typecheck
ruff check app/
mypy app/
```

## Architecture Decision Records

See [`docs/adr/`](docs/adr/) for detailed ADRs:

- [ADR 001](docs/adr/001-async-architecture.md): Async-first architecture
- [ADR 002](docs/adr/002-azure-integrations.md): Azure-native integrations
- [ADR 003](docs/adr/003-api-key-auth.md): API key authentication with bcrypt
- [ADR 004](docs/adr/004-background-processing.md): Background processing strategy
- [ADR 005](docs/adr/005-observability.md): Observability stack
- [ADR 006](docs/adr/006-pydantic-v2.md): Pydantic v2 for validation

## Project Structure

```
├── .github/workflows/ci.yml      # CI/CD pipeline
├── .pre-commit-config.yaml       # Pre-commit hooks
├── docs/
│   ├── adr/                      # Architecture Decision Records
│   ├── architecture.md           # Architecture diagram
│   └── grafana-dashboard.json    # Grafana dashboard
├── infra/bicep/                  # Azure Bicep IaC
├── app/
│   ├── main.py                   # FastAPI factory + lifespan
│   ├── config.py                 # Pydantic Settings config
│   ├── constants.py              # Application constants
│   ├── exceptions.py             # Exception hierarchy
│   ├── logging.py                # Structured logging (structlog)
│   ├── telemetry.py              # OpenTelemetry + Prometheus
│   ├── database.py               # SQLAlchemy 2.0 async setup
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic v2 schemas
│   ├── routes/                   # API route handlers
│   ├── services/                 # Business logic (storage, extractor, LLM)
│   ├── tasks/                    # Background processing
│   ├── middleware/               # Auth, rate limit, logging
│   └── security/                 # Validation, headers
├── tests/                        # Unit + integration tests
├── alembic/                      # Database migrations
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Local development stack
├── render.yaml                   # Render.com deployment
├── pyproject.toml                # Project config (ruff, mypy, pytest)
└── requirements*.txt             # Pinned dependencies
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Branch naming & commit conventions (Conventional Commits)
- Code style (ruff, mypy strict)
- PR checklist
- Testing requirements

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent async framework
- [Anthropic](https://www.anthropic.com/) for Claude 3.5 Sonnet
- [Azure](https://azure.microsoft.com/) for cloud-native services
- [OpenTelemetry](https://opentelemetry.io/) for observability standards