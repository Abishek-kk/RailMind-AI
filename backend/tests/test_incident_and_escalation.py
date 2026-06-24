"""Incident persistence and escalation timer tests."""
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

import app.models
from app.core.database import Base
from app.models.alert import Alert
from app.models.feedback import Feedback
from app.models.incident import Incident
from app.models.staff import Staff
from app.schemas.incident import IncidentCreate
from app.services.alert_service import AlertService
from app.services.escalation_service import EscalationService
from app.services.incident_service import IncidentService


def test_incident_accepts_platform_field():
    payload = {
        "alert_id": 10,
        "camera_id": "CCTV_P1_04",
        "platform": "Platform 1",
        "incident_type": "Loitering",
        "risk_score": 72,
        "risk_level": "Medium Risk",
        "status": "unacknowledged",
    }

    incident = Incident(**payload)
    schema = IncidentCreate(**payload)

    assert incident.platform == "Platform 1"
    assert schema.platform == "Platform 1"


def test_alert_service_starts_timer_for_medium_or_higher_active_alerts():
    service = AlertService(db=SimpleNamespace())

    high_alert = Alert(risk_level="High Risk", risk_score=91, status="active")
    critical_alert = Alert(risk_level="Critical", risk_score=100, status="active")
    medium_alert = Alert(risk_level="Medium Risk", risk_score=75, status="active")
    low_alert = Alert(risk_level="Low Risk", risk_score=45, status="active")
    resolved_alert = Alert(risk_level="High Risk", risk_score=91, status="resolved")

    assert service.should_start_escalation_timer(high_alert) is True
    assert service.should_start_escalation_timer(critical_alert) is True
    assert service.should_start_escalation_timer(medium_alert) is True
    assert service.should_start_escalation_timer(low_alert) is False
    assert service.should_start_escalation_timer(resolved_alert) is False


def test_mark_false_positive_creates_feedback_row():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        staff = Staff(id=42, name="Operator")
        alert = Alert(
            person_id="P1",
            camera_id="CCTV_P1_04",
            platform="Platform 1",
            incident_type="Loitering",
            risk_score=72,
            risk_level="Medium Risk",
        )
        db.add_all([staff, alert])
        db.commit()

        incident = Incident(
            alert_id=alert.id,
            camera_id=alert.camera_id,
            platform=alert.platform,
            incident_type=alert.incident_type,
            risk_score=alert.risk_score,
            risk_level=alert.risk_level,
        )
        db.add(incident)
        db.commit()

        updated = IncidentService(db).mark_false_positive(
            incident.id,
            staff_id=str(staff.id),
            notes="Shadow caused the alert",
        )

        feedback = db.query(Feedback).one()
        assert updated.false_positive is True
        assert updated.false_positive_reported_by == "42"
        assert feedback.alert_id == alert.id
        assert feedback.staff_id == staff.id
        assert feedback.is_false_positive is True
        assert feedback.notes == "Shadow caused the alert"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_escalation_timeout_only_escalates_active_alerts():
    escalated_payloads = []

    class RecordingEscalationService(EscalationService):
        def escalate(self, alert_payload):
            escalated_payloads.append(alert_payload)
            return True

    service = RecordingEscalationService()

    async def get_active_alert(_alert_id):
        return SimpleNamespace(status="active")

    async def get_resolved_alert(_alert_id):
        return SimpleNamespace(status="resolved")

    await service.escalate_after_timeout(1, 0, get_active_alert, {"alert_id": 1})
    await service.escalate_after_timeout(2, 0, get_resolved_alert, {"alert_id": 2})

    assert escalated_payloads == [{"alert_id": 1}]
