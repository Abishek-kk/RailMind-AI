"""Generate heatmaps showing high-activity areas."""

import numpy as np


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


def update_live_heatmap(camera_id, platform, frame_width, frame_height, poses):
    """Update or create a live heatmap for a camera stream."""
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
    return entry["generator"]


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
