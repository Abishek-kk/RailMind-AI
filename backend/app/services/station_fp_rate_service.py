"""Compute station false-positive rates and flag stations exceeding the threshold."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alert
from app.models.feedback import Feedback
from app.models.station_fp_alert import StationFpAlert

logger = logging.getLogger("railmind.fp_rate")


def compute_platform_fp_rates(db: Session, window_days: int = 7) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    q = (
        db.query(
            Alert.platform,
            func.count(Alert.id).label("total"),
            func.sum(
                case((Feedback.is_false_positive == True, 1), else_=0)
            ).label("fp_count"),
        )
        .outerjoin(Feedback, Alert.id == Feedback.alert_id)
        .filter(Alert.timestamp >= cutoff)
        .group_by(Alert.platform)
    )

    result = {}
    for platform, total, fp_count in q.all():
        t = int(total or 0)
        f = int(fp_count or 0)
        if t > 0:
            result[platform] = f / t
    return result


def flag_stations_above_threshold(db: Session, threshold: float = None) -> list:
    if threshold is None:
        threshold = settings.STATION_FP_RATE_ALERT_THRESHOLD

    rates = compute_platform_fp_rates(db)
    flagged = []
    for platform, fp_rate in rates.items():
        if fp_rate >= threshold:
            logger.warning(
                "Station FP rate alert: platform=%s fp_rate=%.2f%% threshold=%.2f%%",
                platform,
                fp_rate * 100,
                threshold * 100,
            )
            existing = (
                db.query(StationFpAlert)
                .filter(StationFpAlert.platform == platform)
                .first()
            )
            if existing is None:
                existing = StationFpAlert(platform=platform, fp_rate=fp_rate)
                db.add(existing)
            else:
                existing.fp_rate = fp_rate
                existing.alerted_at = datetime.now(timezone.utc)
                existing.resolved_at = None
            flagged.append(platform)

    if flagged:
        db.commit()
    return flagged
