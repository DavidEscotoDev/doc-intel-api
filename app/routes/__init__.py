"""API routes package."""

from app.routes import auth, health, process, query, upload

__all__ = ["upload", "process", "query", "health", "auth"]
