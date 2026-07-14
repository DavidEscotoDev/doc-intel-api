# Contributing Guide

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd document-intelligence-api

# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linters
ruff check .
mypy app/
```

## Development Workflow

### Branching
- `main` — production-ready, protected
- Feature branches: `feat/short-description`
- Fix branches: `fix/short-description`
- Docs: `docs/short-description`

### Commits (Conventional Commits)
```
feat: add document upload endpoint
fix: handle empty file upload validation
docs: update README with deployment guide
refactor: extract storage abstraction
test: add integration tests for auth
chore: update dependencies
```

### Pull Request Checklist
- [ ] Tests pass (`pytest -x`)
- [ ] Linting passes (`ruff check .`)
- [ ] Type checking passes (`mypy app/`)
- [ ] Coverage ≥ 85% (`pytest --cov=app --cov-fail-under=85`)
- [ ] Conventional commit messages
- [ ] Self-review completed
- [ ] Documentation updated (if applicable)

## Code Style

### Python (ruff + mypy)
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "UP", "B", "C4", "SIM", "T20", "PI", "PT"]
ignore = ["S101", "T201"]

[tool.mypy]
strict = true
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true
```

### Type Hints
- All functions must have type hints
- Use `typing` imports: `from typing import Optional, List, AsyncGenerator`
- Prefer `|` over `Union` (Python 3.10+)

### Async Patterns
```python
# Good: Proper async context managers
async with db.session() as session:
    result = await session.execute(query)

# Good: Concurrent operations
results = await asyncio.gather(
    fetch_user(user_id),
    fetch_posts(user_id),
)

# Avoid: Blocking calls in async functions
# Bad: time.sleep(1)  # Use asyncio.sleep(1)
# Bad: requests.get(url)  # Use httpx.AsyncClient
```

## Testing

### Test Structure
```
tests/
├── conftest.py           # Fixtures
├── test_auth.py          # Unit: auth middleware
├── test_routes_upload.py # Integration: upload endpoints
├── test_routes_query.py  # Integration: query endpoints
├── test_middleware.py    # Integration: middleware
├── test_security_validation.py # Unit: validation
└── test_tasks_processor.py # Integration: background tasks
```

### Fixtures
```python
# tests/conftest.py
@pytest.fixture
async def test_api_key(db_session):
    key_hash = pwd_context.hash("di_testkey123")
    api_key = APIKey(key_hash=key_hash, name="Test", rate_limit=100)
    db_session.add(api_key)
    await db_session.commit()
    return api_key

@pytest.fixture
def auth_headers(test_api_key):
    return {"Authorization": "Bearer di_testkey123"}
```

### Running Tests
```bash
# All tests with coverage
pytest --cov=app --cov-report=term-missing --cov-fail-under=85

# Specific module
pytest tests/test_routes_upload.py -v

# Watch mode (requires pytest-watch)
ptw tests/
```

## Configuration

### Environment Variables
```bash
# .env (development)
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/docintel
ANTHROPIC_API_KEY=sk-ant-...
API_KEY_PREFIX=di_
LOG_LEVEL=DEBUG
```

### Settings Validation
All config goes through `app/config.py` with Pydantic v2 validation.

## Documentation

### ADRs
Architecture Decision Records in `docs/adr/`:
- 001: Async-First Architecture
- 002: Azure-Native Integrations
- 003: API Key Authentication
- 004: Background Processing
- 005: Observability Stack
- 006: Pydantic v2

### API Docs
- Swagger UI: `/docs` (dev only)
- OpenAPI: `/openapi.json`

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create PR with `release/vX.Y.Z`
4. Merge to `main` triggers CI/CD
5. GitHub Actions builds & deploys

## Questions?

Open an issue or ask in PR comments.