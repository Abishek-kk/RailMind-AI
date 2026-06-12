import cv2
import asyncio
import logging
import math
import time
from argparse import Namespace
import numpy as np
from app.core.config import settings
from app.core.database import SessionLocal
from app.cv.pose_estimator import PoseEstimator
from app.cv.lstm_behavior import BehaviorAnalyzer
from app.features.edge_proximity import EdgeProximityDetector
from app.features.loitering_detector import LoiteringDetector
from app.features.pacing_detector import PacingDetector
from app.features.following_detector import FollowingDetector
from app.features.movement_analyzer import MovementAnalyzer
from app.services.notification_service import NotificationService
from app.services.escalation_service import EscalationService
from app.services.incident_service import IncidentService
from app.services.alert_service import AlertService
from app.agents.agent_graph import run_agent_pipeline
from app.analytics.heatmap import update_live_heatmap
from app.core.websocket_manager import manager

try:
    from ultralytics.trackers import BYTETracker
except Exception as import_error:  # pragma: no cover - exercised by deployments without ultralytics
    BYTETracker = None
    BYTETRACK_IMPORT_ERROR = import_error
else:
    BYTETRACK_IMPORT_ERROR = None

logger = logging.getLogger("railmind")

# Alert cooldown configuration (in seconds)
EMAIL_ALERT_COOLDOWN_SECONDS = 300  # 5 minutes

class VideoProcessor:
    def __init__(self, feed_source: str, camera_id: str, platform: str):
        self.feed_source = feed_source
        self.camera_id = camera_id
        self.platform = platform
        # Use configured pose model path to ensure the correct weights are loaded
        self.pose_estimator = PoseEstimator(model_path=settings.POSE_MODEL_PATH, device=settings.POSE_DEVICE)
        
        # Initialize BYTETracker with required configuration arguments
        self.tracker = None
        if not self.pose_estimator.is_available:
            logger.error("Skipping BYTETracker initialization because YOLOv8 pose estimation is unavailable.")
        elif BYTETracker is None:
            logger.error("BYTETracker unavailable because ultralytics could not be imported: %s", BYTETRACK_IMPORT_ERROR)
        else:
            tracker_args = Namespace(
                track_high_thresh=0.5,  # Confidence threshold for first association
                track_low_thresh=0.1,   # Confidence threshold for second association
                new_track_thresh=0.5,   # Confidence threshold for starting a new track
                track_thresh=0.5,       # Backward-compatible alias used by older ByteTrack builds
                track_buffer=30,        # Maximum number of frames to buffer before dropping track
                match_thresh=0.8,       # Intersection-over-union threshold for matching
                fuse_score=True,        # Combine confidence with IoU distance during matching
                mot20=False             # Use MOT20 challenge format
            )
            try:
                self.tracker = BYTETracker(tracker_args)
            except Exception as err:
                logger.error("BYTETracker initialization failed: %s", err)
        self.cv_available = self.pose_estimator.is_available and self.tracker is not None
        self.behavior_analyzer = BehaviorAnalyzer()
        self.edge_detector = EdgeProximityDetector()
        self.loitering_detector = LoiteringDetector()
        self.pacing_detector = PacingDetector()
        self.following_detector = FollowingDetector()
        self.movement_analyzer = MovementAnalyzer()
        self.notification_service = NotificationService()
        self.escalation_service = EscalationService()

        self.db = None
        self.incident_service = None
        self.alert_service = None

        self.previous_track_ids: set[int] = set()
        self.track_entry_times: dict[int, float] = {}
        self.is_running = False
        # Cooldown tracking for email alerts: {track_id: last_alert_timestamp}
        self.email_alert_cooldown: dict[int, float] = {}
        self.last_detection_broadcast_time = 0.0
        self._tracker_api_version: str | None = None

    def _get_context_multiplier(self) -> float:
        """Resolve platform-specific context multiplier from configuration."""
        multiplier_map = settings.PLATFORM_CONTEXT_MULTIPLIERS or {}
        normalized_platform = self.platform.strip()
        if normalized_platform in multiplier_map:
            return multiplier_map[normalized_platform]
        for key, value in multiplier_map.items():
            if key.lower() in normalized_platform.lower():
                return value
        return 1.0

    async def start_processing_loop(self):
        """Asynchronously boots up and runs the camera feed frames processing thread."""
        self.is_running = True
        cap = None
        try:
            if not self.cv_available:
                logger.error(
                    "CV processing disabled for camera %s: %s",
                    self.camera_id,
                    self.pose_estimator.unavailable_reason or "BYTETracker is unavailable",
                )
                self.is_running = False
                return

            cap = cv2.VideoCapture(self.feed_source)
            if not cap.isOpened():
                logger.error(f"Critical Ingestion Failure: Unable to parse stream {self.feed_source}")
                self.is_running = False
                return

            self.db = SessionLocal()
            self.incident_service = IncidentService(self.db)
            self.alert_service = AlertService(self.db)

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
                tracked_objects = self._update_tracker(results, frame)
                active_frame_detections = []

                current_track_ids = {int(row[4]) for row in tracked_objects} if tracked_objects is not None else set()
                disappeared_tracks = self.previous_track_ids - current_track_ids
                for track_id in disappeared_tracks:
                    self.behavior_analyzer.clear_track_history(track_id)
                    self.loitering_detector.clear_track(track_id)
                    self.pacing_detector.clear_track(track_id)
                    self.track_entry_times.pop(track_id, None)
                self.previous_track_ids = current_track_ids

                frame_time = time.time()
                matched_detections = self._match_tracker_results(
                    tracked_objects,
                    pose_detections,
                    frame_dimensions=(width, height),
                )
                current_tracks = {}
                for track_id, person in matched_detections:
                    if track_id not in self.track_entry_times:
                        self.track_entry_times[track_id] = frame_time
                    bbox = person["bbox"]
                    center = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
                    person["center"] = center
                    current_tracks[track_id] = {
                        "bbox": bbox,
                        "center": center,
                    }

                update_live_heatmap(
                    self.camera_id,
                    self.platform,
                    width,
                    height,
                    [
                        {
                            "center": person["center"],
                            "bbox": person["bbox"],
                        }
                        for _, person in matched_detections
                    ],
                )

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
                        following_distance = float(max(height, width)) / settings.PIXELS_PER_METER
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

                    lstm_scores = self.behavior_analyzer.analyze_temporal_sequence(track_id, feature_vector)
                    lstm_score = max(lstm_scores.values()) if lstm_scores else 0.0
                    pose_label = self.behavior_analyzer.determine_behavior_label(
                        lstm_scores,
                        following_distance=following_distance,
                    )

                    duration_seconds = int(frame_time - self.track_entry_times.get(track_id, frame_time))
                    raw_cv_state = {
                        "person_id": track_id,
                        "camera_id": self.camera_id,
                        "platform": self.platform,
                        "lstm_anomaly_score": lstm_scores.get("anomaly", 0.0),
                        "lstm_score": lstm_score,
                        "lstm_scores": lstm_scores,
                        "edge_distance_meters": edge_distance_meters,
                        "edge_distance": edge_distance_meters,
                        "edge_proximity_seconds": edge_proximity_seconds,
                        "behavior_duration_seconds": duration_seconds,
                        "duration_seconds": duration_seconds,
                        "loitering_duration": loitering_time,
                        "following_distance": following_distance,
                        "pose_classification": pose_label,
                        "context_multiplier": self._get_context_multiplier(),
                        "bounding_box": bbox
                    }

                    # 5. Invoke LangGraph Execution Workflow
                    final_state = await run_agent_pipeline(raw_cv_state)
                    alert_payload = final_state.get("alert_payload", {})
                    execution_status = final_state.get("execution_status", [])
                    alert_info = alert_payload

                    # Persist alert and incident records when a high-risk event is generated
                    should_persist_alert = any(
                        flag in execution_status
                        for flag in [
                            "websocket_broadcast_required",
                            "email_alert_required",
                            "sms_escalation_required",
                        ]
                    )

                    alert_record = None
                    if should_persist_alert:
                        alert_record = self.alert_service.create_alert({
                            "person_id": raw_cv_state["person_id"],
                            "camera_id": raw_cv_state["camera_id"],
                            "platform": raw_cv_state["platform"],
                            "incident_type": alert_payload.get("incident_type", "Normal Activity"),
                            "risk_score": alert_payload.get("risk_score", 0.0),
                            "risk_level": alert_payload.get("risk_level", "Safe"),
                            "status": "active",
                            "bounding_box": raw_cv_state.get("bounding_box"),
                        })
                        if alert_record:
                            alert_payload["id"] = alert_record.id

                    if alert_payload.get("risk_score", 0.0) >= settings.MEDIUM_RISK_THRESHOLD:
                        incident_payload = {
                            "alert_id": alert_record.id if alert_record else None,
                            "camera_id": raw_cv_state["camera_id"],
                            "platform": raw_cv_state["platform"],
                            "incident_type": alert_payload.get("incident_type", "Normal Activity"),
                            "risk_score": alert_payload.get("risk_score", 0.0),
                            "risk_level": alert_payload.get("risk_level", "Safe"),
                            "status": "unacknowledged",
                        }
                        self.incident_service.create_incident(incident_payload)

                    if "websocket_broadcast_required" in execution_status:
                        await manager.broadcast_detection(alert_payload)
                    if "email_alert_required" in execution_status:
                        # Check cooldown before sending email alert
                        alert_time = time.time()
                        last_alert_time = self.email_alert_cooldown.get(track_id, 0)
                        time_since_last_alert = alert_time - last_alert_time
                        
                        if time_since_last_alert >= EMAIL_ALERT_COOLDOWN_SECONDS:
                            # Cooldown expired or first alert for this track - send email
                            await asyncio.to_thread(self.notification_service.send_email_alert, alert_payload)
                            self.email_alert_cooldown[track_id] = alert_time
                            logger.info(f"Email alert sent for track {track_id}")
                        else:
                            # Cooldown still active - skip email but log for debugging
                            remaining_cooldown = EMAIL_ALERT_COOLDOWN_SECONDS - time_since_last_alert
                            logger.debug(
                                f"Email alert skipped for track {track_id}: "
                                f"cooldown active for {remaining_cooldown:.1f}s more"
                            )
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
                detection_broadcast_interval = settings.WEBSOCKET_DETECTION_BROADCAST_INTERVAL_SECONDS
                should_broadcast_detections = (
                    active_frame_detections
                    and frame_time - self.last_detection_broadcast_time >= detection_broadcast_interval
                )
                if should_broadcast_detections:
                    live_broadcast_packet = {
                        "camera_id": self.camera_id,
                        "platform": self.platform,
                        "dimensions": {"width": width, "height": height},
                        "timestamp": frame_count,
                        "detections": active_frame_detections
                    }
                    await manager.broadcast_detection(live_broadcast_packet)
                    self.last_detection_broadcast_time = frame_time

                # Control frequency to match expected video runtime speeds (~30 frames/sec execution)
                await asyncio.sleep(0.033)
        finally:
            if cap is not None:
                cap.release()
            if self.db is not None:
                self.db.close()
                self.db = None
                self.incident_service = None
                self.alert_service = None

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

    def _update_tracker(self, results, frame: np.ndarray) -> np.ndarray:
        boxes = getattr(results, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return np.empty((0, 5), dtype=float)

        detections = self._boxes_to_tracker_detections(boxes)
        img_size = frame.shape[:2]

        if self._tracker_api_version == "new":
            return self.tracker.update(boxes, frame)
        if self._tracker_api_version == "legacy":
            return self.tracker.update(detections, img_size, img_size)

        try:
            tracked = self.tracker.update(boxes, frame)
            self._tracker_api_version = "new"
            return tracked
        except TypeError:
            tracked = self.tracker.update(detections, img_size, img_size)
            self._tracker_api_version = "legacy"
            return tracked

    def _boxes_to_tracker_detections(self, boxes) -> np.ndarray:
        xyxy = self._to_numpy(boxes.xyxy)
        conf = self._to_numpy(boxes.conf).reshape(-1, 1)
        cls = self._to_numpy(boxes.cls).reshape(-1, 1)
        return np.concatenate([xyxy, conf, cls], axis=1)

    def _to_numpy(self, value) -> np.ndarray:
        if hasattr(value, "detach"):
            value = value.detach()
        if hasattr(value, "cpu"):
            value = value.cpu()
        if hasattr(value, "numpy"):
            return value.numpy()
        return np.asarray(value)

    def _match_tracker_results(
        self,
        tracked_objects: np.ndarray,
        pose_detections: list[dict],
        frame_dimensions: tuple[int, int] | None = None,
    ) -> list[tuple[int, dict]]:
        if tracked_objects is None or len(pose_detections) == 0:
            return []

        width, height = frame_dimensions if frame_dimensions is not None else (0, 0)
        real_world_threshold_meters = 0.5
        pixel_threshold = real_world_threshold_meters * settings.PIXELS_PER_METER

        # Ensure threshold scales with resolution when PIXELS_PER_METER is not available.
        if pixel_threshold <= 0 and width and height:
            pixel_threshold = min(width, height) * 0.05

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

            if best_idx is not None and best_distance < pixel_threshold:
                matches.append((track_id, pose_detections[best_idx]))
                unmatched.remove(best_idx)

        return matches

    def stop_processing_loop(self):
        """Gently requests the loop execution thread to break and exit cleanly."""
        self.is_running = False
