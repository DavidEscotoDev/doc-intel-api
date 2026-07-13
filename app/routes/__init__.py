"""API routes package."""

from app.routes import upload, process, query, health, auth

__all__ = ["upload", "process", "query", "health", "auth"]