"""Risk scoring service"""

from app.core.config import settings

class RiskScorer:
    """Calculates risk scores for incidents."""

    def calculate(self, incident_attributes):
        """Calculate a normalized risk score from observation fields."""
        score = 0.0

        lstm_score = float(incident_attributes.get("lstm_score", 0.0))
        score += lstm_score * 0.4

        edge_distance = float(incident_attributes.get("edge_distance", 0.0))
        platform_limit = settings.PLATFORM_EDGE_SAFETY_LIMIT_METERS
        edge_risk = max(0.0, (platform_limit * 2 - edge_distance) / (platform_limit * 2)) if platform_limit > 0 else 0.0
        score += edge_risk * 0.2

        duration_seconds = float(incident_attributes.get("duration_seconds", 0.0))
        duration_risk = min(1.0, duration_seconds / 60.0)
        score += duration_risk * 0.15

        loitering_duration = float(incident_attributes.get("loitering_duration", 0.0))
        loitering_risk = min(1.0, loitering_duration / 180.0)
        score += loitering_risk * 0.1

        following_distance = incident_attributes.get("following_distance")
        following_risk = 1.0 if following_distance is not None and float(following_distance) < 1.2 else 0.0
        score += following_risk * 0.1

        pose_classification = incident_attributes.get("pose_classification", "normal")
        pose_risk = 0.9 if pose_classification in ["distress", "aggressive"] else 0.6 if pose_classification in ["erratic", "suspicious", "following"] else 0.0
        score += pose_risk * 0.1

        context_multiplier = float(incident_attributes.get("context_multiplier", 1.0))
        score += min(1.0, context_multiplier * 0.1)

        return round(min(max(score, 0.0), 1.0), 2)

    def classify(self, score):
        """Classify a score as a human-readable risk level and action."""
        if score <= settings.LOW_RISK_THRESHOLD:
            return "Safe", "log_only"
        if score <= settings.MEDIUM_RISK_THRESHOLD:
            return "Low Risk", "passive_monitor"
        if score <= settings.HIGH_RISK_THRESHOLD:
            return "Medium Risk", "alert_staff"
        if score <= settings.CRITICAL_RISK_THRESHOLD:
            return "High Risk", "urgent_alert"
        return "Critical", "emergency_escalation"
