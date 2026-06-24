"""Alert service business logic"""
import asyncio
import concurrent.futures
import logging
import threading
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.services.escalation_service import EscalationService

logger = logging.getLogger("railmind.alerts")

_fallback_escalation_loop: Optional[asyncio.AbstractEventLoop] = None
_fallback_escalation_thread: Optional[threading.Thread] = None


def _start_fallback_escalation_loop() -> asyncio.AbstractEventLoop:
    global _fallback_escalation_loop, _fallback_escalation_thread
    if _fallback_escalation_loop is None or not _fallback_escalation_loop.is_running():
        _fallback_escalation_loop = asyncio.new_event_loop()

        def _run_loop(loop: asyncio.AbstractEventLoop) -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        _fallback_escalation_thread = threading.Thread(
            target=_run_loop,
            args=(_fallback_escalation_loop,),
            daemon=True,
        )
        _fallback_escalation_thread.start()
    return _fallback_escalation_loop

class AlertService:
    """Handles alert operations"""

    escalation_timers: Dict[int, Union[asyncio.Task[Any], concurrent.futures.Future[Any]]] = {}

    def __init__(self, db: Session, escalation_service: Optional[EscalationService] = None):
        self.db = db
        self.escalation_service = escalation_service or EscalationService()

    def list_alerts(self, filters: Optional[Dict[str, str]] = None) -> List[Alert]:
        query = self.db.query(Alert)
        if filters:
            if filters.get("risk_level"):
                query = query.filter(Alert.risk_level == filters["risk_level"])
            if filters.get("status"):
                query = query.filter(Alert.status == filters["status"])
            if filters.get("platform"):
                query = query.filter(Alert.platform == filters["platform"])
        return query.order_by(Alert.timestamp.desc()).all()

    def create_alert(self, payload: Dict[str, Any], start_escalation_timer: bool = True) -> Alert:
        alert = Alert(**payload)
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        if start_escalation_timer and self.should_start_escalation_timer(alert):
            alert.escalation_status = "pending_timeout"
            self.db.commit()
            self.db.refresh(alert)
            self._start_escalation_timer(alert)
        
        return alert

    def should_start_escalation_timer(self, alert: Alert) -> bool:
        """Return whether an alert should auto-escalate if left active."""
        if alert.status not in {"active", "unacknowledged"}:
            return False

        risk_level = (alert.risk_level or "").strip().lower()
        if any(level in risk_level for level in ("medium", "high", "critical")):
            return True

        return (alert.risk_score or 0.0) >= settings.MEDIUM_RISK_THRESHOLD

    def _start_escalation_timer(self, alert: Alert, timeout_seconds: int = 60) -> None:
        """Start a background task that escalates alert after timeout if not acknowledged."""
        async def escalation_task():
            result = await self.escalation_service.escalate_after_timeout(
                alert.id,
                timeout_seconds,
                self._get_alert_async,
                {
                    "alert_id": alert.id,
                    "incident_type": alert.incident_type,
                    "platform": alert.platform,
                    "risk_score": alert.risk_score,
                    "risk_level": alert.risk_level,
                    "timestamp": alert.timestamp.isoformat() if alert.timestamp else None
                }
            )
            if result is not None:
                self._record_escalation_result(alert.id, result)
            # Clean up timer reference after completion
            if alert.id in self.escalation_timers:
                del self.escalation_timers[alert.id]
        
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(escalation_task())
        except RuntimeError:
            loop = _start_fallback_escalation_loop()
            task = asyncio.run_coroutine_threadsafe(escalation_task(), loop)

        self.escalation_timers[alert.id] = task
        logger.info(f"Started escalation timer for alert {alert.id}")

    async def _get_alert_async(self, alert_id: int) -> Optional[Alert]:
        """Async wrapper to get alert status."""
        with SessionLocal() as db:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert is None:
                return None
            return SimpleNamespace(status=alert.status)

    def _record_escalation_result(self, alert_id: int, result: Any) -> None:
        """Persist SMS escalation outcome on the original alert for operator visibility."""
        success = bool(result)
        status = getattr(result, "status", None) or ("sent" if success else "failed")
        detail = getattr(result, "detail", "") or ""

        with SessionLocal() as db:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert is None:
                logger.warning("Unable to record escalation outcome; alert %s no longer exists", alert_id)
                return
            alert.escalation_level = (alert.escalation_level or 0) + 1
            alert.escalation_triggered_at = datetime.utcnow()
            alert.escalation_status = status
            alert.escalation_error = "" if success else detail
            db.commit()

    def get_alert(self, alert_id: int) -> Optional[Alert]:
        return self.db.query(Alert).filter(Alert.id == alert_id).first()

    def acknowledge_alert(self, alert_id: int, staff_id: Optional[str] = None) -> Optional[Alert]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        assignee = staff_id or "Unknown Operator"
        alert.operator_assigned = assignee
        alert.acknowledged_by = assignee
        self.db.commit()
        self.db.refresh(alert)
        
        if self.cancel_escalation_timer(alert_id):
            logger.info(f"Cancelled escalation timer for acknowledged alert {alert_id}")
        
        return alert

    def cancel_escalation_timer(self, alert_id: int) -> bool:
        timer = AlertService.escalation_timers.pop(alert_id, None)
        if timer is not None:
            timer.cancel()
            return True
        return False

    def escalate_alert(self, alert_id: int) -> Optional[Alert]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        alert.escalation_level = (alert.escalation_level or 0) + 1
        alert.escalation_triggered_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve_alert(self, alert_id: int) -> Optional[Alert]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        alert.status = "resolved"
        alert.resolved_at = func.now()
        self.db.commit()
        self.db.refresh(alert)
        
        if self.cancel_escalation_timer(alert_id):
            logger.info(f"Cancelled escalation timer for resolved alert {alert_id}")
        
        return alert
