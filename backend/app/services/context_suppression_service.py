"""Adjust alert thresholds based on historical peak-density time windows."""

import logging
import time
from collections import defaultdict
from typing import Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.incident import Incident

logger = logging.getLogger("railmind.context")


class ContextSuppressionService:
    """Suppresses expected edge-proximity spikes during peak platform hours."""

    PEAK_PERCENTILE = 0.8
    PEAK_MULTIPLIER = 1.3
    NORMAL_MULTIPLIER = 1.0
    CACHE_TTL_SECONDS = 3600

    def __init__(self, db: Optional[Session] = None):
        self._db = db
        self._peak_hours_cache: Dict[str, set] = {}
        self._cache_expires_at = 0.0

    def get_threshold_adjustment(self, platform: str, current_hour: int, db: Optional[Session] = None) -> float:
        if not platform:
            return self.NORMAL_MULTIPLIER
        if db is not None:
            self._db = db
        peak_hours = self._load_peak_hours()
        if current_hour in peak_hours.get(platform, set()):
            return self.PEAK_MULTIPLIER
        return self.NORMAL_MULTIPLIER

    def _load_peak_hours(self) -> Dict[str, set]:
        now = time.time()
        if now < self._cache_expires_at:
            return self._peak_hours_cache

        result = self._compute_peak_hours()
        self._peak_hours_cache = result
        self._cache_expires_at = now + self.CACHE_TTL_SECONDS
        return result

    def _compute_peak_hours(self) -> Dict[str, set]:
        if self._db is None:
            return {}

        try:
            volume_rows = (
                self._db.query(
                    Incident.platform,
                    func.strftime("%H", Incident.timestamp).label("hour"),
                    func.count(Incident.id).label("volume"),
                )
                .group_by(Incident.platform, func.strftime("%H", Incident.timestamp))
                .all()
            )
        except Exception as exc:
            logger.warning("Failed to query incident volume for context suppression: %s", exc)
            return {}

        platform_hours: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        for platform, hour_str, volume in volume_rows:
            if platform is None:
                continue
            try:
                hour = int(hour_str)
            except (TypeError, ValueError):
                continue
            platform_hours[platform][hour] = int(volume)

        peak_hours: Dict[str, set] = {}
        for platform, hours in platform_hours.items():
            volumes = sorted(hours.values())
            if not volumes:
                continue
            cutoff_index = max(0, int(len(volumes) * self.PEAK_PERCENTILE) - 1)
            cutoff = volumes[cutoff_index]
            peak_hours[platform] = {hour for hour, count in hours.items() if count >= cutoff}

        return peak_hours
