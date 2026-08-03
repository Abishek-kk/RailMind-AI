"""Run YOLOv8 pose tracking on extracted frame images.

Usage:
  python backend/scripts/person_pose_detection_script.py --input-dir backend/data/extracted_frames_data
"""
import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = BACKEND_ROOT / "data" / "extracted_frames_data"
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "pose_detected_images"
DEFAULT_MODEL_PATH = BACKEND_ROOT / "yolov8n-pose.pt"
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png")
COCO_KEYPOINT_NAMES = (
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
)


def _format_keypoints(keypoints) -> str:
    named_points = []
    for name, point in zip(COCO_KEYPOINT_NAMES, keypoints):
        named_points.append(f"{name}: {point}")
    return " | ".join(named_points)


def detect_track_and_pose_in_frames(
    input_dir: str | Path,
    output_dir: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    conf_threshold: float = 0.5,
) -> int:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    model_path = Path(model_path)

    print(f"input directory: {input_dir}")
    print(f"output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not model_path.exists():
        raise FileNotFoundError(f"YOLO pose model does not exist: {model_path}")

    model = YOLO(str(model_path))
    image_files = sorted(path for path in input_dir.iterdir() if path.suffix.lower() in VALID_EXTENSIONS)

    print(f"Found {len(image_files)} frames in '{input_dir}'. Processing...")

    for idx, img_path in enumerate(image_files):
        results = model.track(
            source=str(img_path),
            classes=[0],
            conf=conf_threshold,
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False,
        )
        result = results[0]
        boxes = result.boxes
        person_count = len(boxes) if boxes is not None else 0
        track_ids = []

        if boxes is not None and boxes.id is not None:
            track_ids = boxes.id.int().cpu().tolist()

        if result.keypoints is not None and len(result.keypoints) > 0:
            keypoints_pixel = result.keypoints.xy.cpu().numpy()
            for person_index, person_kpts in enumerate(keypoints_pixel):
                track_id = track_ids[person_index] if person_index < len(track_ids) else "untracked"
                print(f"Track ID {track_id} | {_format_keypoints(person_kpts)}")

        annotated_frame = result.plot()
        cv2.putText(
            annotated_frame,
            f"People: {person_count} | IDs: {track_ids}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        save_path = output_dir / f"detected_{img_path.name}"
        cv2.imwrite(str(save_path), annotated_frame)
        if (idx + 1) % 10 == 0 or (idx + 1) == len(image_files):
            print(f"Processed {idx + 1}/{len(image_files)} frames...")

    print(f"Done! Pose-annotated images saved to: '{output_dir}'")
    return len(image_files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect and track person poses in frame images.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR), help="Directory containing extracted frames.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for annotated output frames.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH), help="YOLOv8 pose model path.")
    parser.add_argument("--conf", type=float, default=0.35, help="Detection confidence threshold.")
    args = parser.parse_args()

    detect_track_and_pose_in_frames(args.input_dir, args.output_dir, args.model, args.conf)


if __name__ == "__main__":
    main()
