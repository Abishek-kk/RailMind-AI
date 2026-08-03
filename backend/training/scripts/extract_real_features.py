"""Extract transformer training sequences from real video folders.

The script maps the local raw-video dataset folders into the behavior folders
expected by prepare_dataset.py, then writes one .npy sequence per video.
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.cv.pose_estimator import PoseEstimator
from app.features.feature_extractor import extract_pose_features


DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets"
TARGET_SEQUENCE_LENGTH = 30
FRAME_STRIDE = 10
VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm"}

BEHAVIOR_FOLDERS = {
    "normal_sequences": "normal",
    "pickpocket_sequences": "pickpocketing",
    "suicide_sequences": "suicide_risk",
}


def _sequence_from_video(video_path: Path, pose_estimator: PoseEstimator) -> np.ndarray | None:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        print(f"  failed to open video: {video_path.name}")
        return None

    sequence: list[list[float]] = []
    frame_index = 0

    while len(sequence) < TARGET_SEQUENCE_LENGTH:
        ok, frame = capture.read()
        if not ok:
            break

        if frame_index % FRAME_STRIDE == 0:
            detections = pose_estimator.estimate_pose(frame)
            if detections:
                sequence.append(extract_pose_features(detections[0]["keypoints"]))

        frame_index += 1

    capture.release()

    if not sequence:
        print(f"  no pose sequence extracted: {video_path.name}")
        return None

    feature_count = len(sequence[0])
    if len(sequence) < TARGET_SEQUENCE_LENGTH:
        padding = [[0.0] * feature_count for _ in range(TARGET_SEQUENCE_LENGTH - len(sequence))]
        sequence = padding + sequence

    return np.asarray(sequence[-TARGET_SEQUENCE_LENGTH:], dtype=np.float32)


def extract_real_features() -> None:
    pose_estimator = PoseEstimator()
    if not pose_estimator.is_available:
        raise RuntimeError(pose_estimator.unavailable_reason)

    total_saved = 0
    for source_dir in sorted(path for path in DATASET_DIR.iterdir() if path.is_dir()):
        target_name = BEHAVIOR_FOLDERS.get(source_dir.name)
        if target_name is None:
            print(f"Skipping unrecognised folder: {source_dir.name}")
            continue

        videos = sorted(path for path in source_dir.iterdir() if path.suffix.lower() in VIDEO_EXTENSIONS)
        print(f"Found folder {source_dir.name} -> {target_name}: {len(videos)} videos", flush=True)

        target_dir = DATASET_DIR / target_name
        target_dir.mkdir(parents=True, exist_ok=True)

        saved_for_folder = 0
        for index, video_path in enumerate(videos, start=1):
            output_path = target_dir / f"{video_path.stem}_{index:04d}.npy"
            if output_path.exists():
                print(f"  [{index}/{len(videos)}] skipping existing {output_path.name}", flush=True)
                continue

            print(f"  [{index}/{len(videos)}] extracting {video_path.name}", flush=True)
            sequence = _sequence_from_video(video_path, pose_estimator)
            if sequence is None:
                continue

            np.save(output_path, sequence)
            saved_for_folder += 1

        total_saved += saved_for_folder
        print(f"  saved {saved_for_folder} new sequences to {target_dir}", flush=True)

    if total_saved == 0:
        raise RuntimeError("No real video features were extracted")

    print(f"Saved {total_saved} total new real-video feature sequences", flush=True)


if __name__ == "__main__":
    extract_real_features()
