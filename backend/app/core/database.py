import os
from sqlalchemy import create_engine
from sqlalchemy import event
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


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Enable SQLite foreign-key enforcement for new DB connections."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session Factory Configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# Base Declarative Object for ORM Model Parsing
Base = declarative_base()

def init_db() -> None:
    """
    Initializes database tables based on system specifications.
    Imports models internally inside the function context to break circular dependencies.
    """
    # Import all models explicitly before creating tables.
    import app.models.alert
    import app.models.analytics
    import app.models.feedback
    import app.models.feed
    import app.models.incident
    import app.models.platform
    import app.models.staff
    import app.models.station_fp_alert
    import app.models.track
    import app.models.training_run
    
    Base.metadata.create_all(bind=Engine)
    _ensure_feed_stream_url_column()
    _ensure_incident_platform_column()
    _ensure_alert_delivery_columns()
    _ensure_analytics_hotspot_columns()
    _ensure_training_run_sample_columns()
    _ensure_station_fp_alerts_table()
    _ensure_alert_reasoning_mode_column()
    _ensure_incident_reasoning_mode_column()


def _ensure_feed_stream_url_column() -> None:
    """Add the stream_url column to the feeds table if it does not exist."""
    inspector = inspect(Engine)
    if "feeds" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("feeds")}
    if "stream_url" in columns:
        return

    with Engine.begin() as connection:
        connection.execute(text("ALTER TABLE feeds ADD COLUMN stream_url VARCHAR"))


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


def _ensure_alert_delivery_columns() -> None:
    """Add notification/escalation visibility columns to existing alerts tables."""
    inspector = inspect(Engine)
    if "alerts" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("alerts")}
    required_columns = {
        "notification_status": "VARCHAR",
        "notification_error": "VARCHAR",
        "escalation_status": "VARCHAR",
        "escalation_error": "VARCHAR",
    }

    with Engine.begin() as connection:
        for column_name, column_type in required_columns.items():
            if column_name not in columns:
                connection.execute(text(f"ALTER TABLE alerts ADD COLUMN {column_name} {column_type}"))


def _ensure_analytics_hotspot_columns() -> None:
    """Add persistent heatmap columns to existing analytics tables."""
    inspector = inspect(Engine)
    if "analytics" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("analytics")}
    required_columns = {
        "camera_id": "VARCHAR",
        "zone": "VARCHAR",
        "hotspot_count": "INTEGER NOT NULL DEFAULT 0",
        "hotspot_intensity": "FLOAT NOT NULL DEFAULT 0.0",
        "updated_at": "DATETIME",
    }

    with Engine.begin() as connection:
        for column_name, column_type in required_columns.items():
            if column_name not in columns:
                connection.execute(text(f"ALTER TABLE analytics ADD COLUMN {column_name} {column_type}"))


def _ensure_training_run_sample_columns() -> None:
    """Add continual-learning sample counters to existing training run tables."""
    inspector = inspect(Engine)
    if "training_runs" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("training_runs")}
    required_columns = {
        "synthetic_sample_count": "INTEGER NOT NULL DEFAULT 0",
        "real_sample_count": "INTEGER NOT NULL DEFAULT 0",
    }

    with Engine.begin() as connection:
        for column_name, column_type in required_columns.items():
            if column_name not in columns:
                connection.execute(text(f"ALTER TABLE training_runs ADD COLUMN {column_name} {column_type}"))


def _ensure_station_fp_alerts_table() -> None:
    """Create station_fp_alerts table if it does not exist."""
    inspector = inspect(Engine)
    if "station_fp_alerts" in inspector.get_table_names():
        return

    with Engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS station_fp_alerts (
                id INTEGER PRIMARY KEY,
                platform VARCHAR NOT NULL UNIQUE,
                fp_rate FLOAT NOT NULL,
                alerted_at DATETIME NOT NULL,
                resolved_at DATETIME
            )
        """))


def _ensure_alert_reasoning_mode_column() -> None:
    """Add reasoning_mode column to existing alerts table if missing."""
    inspector = inspect(Engine)
    if "alerts" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("alerts")}
    if "reasoning_mode" in columns:
        return

    with Engine.begin() as connection:
        connection.execute(text("ALTER TABLE alerts ADD COLUMN reasoning_mode VARCHAR"))


def _ensure_incident_reasoning_mode_column() -> None:
    """Add reasoning_mode column to existing incidents table if missing."""
    inspector = inspect(Engine)
    if "incidents" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("incidents")}
    if "reasoning_mode" in columns:
        return

    with Engine.begin() as connection:
        connection.execute(text("ALTER TABLE incidents ADD COLUMN reasoning_mode VARCHAR"))
