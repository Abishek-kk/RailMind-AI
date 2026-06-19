from typing import Generator
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

# Assuming SQLAlchemy standard setup in app.core.database
# If database.py isn't built yet, we can mock or use a session placeholder
try:
    from app.core.database import SessionLocal
except ImportError:
    SessionLocal = None

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """Require a configured API key for protected API routes."""
    configured_key = settings.RAILMIND_API_KEY.strip()
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured. Set RAILMIND_API_KEY before exposing the API.",
        )

    if not api_key or not secrets.compare_digest(api_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

def get_db() -> Generator:
    """
    FastAPI dependency that provides a thread-safe database session per request
    and ensures it is properly closed when the request is complete.
    """
    if SessionLocal is None:
        yield None
        return
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
