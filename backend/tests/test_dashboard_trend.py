"""Dashboard trend aggregation tests."""
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.routes.dashboard import build_incident_trend, get_trend_bucket


def make_alert(incident_type: str, timestamp: datetime):
    return SimpleNamespace(incident_type=incident_type, timestamp=timestamp)


def test_get_trend_bucket_maps_dashboard_series():
    assert get_trend_bucket("Suicide Risk") == "Suicide Risk"
    assert get_trend_bucket("Pickpocketing") == "Pickpocketing"
    assert get_trend_bucket("Theft Prevention") == "Pickpocketing"
    assert get_trend_bucket("Loitering / Trespass") == "Loitering"
    assert get_trend_bucket("General Anomaly") is None


def test_build_incident_trend_counts_alerts_by_day_and_type():
    today = date(2026, 6, 11)
    yesterday = today - timedelta(days=1)
    alerts = [
        make_alert("Suicide Risk", datetime.combine(today, datetime.min.time())),
        make_alert("Pickpocketing", datetime.combine(today, datetime.min.time())),
        make_alert("Theft Prevention", datetime.combine(today, datetime.min.time())),
        make_alert("Loitering", datetime.combine(yesterday, datetime.min.time())),
    ]

    trend = build_incident_trend(alerts, 3, today)

    assert trend == [
        {"date": "2026-06-09", "Suicide Risk": 0, "Pickpocketing": 0, "Loitering": 0},
        {"date": "2026-06-10", "Suicide Risk": 0, "Pickpocketing": 0, "Loitering": 1},
        {"date": "2026-06-11", "Suicide Risk": 1, "Pickpocketing": 2, "Loitering": 0},
    ]
