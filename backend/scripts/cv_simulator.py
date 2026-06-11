"""Lightweight CV simulator that reads MP4s from data/mock_feeds and drives the agent pipeline.

This script does a low-cost per-frame heuristic to produce feature vectors
and calls the LangGraph agent pipeline (`run_agent_pipeline`) so you can
observe time-series detections without running heavy ML models.

Usage:
  f:/teamaccelerate/.venv/Scripts/python.exe backend/scripts/cv_simulator.py
"""
import sys
import os
import asyncio
import time
import glob
import cv2
import math
from typing import Tuple

# Make the backend package importable when running the script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.agent_graph import run_agent_pipeline


def _find_mock_videos(mock_dir: str):
    patterns = ["*.mp4", "*.mov", "*.mkv", "*.avi"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(mock_dir, p)))
    return sorted(files)


def _centroid_from_bbox(bbox: Tuple[int, int, int, int]) -> Tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


async def process_video(path: str, camera_id: str = "CAM_SIM", platform: str = "DemoPlatform"):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Failed to open video: {path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 10
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    print(f"Processing {os.path.basename(path)} @ {int(fps)}FPS ({width}x{height})")

    prev_centroid = None
    track_id = 1
    edge_timer = 0.0
    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                # loop video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                prev_centroid = None
                edge_timer = 0.0
                frame_idx = 0
                await asyncio.sleep(0.1)
                continue

            frame_idx += 1

            # Only sample every N frames to keep load low
            if frame_idx % max(1, int(fps // 2)) != 0:
                await asyncio.sleep(0)  # yield
                continue

            # Simulated detection bbox: center box (this is lightweight placeholder)
            bbox = [int(width * 0.4), int(height * 0.3), int(width * 0.6), int(height * 0.8)]
            centroid = _centroid_from_bbox(bbox)

            # movement speed approx: pixel displacement per second converted to m/s (rough heuristic)
            speed_px = 0.0
            if prev_centroid is not None:
                dx = centroid[0] - prev_centroid[0]
                dy = centroid[1] - prev_centroid[1]
                dist_px = math.hypot(dx, dy)
                # assume 100 px ~= 1 meter for demo purposes
                speed_mps = (dist_px / 100.0) * (fps / max(1, int(fps // 2)))
            else:
                speed_mps = 0.0

            prev_centroid = centroid

            # edge distance heuristic: distance from bottom of frame as fraction -> meters
            # assume bottom edge is platform edge
            distance_to_bottom_px = height - centroid[1]
            edge_distance_meters = max(0.0, (distance_to_bottom_px / height) * 3.0)

            # edge proximity seconds: accumulate when closer than threshold (0.5m)
            if edge_distance_meters <= 0.5:
                edge_timer += (1.0 / max(1, int(fps)))
            else:
                edge_timer = 0.0

            following_distance = float('inf')

            feature_vector = [
                float(edge_timer),  # edge_proximity
                0.0,                # loitering_time (not computed)
                0.0,                # pacing_count
                float(speed_mps),   # movement_speed
                0.0,                # direction_changes
                following_distance,
                0.0,                # crowd_interactions
            ]

            raw_cv_state = {
                "person_id": track_id,
                "camera_id": camera_id,
                "platform": platform,
                "lstm_scores": {"normal": 0.0, "suicide": 0.0, "pickpocket": 0.0, "anomaly": 0.0},
                "lstm_anomaly_score": 0.0,
                "lstm_score": 0.0,
                "edge_distance_meters": edge_distance_meters,
                "edge_proximity_seconds": edge_timer,
                "behavior_duration_seconds": frame_idx / max(1, int(fps)),
                "following_distance": following_distance,
                "pose_classification": "normal",
                "bounding_box": bbox,
                "metadata": {"source_video": os.path.basename(path)},
            }

            # Run the agent graph pipeline for this synthetic frame observation
            final_state = await run_agent_pipeline(raw_cv_state)
            # Print a concise summary for demo purposes
            alert = final_state.get("alert_payload", {})
            decision = final_state.get("decision", {})
            if alert:
                print(f"[{camera_id}] frame={frame_idx} risk={alert.get('risk_score')} type={alert.get('incident_type')}")

            # yield control so other tasks can run
            await asyncio.sleep(0)

    finally:
        cap.release()


async def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mock_dir = os.path.join(repo_root, "data", "mock_feeds")
    videos = _find_mock_videos(mock_dir)
    if not videos:
        print("No mock videos found in backend/data/mock_feeds/. Add MP4 files and re-run.")
        return

    tasks = []
    for idx, vp in enumerate(videos):
        cam_id = f"CAM_SIM_{idx+1:02d}"
        tasks.append(asyncio.create_task(process_video(vp, camera_id=cam_id, platform=f"Platform_{idx+1}")))

    print(f"Started simulator for {len(tasks)} videos. Press Ctrl-C to stop.")
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Simulator stopped by user.")
