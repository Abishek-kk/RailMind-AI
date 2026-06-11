import numpy as np
from ultralytics import YOLO
from typing import Optional
from app.core.config import settings


class PoseEstimator:
    def __init__(self, model_path: Optional[str] = None, device: str | None = None):
        """Loads the specialized YOLOv8 Pose model configuration.

        Args:
            model_path: Path to the YOLOv8 pose weights. If None, uses the
                configured `settings.POSE_MODEL_PATH`.
            device: Inference device string (e.g. 'cpu' or 'cuda:0'). If None,
                uses `settings.POSE_DEVICE`.
        """
        model_path = model_path or settings.POSE_MODEL_PATH
        device = device or settings.POSE_DEVICE

        # Load model and move to device if supported
        self.model = YOLO(model_path)
        try:
            # ultralytics models support .to(device)
            self.model.to(device)
        except Exception:
            # If moving to device fails, continue with default
            pass

    def estimate_pose(self, frame: np.ndarray) -> list:
        """Process a raw frame and return pose detections.

        Returns list of {"bbox": [x1,y1,x2,y2], "keypoints": [[x,y,conf], ...]}
        """
        results = self.model(frame, verbose=False)[0]
        pose_detections = []

        if getattr(results, "keypoints", None) is not None and len(results.keypoints.data) > 0:
            # keypoints.data shape is (num_people, 17, 3)
            for i, kpts in enumerate(results.keypoints.data):
                bbox = results.boxes[i].xyxy[0].tolist() if getattr(results, "boxes", None) is not None else [0, 0, 0, 0]
                kpts_list = kpts.tolist()
                pose_detections.append({
                    "bbox": [int(x) for x in bbox],
                    "keypoints": kpts_list,
                })

        return pose_detections