import os
import sys
import json
import csv
import math
import time
import hashlib
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

# =====================================================================
# CONFIG -- tune these thresholds for your camera / use case
# =====================================================================

class config:
    INTRUSION_CONFIRM_FRAMES = 3          # consecutive frames in track zone before alert
    LOITER_DWELL_SECONDS = 45             # time in platform zone before "loitering"
    LOITER_MOVEMENT_RADIUS_PX = 80        # max movement radius to still count as "loitering"
    DIRECTION_REVERSAL_ANGLE_DEG = 120    # heading change considered a "reversal"
    MIN_SPEED_FOR_HEADING_PX = 5          # ignore heading calc below this displacement
    DENSITY_HIGH_THRESHOLD = 15           # people count considered "high density"
    ASSUMED_FPS = 25                      # fallback if video FPS can't be read

WORK_ROOT = "pipeline_data"

# =====================================================================
# STEP 1: frame extraction
# =====================================================================

def extract_frames(video_path, output_dir, image_format="jpg"):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video in the path : {video_path}")
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        filename = os.path.join(output_dir, f"frame_{frame_count:06d}.{image_format}")
        cv2.imwrite(filename, frame)
        frame_count += 1
    cap.release()
    print(f"Extracted {frame_count} frames to '{output_dir}'")

#checks if the frames from the video are already extracted or not
def _ensure_frames_extracted(video_path, frames_dir):
    if os.path.isdir(frames_dir) and any(f.endswith(".jpg") for f in os.listdir(frames_dir)):
        print(f"[pipeline] Frames already extracted at '{frames_dir}', skipping extraction.")
        return
    print(f"[pipeline] Extracting frames for '{video_path}'...")
    extract_frames(video_path, frames_dir)

# =====================================================================
# STEP 2: zone calibration (interactive, once per video, cached)
# =====================================================================

def _get_config_zones(img_path):
    """
    Opens an interactive window on the given frame. Click points to
    trace a polygon, press 'n' to save it and start a new one, press
    'q' when done. Returns {"poly_coords": [polygon1_points, polygon2_points, ...]}.
    Convention used by this pipeline: polygon 1 = track/danger zone,
    polygon 2 = platform zone.
    """
    polygons = []
    current_polygon = []

    def click_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            current_polygon.append((x, y))
            print(f"Point added: ({x}, {y})")

    img = cv2.imread(img_path)
    if img is None:
        raise IOError(f"Could not read image: {img_path}")

    clone = img.copy()
    window_name = "Calibrate Zones (click points, 'n'=next polygon, 'q'=done)"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, click_event)

    while True:
        display = clone.copy()
        for poly in polygons:
            for i in range(len(poly)):
                cv2.circle(display, poly[i], 4, (0, 255, 0), -1)
                if i > 0:
                    cv2.line(display, poly[i - 1], poly[i], (0, 255, 0), 2)
        for i in range(len(current_polygon)):
            cv2.circle(display, current_polygon[i], 4, (0, 0, 255), -1)
            if i > 0:
                cv2.line(display, current_polygon[i - 1], current_polygon[i], (0, 0, 255), 2)

        cv2.imshow(window_name, display)
        key = cv2.waitKey(20) & 0xFF

        if key == ord("n"):
            if current_polygon:
                polygons.append(current_polygon.copy())
                current_polygon.clear()
                print("Polygon saved. Starting new polygon.")
        elif key == ord("q"):
            if current_polygon:
                polygons.append(current_polygon.copy())
            break

    cv2.destroyAllWindows()
    return {"poly_coords": list(polygons)}

def _ensure_zones_calibrated(frames_dir, zones_path):
    if os.path.exists(zones_path):
        with open(zones_path, "r") as f:
            zones = json.load(f)
        print(f"[pipeline] Using cached zone calibration from '{zones_path}'.")
        return zones

    frame_files = sorted(f for f in os.listdir(frames_dir) if f.lower().endswith(".jpg"))
    if not frame_files:
        raise RuntimeError(f"No frames found in '{frames_dir}' to calibrate zones on.")

    first_frame_path = os.path.join(frames_dir, frame_files[0])
    print(f"[pipeline] No calibration found for this video. Launching zone calibration "
          f"on first frame: '{first_frame_path}'")
    print("[pipeline] Click the TRACK (danger) zone polygon first, press 'n', "
          "then click the PLATFORM zone polygon, then press 'q'.")

    data = _get_config_zones(first_frame_path)
    poly_coords = data["poly_coords"]

    if len(poly_coords) < 2:
        raise RuntimeError(
            "Calibration requires 2 polygons (track zone, then platform zone). "
            f"Only {len(poly_coords)} were drawn."
        )

    zones = {"track_zone": poly_coords[0], "platform_zone": poly_coords[1]}

    os.makedirs(os.path.dirname(zones_path), exist_ok=True)
    with open(zones_path, "w") as f:
        json.dump(zones, f, indent=2)
    print(f"[pipeline] Calibration saved to '{zones_path}'. Future runs on this video "
          f"will reuse it automatically.")

    return zones

# =====================================================================
# STEP 3: behavior analytics
# =====================================================================
# NOTE: every signal here is a literal description of position/movement
# ("in track zone for N frames", "stationary for N seconds") -- not a
# judgment about a person's intent or mental state. Treat the output as
# input for a human reviewer / alert queue, not an automated verdict.

from shapely.geometry import Point, Polygon

@dataclass
class TrackState:
    track_id: int
    positions: deque = field(default_factory=lambda: deque(maxlen=300))
    first_seen_frame: Optional[int] = None
    last_seen_frame: Optional[int] = None
    frames_in_track_zone: int = 0
    consecutive_frames_in_track_zone: int = 0
    frames_in_platform_zone: int = 0
    direction_reversals: int = 0
    last_heading: Optional[float] = None
    intrusion_alert_fired: bool = False
    loiter_alert_fired: bool = False
    currently_in_track_zone: bool = False


class BehaviorAnalyzer:
    def __init__(self, track_zone_polygon, platform_zone_polygon, fps=config.ASSUMED_FPS):
        self.track_zone = Polygon(track_zone_polygon)
        self.platform_zone = Polygon(platform_zone_polygon)
        self.fps = fps
        self.tracks: dict[int, TrackState] = {}
        self.events = []

    def process_frame(self, frame_idx, people):
        """
        people: list of dicts per detected person this frame:
            {"track_id": int, "ankle_l": (x,y), "ankle_r": (x,y), "confidence": float}
        """
        for person in people:
            tid = person["track_id"]
            if tid is None:
                continue

            state = self.tracks.setdefault(tid, TrackState(track_id=tid))
            if state.first_seen_frame is None:
                state.first_seen_frame = frame_idx
            state.last_seen_frame = frame_idx

            ax = (person["ankle_l"][0] + person["ankle_r"][0]) / 2
            ay = (person["ankle_l"][1] + person["ankle_r"][1]) / 2
            state.positions.append((frame_idx, ax, ay))

            self._check_track_zone(state, ax, ay, person["confidence"])
            self._check_platform_zone_and_dwell(state, ax, ay)
            self._check_direction_reversal(state)

        self._log_density(frame_idx, people)
        return self.events

    def get_track_summary(self, track_id):
        state = self.tracks.get(track_id)
        if not state:
            return None
        duration_s = 0
        if state.first_seen_frame is not None and state.last_seen_frame is not None:
            duration_s = (state.last_seen_frame - state.first_seen_frame) / self.fps
        return {
            "track_id": track_id,
            "duration_tracked_s": round(duration_s, 1),
            "frames_in_track_zone": state.frames_in_track_zone,
            "frames_in_platform_zone": state.frames_in_platform_zone,
            "direction_reversals": state.direction_reversals,
            "currently_in_track_zone": state.currently_in_track_zone,
            "ever_entered_track_zone": state.frames_in_track_zone > 0,
            "loitering_detected": state.loiter_alert_fired,
        }

    def _check_track_zone(self, state, x, y, confidence):
        in_zone = self.track_zone.contains(Point(x, y))
        state.currently_in_track_zone = in_zone

        if in_zone:
            state.frames_in_track_zone += 1
            state.consecutive_frames_in_track_zone += 1
        else:
            state.consecutive_frames_in_track_zone = 0
            state.intrusion_alert_fired = False

        if (state.consecutive_frames_in_track_zone >= config.INTRUSION_CONFIRM_FRAMES
                and not state.intrusion_alert_fired):
            state.intrusion_alert_fired = True
            self._log_event(
                "TRACK_ZONE_INTRUSION", state.track_id, confidence,
                {"consecutive_frames": state.consecutive_frames_in_track_zone,
                 "position": (round(x), round(y))},
            )

    def _check_platform_zone_and_dwell(self, state, x, y):
        if not self.platform_zone.contains(Point(x, y)):
            return
        state.frames_in_platform_zone += 1

        dwell_s = state.frames_in_platform_zone / self.fps
        if dwell_s < config.LOITER_DWELL_SECONDS or state.loiter_alert_fired:
            return

        recent = list(state.positions)[-int(config.LOITER_DWELL_SECONDS * self.fps):]
        if len(recent) < 2:
            return
        xs = [p[1] for p in recent]
        ys = [p[2] for p in recent]
        spread = math.hypot(max(xs) - min(xs), max(ys) - min(ys))

        if spread <= config.LOITER_MOVEMENT_RADIUS_PX:
            state.loiter_alert_fired = True
            self._log_event(
                "LOITERING", state.track_id, None,
                {"dwell_seconds": round(dwell_s, 1), "movement_radius_px": round(spread, 1)},
            )

    def _check_direction_reversal(self, state):
        if len(state.positions) < 2:
            return
        (_, x1, y1) = state.positions[-2]
        (_, x2, y2) = state.positions[-1]
        dx, dy = x2 - x1, y2 - y1
        speed = math.hypot(dx, dy)
        if speed < config.MIN_SPEED_FOR_HEADING_PX:
            return

        heading = math.degrees(math.atan2(dy, dx))
        if state.last_heading is not None:
            diff = abs((heading - state.last_heading + 180) % 360 - 180)
            if diff >= config.DIRECTION_REVERSAL_ANGLE_DEG:
                state.direction_reversals += 1
                self._log_event(
                    "DIRECTION_REVERSAL", state.track_id, None,
                    {"angle_change_deg": round(diff, 1)},
                )
        state.last_heading = heading

    def _log_density(self, frame_idx, people):
        count = len(people)
        if count >= config.DENSITY_HIGH_THRESHOLD:
            self._log_event("HIGH_DENSITY", None, None,
                             {"person_count": count, "frame_idx": frame_idx})

    def _log_event(self, event_type, track_id, confidence, extra=None):
        self.events.append({
            "timestamp": time.time(),
            "event_type": event_type,
            "track_id": track_id,
            "confidence": confidence,
            **(extra or {}),
        })


# =====================================================================
# STEP 4: orchestrator
# =====================================================================

def _video_id(video_path):
    stat = os.stat(video_path)
    key = f"{os.path.abspath(video_path)}::{stat.st_size}::{stat.st_mtime}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]

def _video_paths(video_path):
    vid = _video_id(video_path)
    base = os.path.join(WORK_ROOT, vid)
    return {
        "video_id": vid,
        "base": base,
        "frames_dir": os.path.join(base, "frames"),
        "annotated_dir": os.path.join(base, "annotated"),
        "zones_path": os.path.join(base, "zones.json"),
        "events_csv_path": os.path.join(base, "events_log.csv"),
    }


def _draw_zones(frame, track_zone_polygon, platform_zone_polygon):
    track_pts = np.array(track_zone_polygon, dtype=np.int32)
    platform_pts = np.array(platform_zone_polygon, dtype=np.int32)
    overlay = frame.copy()
    cv2.fillPoly(overlay, [track_pts], (0, 0, 255))
    frame = cv2.addWeighted(overlay, 0.15, frame, 0.85, 0)
    cv2.polylines(frame, [track_pts], isClosed=True, color=(0, 0, 255), thickness=2)
    cv2.polylines(frame, [platform_pts], isClosed=True, color=(255, 200, 0), thickness=1)
    return frame


def _get_video_fps(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    if not fps or fps <= 1:
        return config.ASSUMED_FPS
    return int(round(fps))


def _run_pose_and_analytics(frames_dir, annotated_dir, zones, fps, conf_threshold=0.35,
                             save_annotated_frames=True):
    from ultralytics import YOLO

    os.makedirs(annotated_dir, exist_ok=True)
    model = YOLO("yolov8n-pose.pt")
    analyzer = BehaviorAnalyzer(zones["track_zone"], zones["platform_zone"], fps=fps)

    image_files = sorted(f for f in os.listdir(frames_dir) if f.lower().endswith(".jpg"))
    print(f"[pipeline] Running pose detection + behavior analytics on {len(image_files)} frames...")

    for idx, img_name in enumerate(image_files):
        img_path = os.path.join(frames_dir, img_name)
        results = model.track(source=img_path, classes=[0], conf=conf_threshold,
                               tracker="bytetrack.yaml", persist=True, verbose=False)
        result = results[0]
        boxes = result.boxes

        track_ids = boxes.id.int().cpu().tolist() if boxes.id is not None else []
        confidences = boxes.conf.cpu().tolist() if boxes.conf is not None else []

        people_for_analyzer = []
        if result.keypoints is not None and len(result.keypoints) > 0:
            keypoints_pixel = result.keypoints.xy.cpu().numpy()
            for i, tid in enumerate(track_ids):
                person_kpts = keypoints_pixel[i]
                left_ankle = tuple(person_kpts[15])
                right_ankle = tuple(person_kpts[16])
                if left_ankle == (0.0, 0.0) and right_ankle == (0.0, 0.0):
                    continue
                people_for_analyzer.append({
                    "track_id": tid, "ankle_l": left_ankle, "ankle_r": right_ankle,
                    "confidence": confidences[i] if i < len(confidences) else None,
                })

        analyzer.process_frame(idx, people_for_analyzer)

        if save_annotated_frames:
            annotated_frame = result.plot()
            annotated_frame = _draw_zones(annotated_frame, zones["track_zone"], zones["platform_zone"])
            cv2.putText(annotated_frame, f"People: {len(track_ids)} | IDs: {track_ids}",
                        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imwrite(os.path.join(annotated_dir, f"safety_{img_name}"), annotated_frame)

        if (idx + 1) % 25 == 0 or (idx + 1) == len(image_files):
            print(f"[pipeline] Processed {idx + 1}/{len(image_files)} frames "
                  f"({len(analyzer.events)} events so far)")

    return analyzer


def _write_events_csv(events, path):
    if not events:
        return
    fieldnames = sorted({key for event in events for key in event.keys()})
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow(event)


def _label_activity(summary):
    if summary["currently_in_track_zone"]:
        return "IN_DANGER_ZONE"
    if summary["ever_entered_track_zone"]:
        return "PREVIOUSLY_IN_DANGER_ZONE"
    if summary["loitering_detected"]:
        return "LOITERING_ON_PLATFORM"
    if summary["direction_reversals"] >= 3:
        return "ERRATIC_MOVEMENT"
    return "NORMAL"


def _build_final_result(analyzer):
    result = {}
    for track_id in analyzer.tracks:
        summary = analyzer.get_track_summary(track_id)
        summary["activity"] = _label_activity(summary)
        summary["in_danger_zone"] = summary["currently_in_track_zone"]
        result[track_id] = summary
    return result


def process_video(video_path, conf_threshold=0.35, save_annotated_frames=True):
    """
    Runs the full pipeline for one video and returns:
        { track_id: {activity, in_danger_zone, duration_tracked_s, ...}, ... }
    Safe to call repeatedly on the same video -- extraction and
    calibration are both skipped automatically if already done.
    """
    paths = _video_paths(video_path)
    os.makedirs(paths["base"], exist_ok=True)

    _ensure_frames_extracted(video_path, paths["frames_dir"])
    zones = _ensure_zones_calibrated(paths["frames_dir"], paths["zones_path"])
    fps = _get_video_fps(video_path)

    analyzer = _run_pose_and_analytics(
        frames_dir=paths["frames_dir"], annotated_dir=paths["annotated_dir"],
        zones=zones, fps=fps, conf_threshold=conf_threshold,
        save_annotated_frames=save_annotated_frames,
    )

    _write_events_csv(analyzer.events, paths["events_csv_path"])

    final_result = _build_final_result(analyzer)
    print(f"[pipeline] Done. {len(final_result)} tracked people. "
          f"Events log: '{paths['events_csv_path']}'. "
          f"Annotated frames: '{paths['annotated_dir']}'.")
    return final_result


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    VIDEO_PATH = "raw_test_video_1.mp4"

    video_path = VIDEO_PATH

    if not os.path.exists(video_path):
        print(f"Video not found: '{video_path}'")
        print("Usage: python railway_safety_pipeline.py path/to/video.mp4")
        sys.exit(1)

    result = process_video(video_path)
    print("\n--- FINAL RESULT ---")
    print(json.dumps(result, indent=2, default=str))