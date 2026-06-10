"""Escalation service"""
import logging
from typing import Dict, Any

from twilio.rest import Client
from app.core.config import settings

logger = logging.getLogger("railmind.escalation")

class EscalationService:
    """Handles incident escalation via SMS."""

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_FROM_NUMBER
        self.to_numbers = settings.TWILIO_TO_NUMBERS

    def send_sms_alert(self, alert_payload: Dict[str, Any]) -> bool:
        if not self.account_sid or not self.auth_token or not self.from_number:
            logger.warning("Twilio configuration is incomplete; skipping SMS alert.")
            return False
        if not self.to_numbers:
            logger.warning("No Twilio destination numbers configured; skipping SMS alert.")
            return False

        client = Client(self.account_sid, self.auth_token)
        body = (
            f"RailMind Critical Alert: {alert_payload.get('incident_type', 'Unknown')} on {alert_payload.get('platform', 'Unknown')}\n"
            f"Risk Level: {alert_payload.get('risk_level', 'Unknown')}\n"
            f"Risk Score: {alert_payload.get('risk_score', 0.0):.2f}\n"
            f"Timestamp: {alert_payload.get('timestamp', 'N/A')}"
        )

        success = True
        for to_number in self.to_numbers:
            try:
                client.messages.create(
                    body=body,
                    from_=self.from_number,
                    to=to_number,
                )
                logger.info("Sent SMS alert to %s", to_number)
            except Exception as exc:
                success = False
                logger.error("Failed to send SMS to %s: %s", to_number, exc, exc_info=True)

        return success

    def escalate(self, alert_payload: Dict[str, Any]) -> bool:
        logger.warning("Escalating alert: %s", alert_payload)
        return True

    def notify_security_team(self, alert_payload: Dict[str, Any]) -> bool:
        logger.warning("Notifying security team for alert: %s", alert_payload)
        return True
