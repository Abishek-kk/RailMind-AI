import os
from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Ensure the data directory exists for SQLite storage
db_path = settings.DATABASE_URL.replace("sqlite:///", "")
db_dir = os.path.dirname(db_path)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

# ConnectArgs check avoids thread pool errors when using SQLite concurrently
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

# Initialize Database Pipeline Connection Engine
Engine = create_engine(
    settings.DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True  # Automatically checks and revives dead connection frames
)

# Session Factory Configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# Base Declarative Object for ORM Model Parsing
Base = declarative_base()

def init_db() -> None:
    """
    Initializes database tables based on system specifications.
    Imports models internally inside the function context to break circular dependencies.
    """
    # Import all models explicitly before creating tables
    import app.models.alert
    import app.models.incident
    import app.models.feed
    
    Base.metadata.create_all(bind=Engine)
    _ensure_incident_platform_column()


def _ensure_incident_platform_column() -> None:
    """Backfill the platform column for existing SQLite incidents tables."""
    inspector = inspect(Engine)
    if "incidents" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("incidents")}
    if "platform" in columns:
        return

    with Engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE incidents ADD COLUMN platform VARCHAR NOT NULL DEFAULT 'Unknown Platform'")
        )
