"""Escalation service"""
from dataclasses import dataclass
import logging
import asyncio
from typing import Dict, Any

from twilio.rest import Client
from app.core.config import settings

logger = logging.getLogger("railmind.escalation")


@dataclass
class SmsDeliveryResult:
    success: bool
    status: str
    detail: str = ""

    def __bool__(self) -> bool:
        return self.success


class EscalationService:
    """Handles incident escalation via SMS."""

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_FROM_NUMBER
        self.to_numbers = settings.TWILIO_TO_NUMBERS

    def send_sms_alert(self, alert_payload: Dict[str, Any]) -> SmsDeliveryResult:
        body = (
            f"RailMind Critical Alert: {alert_payload.get('incident_type', 'Unknown')} on {alert_payload.get('platform', 'Unknown')}\n"
            f"Risk Level: {alert_payload.get('risk_level', 'Unknown')}\n"
            f"Risk Score: {alert_payload.get('risk_score', 0.0):.2f}\n"
            f"Timestamp: {alert_payload.get('timestamp', 'N/A')}"
        )

        if not self.account_sid or not self.auth_token or not self.from_number:
            detail = "Twilio configuration is incomplete; no SMS was sent."
            logger.warning("%s Content:\n%s", detail, body)
            return SmsDeliveryResult(False, "not_configured", detail)

        if not self.to_numbers:
            detail = "No Twilio destination numbers configured; no SMS was sent."
            logger.warning("%s Content:\n%s", detail, body)
            return SmsDeliveryResult(False, "no_recipients", detail)

        # Real Twilio send path
        client = Client(self.account_sid, self.auth_token)

        failures = []
        for to_number in self.to_numbers:
            try:
                client.messages.create(
                    body=body,
                    from_=self.from_number,
                    to=to_number,
                )
                logger.info("Sent SMS alert to %s", to_number)
            except Exception as exc:
                failures.append(f"{to_number}: {exc}")
                logger.error("Failed to send SMS to %s: %s", to_number, exc, exc_info=True)

        if failures:
            return SmsDeliveryResult(False, "failed", "; ".join(failures))

        return SmsDeliveryResult(True, "sent")

    def escalate(self, alert_payload: Dict[str, Any]) -> SmsDeliveryResult:
        """
        Escalate alert via SMS to security team.
        This is the primary escalation method called after 60-second timeout.
        """
        logger.warning("Escalating alert via SMS: %s", alert_payload)
        return self.send_sms_alert(alert_payload)

    def notify_security_team(self, alert_payload: Dict[str, Any]) -> SmsDeliveryResult:
        """
        Notify security team of critical incident.
        """
        logger.warning("Notifying security team for alert: %s", alert_payload)
        return self.send_sms_alert(alert_payload)

    async def escalate_after_timeout(self, alert_id: int, timeout_seconds: int, 
                                     get_alert_fn, alert_payload: Dict[str, Any]):
        """
        Background task that waits for timeout_seconds and escalates if alert still unacknowledged.
        
        Args:
            alert_id: ID of the alert to check
            timeout_seconds: How long to wait before escalating (typically 60)
            get_alert_fn: Async function to retrieve alert status: async def get_alert(id) -> Alert or None
            alert_payload: Alert payload to send on escalation
        """
        try:
            logger.info(f"Starting escalation timer for alert {alert_id} ({timeout_seconds}s timeout)")
            await asyncio.sleep(timeout_seconds)
            
            # Check if alert is still active/unacknowledged.
            alert = await get_alert_fn(alert_id)
            if alert and alert.status in {"active", "unacknowledged"}:
                logger.warning(f"Alert {alert_id} still unacknowledged after {timeout_seconds}s. Escalating...")
                return self.escalate(alert_payload)
            else:
                logger.info(f"Alert {alert_id} was acknowledged before timeout. No escalation needed.")
                return None
        except asyncio.CancelledError:
            logger.info(f"Escalation timer for alert {alert_id} was cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in escalation timer for alert {alert_id}: {e}", exc_info=True)
            return SmsDeliveryResult(False, "failed", str(e))
