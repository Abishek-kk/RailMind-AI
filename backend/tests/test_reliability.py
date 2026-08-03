"""Architecture and reliability regression tests."""

import asyncio
from contextlib import suppress

import pytest
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, inspect

import app.core.processor_manager as processor_manager
import app.models
from app.core.database import Base
from app.features.loitering_detector import LoiteringDetector
from app.core.config import settings
from app.main import _ensure_transformer_models, app
from app.models.feedback import Feedback
from app.models.incident import Incident


def test_incident_alert_id_has_foreign_key():
    foreign_keys = Incident.__table__.c.alert_id.foreign_keys

    assert len(foreign_keys) == 1
    assert next(iter(foreign_keys)).target_fullname == "alerts.id"


def test_documented_database_tables_are_registered():
    expected_tables = {
        "alerts",
        "analytics",
        "feedback",
        "feeds",
        "incidents",
        "platforms",
        "staff",
        "tracks",
        "training_runs",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_documented_database_tables_create_on_fresh_sqlite():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert {
        "tracks",
        "analytics",
        "platforms",
        "feedback",
    }.issubset(tables)

    track_columns = {column["name"] for column in inspector.get_columns("tracks")}
    assert {
        "track_id",
        "camera_id",
        "session_id",
        "feature_sequence_json",
        "transformer_label",
        "confidence",
    }.issubset(track_columns)

    analytics_columns = {column["name"] for column in inspector.get_columns("analytics")}
    assert {
        "date",
        "hour",
        "platform_id",
        "camera_id",
        "zone",
        "incident_count",
        "avg_risk_score",
        "false_positive_count",
        "hotspot_count",
        "hotspot_intensity",
    }.issubset(analytics_columns)

    platform_columns = {column["name"] for column in inspector.get_columns("platforms")}
    assert {"station_id", "platform_number", "camera_ids_json", "edge_zone_config_json"}.issubset(platform_columns)

    feedback_columns = {column["name"] for column in inspector.get_columns("feedback")}
    assert {"alert_id", "staff_id", "is_false_positive", "notes", "submitted_at"}.issubset(feedback_columns)


def test_feedback_links_alerts_staff_and_training_runs():
    foreign_key_targets = {
        foreign_key.target_fullname
        for column in Feedback.__table__.columns
        for foreign_key in column.foreign_keys
    }

    assert {"alerts.id", "staff.id", "training_runs.id"}.issubset(foreign_key_targets)


def test_cors_does_not_use_wildcard_with_credentials():
    cors_middleware = next(
        middleware for middleware in app.user_middleware if middleware.cls is CORSMiddleware
    )

    assert cors_middleware.kwargs["allow_credentials"] is True
    assert "*" not in cors_middleware.kwargs["allow_origins"]


def test_loitering_detector_bounds_position_history():
    detector = LoiteringDetector(duration_threshold=2, fps=30)

    for frame_id in range(300):
        detector.detect(1, {"center": (10, 10)}, frame_id)

    assert len(detector.presence_tracking[1]) == 60


def test_loitering_detector_clears_disappeared_tracks():
    detector = LoiteringDetector(duration_threshold=2, fps=30)

    detector.detect(1, {"center": (10, 10)}, 0)
    detector.clear_track(1)

    assert 1 not in detector.presence_tracking
    assert 1 not in detector.first_seen_frames


def test_transformer_startup_does_not_generate_untrained_placeholders(tmp_path, monkeypatch):
    pose_model = tmp_path / "yolov8n-pose.pt"
    pose_model.write_bytes(b"placeholder")

    monkeypatch.setattr(settings, "MODEL_DIR", str(tmp_path / "models"))
    monkeypatch.setattr(settings, "POSE_MODEL_PATH", str(pose_model))

    _ensure_transformer_models()

    assert list((tmp_path / "models").glob("*.pt")) == []


def test_start_processor_requires_running_event_loop(monkeypatch):
    processor_manager._processors.clear()

    class ExplodingVideoProcessor:
        def __init__(self, *args, **kwargs):
            raise AssertionError("VideoProcessor should not be constructed without a running loop")

    monkeypatch.setattr(processor_manager, "VideoProcessor", ExplodingVideoProcessor)

    with pytest.raises(RuntimeError, match="running asyncio event loop"):
        processor_manager.start_processor("missing.mp4", "CAM_NO_LOOP", "Platform 1")


@pytest.mark.asyncio
async def test_start_processor_attaches_task_to_running_loop(monkeypatch):
    processor_manager._processors.clear()

    class DummyVideoProcessor:
        def __init__(self, *args, **kwargs):
            pass

        async def start_processing_loop(self):
            await asyncio.Event().wait()

        def stop_processing_loop(self):
            pass

    monkeypatch.setattr(processor_manager, "VideoProcessor", DummyVideoProcessor)

    task = processor_manager.start_processor("sample.mp4", "CAM_LOOP", "Platform 1")

    try:
        assert task.get_loop() is asyncio.get_running_loop()
    finally:
        processor_manager.stop_processor("CAM_LOOP")
        with suppress(asyncio.CancelledError):
            await task
        processor_manager._processors.clear()
