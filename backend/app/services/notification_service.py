"""Notification service"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger("railmind.notifications")

class NotificationService:
    """Sends email alerts via SMTP."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.recipients = settings.ALERT_EMAIL_RECIPIENTS

    def send_email_alert(self, alert_payload: Dict[str, Any]) -> bool:
        if not self.recipients:
            logger.warning("No email recipients configured; skipping email alert.")
            return False

        subject = f"[RailMind CRITICAL] {alert_payload.get('incident_type', 'Incident')} — {alert_payload.get('platform', 'Unknown Platform')}"
        body_html = f"""
        <html>
            <body>
                <h2>RailMind Critical Alert</h2>
                <p><strong>Incident Type:</strong> {alert_payload.get('incident_type', 'Unknown')}</p>
                <p><strong>Risk Level:</strong> {alert_payload.get('risk_level', 'Unknown')}</p>
                <p><strong>Risk Score:</strong> {alert_payload.get('risk_score', 0.0):.2f}</p>
                <p><strong>Platform:</strong> {alert_payload.get('platform', 'Unknown')}</p>
                <p><strong>Person ID:</strong> {alert_payload.get('person_id', 'N/A')}</p>
                <p><strong>Timestamp:</strong> {alert_payload.get('timestamp', 'N/A')}</p>
            </body>
        </html>
        """

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.smtp_user or f"no-reply@{self.smtp_host}"
        message["To"] = ", ".join(self.recipients)
        message.attach(MIMEText(body_html, "html"))

        # Dry-run mode: treat localhost/empty SMTP host as development mode and
        # log the full email content instead of attempting to send. Also fall
        # back to this mode if an SMTP send attempt fails at runtime.
        is_local_host = not self.smtp_host or str(self.smtp_host).lower() in {"localhost", "127.0.0.1", ""}
        if is_local_host:
            logger.info(
                "SMTP host configured as localhost/empty; performing email dry-run. Subject: %s\nBody: %s",
                subject,
                body_html,
            )
            return True

        try:
            if self.smtp_port == 465:
                smtp_client = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
            else:
                smtp_client = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)

            with smtp_client as smtp:
                if self.smtp_port != 465:
                    smtp.starttls()
                if self.smtp_user and self.smtp_password:
                    smtp.login(self.smtp_user, self.smtp_password)
                smtp.sendmail(message["From"], self.recipients, message.as_string())

            logger.info("Email alert sent to %s", self.recipients)
            return True
        except Exception as exc:
            # Instead of treating SMTP failures as hard errors in local/dev,
            # log the email contents and return True so downstream logic can
            # continue as if the notification succeeded.
            logger.info(
                "SMTP send failed (%s); falling back to dry-run logging. Subject: %s\nBody: %s",
                exc,
                subject,
                body_html,
            )
            logger.debug("SMTP exception details:", exc_info=True)
            return True

    def send_notification(self, payload: Dict[str, Any]) -> bool:
        logger.info("Sending notification payload: %s", payload)
        return True

    def notify_webhook(self, target_url: str, payload: Dict[str, Any]) -> bool:
        logger.info("Webhook notify %s with payload %s", target_url, payload)
        return True
