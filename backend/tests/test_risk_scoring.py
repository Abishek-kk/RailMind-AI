"""Risk scoring tests."""

from app.core.config import settings
from app.services.risk_scoring import RiskScorer


def test_risk_score_additive_weights_sum_to_one():
    weights = settings.RISK_SCORE_WEIGHTS

    assert "context" not in weights
    assert sum(weights.values()) == 1.0


def test_context_multiplier_scales_base_score_without_raw_addition(monkeypatch):
    scorer = RiskScorer()
    incident = {
        "lstm_score": 0.5,
        "edge_distance": settings.PLATFORM_EDGE_SAFETY_LIMIT_METERS * 2,
        "duration_seconds": 0,
        "loitering_duration": 0,
        "following_distance": None,
        "pose_classification": "normal",
        "context_multiplier": 1.5,
    }

    monkeypatch.setattr(settings, "RISK_SCORE_WEIGHTS", {
        "lstm": 1.0,
        "edge": 0.0,
        "duration": 0.0,
        "loitering": 0.0,
        "following": 0.0,
        "pose": 0.0,
    })
    monkeypatch.setattr(settings, "RISK_CONTEXT_MULTIPLIER_WEIGHT", 0.1)

    assert scorer.calculate(incident) == 52


def test_legacy_context_weight_is_excluded_from_additive_normalization(monkeypatch):
    scorer = RiskScorer()
    incident = {
        "lstm_score": 1.0,
        "edge_distance": 0.0,
        "duration_seconds": 60,
        "loitering_duration": 180,
        "following_distance": 0.1,
        "pose_classification": "distress",
        "context_multiplier": 1.0,
    }

    monkeypatch.setattr(settings, "RISK_SCORE_WEIGHTS", {
        "lstm": 0.4,
        "edge": 0.2,
        "duration": 0.15,
        "loitering": 0.1,
        "following": 0.1,
        "pose": 0.1,
        "context": 0.1,
    })

    assert scorer.calculate(incident) <= 100


def test_risk_classification_matches_documented_action_ranges():
    scorer = RiskScorer()

    assert scorer.classify(39) == ("Safe", "log_only")
    assert scorer.classify(40) == ("Low Risk", "alert_staff")
    assert scorer.classify(69) == ("Low Risk", "alert_staff")
    assert scorer.classify(70) == ("Medium Risk", "alert_security")
    assert scorer.classify(89) == ("Medium Risk", "alert_security")
    assert scorer.classify(90) == ("Critical", "emergency_escalation")
