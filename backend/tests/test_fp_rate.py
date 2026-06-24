"""Station false-positive rate alert tests."""
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.models.alert import Alert
from app.models.feedback import Feedback
from app.models.station_fp_alert import StationFpAlert
from app.main import app


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.commit()
        session.close()
        engine.dispose()


def _make_alert(db, platform, hours_ago, is_fp=False):
    alert = Alert(
        platform=platform,
        camera_id="CAM1",
        person_id="p1",
        incident_type="Loitering",
        risk_score=50.0,
        risk_level="Medium Risk",
        status="active",
        is_false_positive=False,
        timestamp=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
    )
    db.add(alert)
    db.flush()

    if is_fp:
        fb = Feedback(
            alert_id=alert.id,
            staff_id=1,
            is_false_positive=True,
            submitted_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        )
        db.add(fb)
        db.flush()
    return alert


def test_fp_rate_above_threshold_flags_station(db_session):
    from app.services.station_fp_rate_service import flag_stations_above_threshold

    for i in range(10):
        _make_alert(db_session, "Platform 1", i, is_fp=(i < 6))

    flagged = flag_stations_above_threshold(db_session, threshold=0.40)
    assert "Platform 1" in flagged

    record = db_session.query(StationFpAlert).filter_by(platform="Platform 1").first()
    assert record is not None
    assert record.fp_rate == pytest.approx(0.6)


def test_fp_rate_below_threshold_does_not_flag(db_session):
    from app.services.station_fp_rate_service import flag_stations_above_threshold

    for i in range(10):
        _make_alert(db_session, "Platform 2", i, is_fp=(i < 3))

    flagged = flag_stations_above_threshold(db_session, threshold=0.40)
    assert "Platform 2" not in flagged

    record = db_session.query(StationFpAlert).filter_by(platform="Platform 2").first()
    assert record is None


@pytest.mark.asyncio
async def test_fp_rate_endpoint_returns_flagged_platforms(db_session, monkeypatch):
    monkeypatch.setattr(settings, "RAILMIND_API_KEY", "test-key")

    for i in range(10):
        _make_alert(db_session, "Platform 1", i, is_fp=(i < 6))

    from app.services.station_fp_rate_service import flag_stations_above_threshold
    flag_stations_above_threshold(db_session, threshold=0.40)

    from app.api.deps import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/analytics/fp-rate-alerts", headers={"X-API-Key": "test-key"})
        assert resp.status_code == 200
        data = resp.json()
        assert any(item["platform"] == "Platform 1" for item in data)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_fp_rate_endpoint_excludes_unflagged_platforms(db_session, monkeypatch):
    monkeypatch.setattr(settings, "RAILMIND_API_KEY", "test-key")

    for i in range(10):
        _make_alert(db_session, "Platform 2", i, is_fp=(i < 2))

    from app.services.station_fp_rate_service import flag_stations_above_threshold
    flag_stations_above_threshold(db_session, threshold=0.40)

    from app.api.deps import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/analytics/fp-rate-alerts", headers={"X-API-Key": "test-key"})
        assert resp.status_code == 200
        data = resp.json()
        assert not any(item["platform"] == "Platform 2" for item in data)
    finally:
        app.dependency_overrides.pop(get_db, None)
