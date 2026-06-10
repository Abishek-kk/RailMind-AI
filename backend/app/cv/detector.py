import cv2
import numpy as np
from ultralytics import YOLO

class PersonDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        """Initializes standard YOLOv8 Object Detection weight boundaries."""
        self.model = YOLO(model_path)

    def detect(self, frame: np.ndarray) -> list:
        """
        Parses an incoming image frame matrix and filters out bounding box 
        coordinates strictly matching human subject detections (Class 0).
        """
        results = self.model(frame, verbose=False)[0]
        detections = []
        
        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            # Filter: Class 0 is 'person' in the COCO dataset configuration
            if cls == 0 and conf > 0.40:
                xyxy = box.xyxy[0].tolist()
                detections.append({
                    "bbox": [int(x) for x in xyxy],
                    "confidence": round(conf, 2)
                })
                
        return detections