import cv2
import asyncio
import logging
import math
import numpy as np
from ultralytics.trackers import BYTETracker
from app.core.config import settings
from app.cv.pose_estimator import PoseEstimator
from app.cv.lstm_behavior import BehaviorAnalyzer
from app.features.edge_proximity import EdgeProximityDetector
from app.features.loitering_detector import LoiteringDetector
from app.features.pacing_detector import PacingDetector
from app.features.following_detector import FollowingDetector
from app.features.movement_analyzer import MovementAnalyzer
from app.services.notification_service import NotificationService
from app.services.escalation_service import EscalationService
from app.agents.agent_graph import run_agent_pipeline
from app.core.websocket_manager import manager

logger = logging.getLogger("railmind")

class VideoProcessor:
    def __init__(self, feed_source: str, camera_id: str, platform: str):
        self.feed_source = feed_source
        self.camera_id = camera_id
        self.platform = platform
        self.pose_estimator = PoseEstimator()
        self.tracker = BYTETracker()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.edge_detector = EdgeProximityDetector()
        self.loitering_detector = LoiteringDetector()
        self.pacing_detector = PacingDetector()
        self.following_detector = FollowingDetector()
        self.movement_analyzer = MovementAnalyzer()
        self.notification_service = NotificationService()
        self.escalation_service = EscalationService()
        self.previous_track_ids: set[int] = set()
        self.is_running = False

    async def start_processing_loop(self):
        """Asynchronously boots up and runs the camera feed frames processing thread."""
        self.is_running = True
        cap = cv2.VideoCapture(self.feed_source)
        
        if not cap.isOpened():
            logger.error(f"Critical Ingestion Failure: Unable to parse stream {self.feed_source}")
            self.is_running = False
            return

        frame_count = 0
        logger.info(f"CV Processing Pipeline active for channel {self.camera_id} on {self.platform}")

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                # If reading a mock mp4 file, loop it seamlessly back to the start frame
                if isinstance(self.feed_source, str) and not self.feed_source.startswith("rtsp"):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    logger.warning(f"Connection stream dropped out for camera: {self.camera_id}")
                    break

            frame_count += 1
            # Skip frames strategically to optimize edge hardware performance overhead
            if frame_count % 2 != 0:
                await asyncio.sleep(0.001)
                continue

            height, width, _ = frame.shape

            # 1. Capture spatial skeletons and update tracker with YOLOv8 pose detections
            results = self.pose_estimator.model(frame, verbose=False)[0]
            pose_detections = self._extract_pose_detections(results)
            tracked_objects = self.tracker.update(results, frame)
            active_frame_detections = []

            current_track_ids = {int(row[4]) for row in tracked_objects} if tracked_objects is not None else set()
            disappeared_tracks = self.previous_track_ids - current_track_ids
            for track_id in disappeared_tracks:
                self.behavior_analyzer.clear_track_history(track_id)
            self.previous_track_ids = current_track_ids

            matched_detections = self._match_tracker_results(tracked_objects, pose_detections)
            current_tracks = {}
            for track_id, person in matched_detections:
                bbox = person["bbox"]
                center = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
                person["center"] = center
                current_tracks[track_id] = {
                    "bbox": bbox,
                    "center": center,
                }

            for track_id, person in matched_detections:
                bbox = person["bbox"]
                person_center = person["center"]

                edge_proximity_seconds = self.edge_detector.update(track_id, bbox, height)
                edge_distance_meters = self.edge_detector.get_distance_to_edge(bbox, height)
                if edge_distance_meters is None:
                    edge_distance_meters = settings.PLATFORM_EDGE_SAFETY_LIMIT_METERS * 2

                loitering_time = self.loitering_detector.detect(track_id, person, frame_count)
                pacing_count = self.pacing_detector.detect(track_id, person)
                movement_speed = self.movement_analyzer.update_track(track_id, person)
                direction_changes = self.movement_analyzer.get_direction_changes(track_id)
                following_distance = self.following_detector.get_following_distance(track_id, current_tracks)
                if following_distance == float("inf"):
                    following_distance = float(max(height, width))
                crowd_interactions = self.following_detector.get_crowd_interaction_count(track_id, current_tracks)

                feature_vector = [
                    float(edge_proximity_seconds),
                    float(loitering_time),
                    float(pacing_count),
                    float(movement_speed),
                    float(direction_changes),
                    float(following_distance),
                    float(crowd_interactions),
                ]

                lstm_anomaly_score = self.behavior_analyzer.analyze_temporal_sequence(track_id, feature_vector)

                raw_cv_state = {
                    "person_id": track_id,
                    "camera_id": self.camera_id,
                    "platform": self.platform,
                    "lstm_anomaly_score": lstm_anomaly_score,
                    "lstm_score": lstm_anomaly_score,
                    "edge_distance_meters": edge_distance_meters,
                    "edge_distance": edge_distance_meters,
                    "edge_proximity_seconds": edge_proximity_seconds,
                    "behavior_duration_seconds": int(frame_count / 30),
                    "duration_seconds": int(frame_count / 30),
                    "loitering_duration": loitering_time,
                    "following_distance": following_distance,
                    "pose_classification": "erratic" if lstm_anomaly_score > 0.65 else "normal",
                    "context_multiplier": 1.25 if "Platform 1" in self.platform else 1.0,
                    "bounding_box": bbox
                }

                # 5. Invoke LangGraph Execution Workflow
                final_state = await run_agent_pipeline(raw_cv_state)
                alert_payload = final_state.get("alert_payload", {})
                execution_status = final_state.get("execution_status", [])
                alert_info = alert_payload

                if "websocket_broadcast_required" in execution_status:
                    await manager.broadcast_detection(alert_payload)
                if "email_alert_required" in execution_status:
                    await asyncio.to_thread(self.notification_service.send_email_alert, alert_payload)
                if "sms_escalation_required" in execution_status:
                    await asyncio.to_thread(self.escalation_service.send_sms_alert, alert_payload)

                # 6. Accumulate visual metadata overlay values
                active_frame_detections.append({
                    "track_id": track_id,
                    "bbox": bbox,
                    "distance": edge_distance_meters,
                    "risk_score": alert_info.get("risk_score", 0.0),
                    "risk_level": alert_info.get("risk_level", "Safe"),
                    "incident_type": alert_info.get("incident_type", "Normal Activity")
                })

            # 7. Asynchronously broadcast frame telemetry data straight out to frontend components
            if active_frame_detections:
                live_broadcast_packet = {
                    "camera_id": self.camera_id,
                    "platform": self.platform,
                    "dimensions": {"width": width, "height": height},
                    "timestamp": frame_count,
                    "detections": active_frame_detections
                }
                await manager.broadcast_detection(live_broadcast_packet)

            # Control frequency to match expected video runtime speeds (~30 frames/sec execution)
            await asyncio.sleep(0.033)

        cap.release()

    def _extract_pose_detections(self, results) -> list[dict]:
        pose_detections = []

        if results.keypoints is None or len(results.keypoints.data) == 0:
            return pose_detections

        for i, kpts in enumerate(results.keypoints.data):
            bbox = results.boxes[i].xyxy[0].tolist() if results.boxes is not None else [0, 0, 0, 0]
            pose_detections.append({
                "bbox": [int(x) for x in bbox],
                "keypoints": kpts.tolist()
            })

        return pose_detections

    def _match_tracker_results(self, tracked_objects: np.ndarray, pose_detections: list[dict]) -> list[tuple[int, dict]]:
        if tracked_objects is None or len(pose_detections) == 0:
            return []

        matches = []
        unmatched = set(range(len(pose_detections)))

        for track in tracked_objects:
            track_id = int(track[4])
            x1, y1, x2, y2 = track[:4].tolist()
            track_center = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

            best_idx = None
            best_distance = float("inf")
            for det_idx in list(unmatched):
                bbox = pose_detections[det_idx]["bbox"]
                det_center = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
                distance = math.dist(track_center, det_center)
                if distance < best_distance:
                    best_distance = distance
                    best_idx = det_idx

            if best_idx is not None and best_distance < 80:
                matches.append((track_id, pose_detections[best_idx]))
                unmatched.remove(best_idx)

        return matches

    def stop_processing_loop(self):
        """Gently requests the loop execution thread to break and exit cleanly."""
        self.is_running = False