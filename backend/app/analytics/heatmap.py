"""Generate heatmaps showing high-activity areas."""

from datetime import datetime, timezone

import numpy as np

from app.models.analytics import Analytics
from app.models.platform import Platform


class HeatmapGenerator:
    """Generates heatmaps from tracking data"""
    
    def __init__(self, frame_width, frame_height, grid_size=32):
        """Initialize heatmap generator"""
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.grid_size = grid_size
        self.heatmap = np.zeros((grid_size, grid_size), dtype=float)
    
    def update(self, poses):
        """Update heatmap with new pose data"""
        if not poses:
            return self.heatmap
        for pose in poses:
            center = pose.get("center") or pose.get("position")
            if center is None:
                bbox = pose.get("bounding_box") or pose.get("bbox")
                if bbox and len(bbox) >= 4:
                    center = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
            if center is None:
                continue
            x, y = center
            col = min(self.grid_size - 1, int((x / self.frame_width) * self.grid_size))
            row = min(self.grid_size - 1, int((y / self.frame_height) * self.grid_size))
            if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
                self.heatmap[row, col] += 1.0
        return self.heatmap
    
    def get_heatmap(self):
        """Get current heatmap"""
        if self.heatmap is None:
            self.heatmap = np.zeros((self.grid_size, self.grid_size), dtype=float)
        return self.heatmap.tolist()
    
    def identify_hotspots(self):
        """Identify high-activity areas"""
        if self.heatmap is None:
            return []
        flattened = self.heatmap.flatten()
        if flattened.sum() == 0:
            return []
        threshold = np.percentile(flattened, 85)
        hotspots = []
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.heatmap[row, col] >= threshold:
                    hotspots.append({"row": row, "col": col, "value": float(self.heatmap[row, col])})
        return hotspots


_heatmap_registry = {}


def update_live_heatmap(camera_id, platform, frame_width, frame_height, poses, db=None):
    """Update or create a live heatmap for a camera stream and optionally persist hotspots."""
    if frame_width <= 0 or frame_height <= 0:
        return None

    entry = _heatmap_registry.get(camera_id)
    if entry is None:
        entry = {
            "platform": platform,
            "generator": HeatmapGenerator(frame_width, frame_height),
        }
        _heatmap_registry[camera_id] = entry
    else:
        entry["platform"] = platform

    entry["generator"].update(poses)
    if db is not None:
        persist_heatmap_snapshot(db, camera_id, platform, entry["generator"])
    return entry["generator"]


def persist_heatmap_snapshot(db, camera_id: str, platform: str, generator: HeatmapGenerator):
    """Persist current hotspot aggregates so analytics survive process restarts."""
    heatmap = generator.heatmap
    max_value = float(heatmap.max()) if heatmap.size else 0.0
    if max_value <= 0:
        return []

    now = datetime.now(timezone.utc)
    platform_row = _get_or_create_platform(db, platform, camera_id)
    persisted_rows = []

    for hotspot in generator.identify_hotspots():
        intensity = min(1.0, hotspot["value"] / max_value)
        zone = f"{camera_id} R{hotspot['row']:02d} C{hotspot['col']:02d}"
        row = (
            db.query(Analytics)
            .filter(
                Analytics.date == now.date(),
                Analytics.hour == now.hour,
                Analytics.platform_id == platform_row.id,
                Analytics.camera_id == camera_id,
                Analytics.zone == zone,
            )
            .first()
        )

        if row is None:
            row = Analytics(
                date=now.date(),
                hour=now.hour,
                platform_id=platform_row.id,
                camera_id=camera_id,
                zone=zone,
            )
            db.add(row)

        row.hotspot_count = int(hotspot["value"])
        row.hotspot_intensity = round(float(intensity), 4)
        persisted_rows.append(row)

    db.commit()
    return persisted_rows


def get_persistent_platform_heatmap(db, platform: str | None = None):
    """Return persisted hotspot rows, suitable for multi-worker and restart-safe dashboards."""
    query = db.query(Analytics, Platform).join(Platform, Analytics.platform_id == Platform.id)
    query = query.filter(Analytics.zone.isnot(None), Analytics.hotspot_count > 0)
    if platform:
        query = query.filter((Platform.name == platform) | (Platform.platform_number == platform))

    rows = []
    for analytics_row, platform_row in query.all():
        rows.append(
            {
                "platform": platform_row.name or platform_row.platform_number,
                "camera_id": analytics_row.camera_id,
                "zone": analytics_row.zone,
                "intensity": round(float(analytics_row.hotspot_intensity or 0.0), 4),
                "hotspot_count": int(analytics_row.hotspot_count or 0),
                "date": analytics_row.date.isoformat() if analytics_row.date else None,
                "hour": analytics_row.hour,
            }
        )

    return sorted(rows, key=lambda item: (item["date"] or "", item["hour"] or -1, item["intensity"]), reverse=True)


def _get_or_create_platform(db, platform: str, camera_id: str) -> Platform:
    platform_row = (
        db.query(Platform)
        .filter((Platform.name == platform) | (Platform.platform_number == platform))
        .first()
    )
    if platform_row is not None:
        camera_ids = list(platform_row.camera_ids_json or [])
        if camera_id not in camera_ids:
            camera_ids.append(camera_id)
            platform_row.camera_ids_json = camera_ids
            db.flush()
        return platform_row

    platform_row = Platform(
        station_id="default",
        platform_number=platform,
        name=platform,
        camera_ids_json=[camera_id],
    )
    db.add(platform_row)
    db.flush()
    return platform_row


def get_live_platform_heatmap():
    """Return normalized live hotspot intensities grouped for dashboard rendering."""
    rows = []
    for camera_id, entry in _heatmap_registry.items():
        generator = entry["generator"]
        heatmap = generator.heatmap
        max_value = float(heatmap.max()) if heatmap.size else 0.0
        if max_value <= 0:
            continue

        for hotspot in generator.identify_hotspots():
            intensity = min(1.0, hotspot["value"] / max_value)
            rows.append(
                {
                    "platform": entry["platform"],
                    "zone": f"{camera_id} R{hotspot['row']:02d} C{hotspot['col']:02d}",
                    "intensity": round(intensity, 4),
                }
            )

    return sorted(rows, key=lambda item: item["intensity"], reverse=True)


def clear_live_heatmaps():
    """Clear live heatmap state; intended for tests and process cleanup."""
    _heatmap_registry.clear()
