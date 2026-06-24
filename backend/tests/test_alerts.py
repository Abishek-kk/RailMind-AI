"""Alert tests"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.database import Base
from app.models.alert import Alert
from app.api.deps import get_db
from app.main import app
from app.schemas.alert import AlertCreate
from app.services.escalation_service import EscalationService


def test_alert_creation():
    """Test alert creation"""
    alert = AlertCreate(
        person_id="P1",
        camera_id="C1",
        platform="Platform 1",
        incident_type="Loitering",
        risk_score=0.75,
        risk_level="Medium Risk",
        status="active",
    )
    assert alert.person_id == "P1"
    assert alert.risk_level == "Medium Risk"


def test_get_alerts():
    """Test getting alerts"""
    alerts = [
        AlertCreate(
            person_id="P2",
            camera_id="C2",
            platform="Platform 2",
            incident_type="Pickpocketing",
            risk_score=0.85,
            risk_level="High Risk",
            status="active",
        )
    ]
    assert len(alerts) == 1
    assert alerts[0].incident_type == "Pickpocketing"


@pytest.fixture
def alert_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.mark.asyncio
async def test_escalate_alert_updates_level_and_invokes_service(alert_db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "RAILMIND_API_KEY", "test-key")

    alert = Alert(
        platform="Platform 1",
        camera_id="CAM1",
        person_id="p1",
        incident_type="Loitering",
        risk_score=50.0,
        risk_level="Medium Risk",
        status="active",
        escalation_level=0,
    )
    alert_db_session.add(alert)
    alert_db_session.commit()
    alert_db_session.refresh(alert)

    escalated_payloads = []
    def mock_escalate(self, payload):
        escalated_payloads.append(payload)
        from app.services.escalation_service import SmsDeliveryResult
        return SmsDeliveryResult(True, "sent")

    monkeypatch.setattr(EscalationService, "escalate", mock_escalate)

    async def override_get_db():
        yield alert_db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                f"/api/alerts/{alert.id}/escalate",
                headers={"X-API-Key": "test-key"}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["escalation_level"] == 1
        assert len(escalated_payloads) == 1
        assert escalated_payloads[0]["alert_id"] == alert.id
    finally:
        app.dependency_overrides.pop(get_db, None)
