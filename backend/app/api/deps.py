from typing import Generator
# Assuming SQLAlchemy standard setup in app.core.database
# If database.py isn't built yet, we can mock or use a session placeholder
try:
    from app.core.database import SessionLocal
except ImportError:
    SessionLocal = None

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