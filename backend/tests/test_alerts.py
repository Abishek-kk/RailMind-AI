"""Alert tests"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.schemas.alert import AlertCreate


def test_alert_creation():
    """Test alert creation"""
    alert = AlertCreate(
        person_id="P1",
        camera_id="C1",
        platform="Platform 1",
        incident_type="Loitering",
        risk_score=0.75,
        risk_level="Medium Risk",
        status="unacknowledged",
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
            status="unacknowledged",
        )
    ]
    assert len(alerts) == 1
    assert alerts[0].incident_type == "Pickpocketing"
