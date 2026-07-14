# ADR 001: Async-First Architecture

## Context
The Document Intelligence API must handle I/O-heavy workloads: file uploads, text extraction, LLM API calls, and database operations. Synchronous code would block threads and limit concurrency.

## Decision
Use **async/await throughout** the entire stack:
- **FastAPI** for async request handling
- **SQLAlchemy 2.0** with async session (`async_sessionmaker`, `AsyncSession`)
- **asyncpg** as the PostgreSQL driver
- **httpx.AsyncClient** for external HTTP calls
- **FastAPI BackgroundTasks** for async background processing

## Consequences

### Positive
- High concurrency with low thread count (1 worker handles 100s of concurrent requests)
- Natural fit for I/O-bound workloads
- Better resource utilization under load

### Negative
- All dependencies must be async-compatible (no blocking calls in async functions)
- Team must understand async patterns (event loop, `await`, task groups)
- Debugging async stack traces can be harder

## Implementation Notes
- Database: `create_async_engine`, `async_sessionmaker`, `AsyncSession`
- LLM calls: `anthropic.AsyncAnthropic().messages.create()`
- File I/O: `aiofiles` for async file operations
- Background: `BackgroundTasks.add_task(async_func, args)`

## Alternatives Considered
- **Thread pool executor**: Adds complexity, doesn't solve fundamental I/O blocking
- **Celery + Redis**: Overkill for current scale; BackgroundTasks sufficient for MVP
- **Sync FastAPI + workers**: Wastes resources on I/O wait