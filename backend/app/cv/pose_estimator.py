import numpy as np
import logging
import os
from typing import Optional
from app.core.config import settings

try:
    from ultralytics import YOLO
except Exception as import_error:  # pragma: no cover - exercised by deployments without ultralytics
    YOLO = None
    YOLO_IMPORT_ERROR = import_error
else:
    YOLO_IMPORT_ERROR = None

logger = logging.getLogger("railmind")


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
        self.model_path = model_path
        self.device = device
        self.model = None
        self.is_available = False
        self.unavailable_reason = ""

        if YOLO is None:
            self.unavailable_reason = f"ultralytics is not installed or could not be imported: {YOLO_IMPORT_ERROR}"
            logger.error("YOLOv8 pose estimator unavailable: %s", self.unavailable_reason)
            return

        if not os.path.exists(model_path):
            self.unavailable_reason = (
                f"pose model weights are missing at {model_path}. "
                "Set POSE_MODEL_PATH to a valid YOLOv8 pose weights file before enabling CV processing."
            )
            logger.error("YOLOv8 pose estimator unavailable: %s", self.unavailable_reason)
            return

        try:
            # Load model and move to device if supported
            self.model = YOLO(model_path)
            try:
                # ultralytics models support .to(device)
                self.model.to(device)
            except Exception:
                # If moving to device fails, continue with default
                pass
        except Exception as err:
            self.model = None
            self.unavailable_reason = f"failed to load YOLOv8 pose model from {model_path}: {err}"
            logger.error("YOLOv8 pose estimator unavailable: %s", self.unavailable_reason)
            return

        self.is_available = True

    def estimate_pose(self, frame: np.ndarray) -> list:
        """Process a raw frame and return pose detections.

        Returns list of {"bbox": [x1,y1,x2,y2], "keypoints": [[x,y,conf], ...]}
        """
        if self.model is None:
            return []

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
