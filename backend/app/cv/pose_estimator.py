import numpy as np
from ultralytics import YOLO

class PoseEstimator:
    def __init__(self, model_path: str = "yolov8n-pose.pt"):
        """Loads the specialized YOLOv8 Pose model configuration."""
        self.model = YOLO(model_path)

    def estimate_pose(self, frame: np.ndarray) -> list:
        """
        Processes a raw frame matrix and maps 17 key skeletal landmark points 
        [x, y, visibility_confidence] for every individual in view.
        """
        results = self.model(frame, verbose=False)[0]
        pose_detections = []
        
        if results.keypoints is not None and len(results.keypoints.data) > 0:
            # keypoints.data shape is (num_people, 17, 3)
            for i, kpts in enumerate(results.keypoints.data):
                bbox = results.boxes[i].xyxy[0].tolist() if results.boxes is not None else [0, 0, 0, 0]
                
                # Convert the individual tensors to native python lists
                kpts_list = kpts.tolist() 
                
                pose_detections.append({
                    "bbox": [int(x) for x in bbox],
                    "keypoints": kpts_list  # Explicitly matches our [17][3] data requirement
                })
                
        return pose_detections