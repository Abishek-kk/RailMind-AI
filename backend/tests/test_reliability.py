"""Architecture and reliability regression tests."""

from fastapi.middleware.cors import CORSMiddleware

from app.features.loitering_detector import LoiteringDetector
from app.main import app
from app.models.incident import Incident


def test_incident_alert_id_has_foreign_key():
    foreign_keys = Incident.__table__.c.alert_id.foreign_keys

    assert len(foreign_keys) == 1
    assert next(iter(foreign_keys)).target_fullname == "alerts.id"


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
