"""Generate heatmaps showing high-activity areas"""

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
