"""Extract image frames from a video file.

Usage:
  python backend/scripts/extract_frames.py --video backend/data/raw_video_data/raw_test_video_1.mp4
"""
import argparse
from pathlib import Path

import cv2


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIDEO_PATH = BACKEND_ROOT / "data" / "raw_video_data" / "raw_test_video_1.mp4"
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "extracted_frames_data"


def extract_frames(video_path: str | Path, output_dir: str | Path, image_format: str = "jpg") -> int:
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise OSError(f"Could not open video at path: {video_path}")

    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            filename = output_dir / f"frame_{frame_count:06d}.{image_format}"
            cv2.imwrite(str(filename), frame)
            frame_count += 1
    finally:
        cap.release()

    print(f"Extracted {frame_count} frames to '{output_dir}'")
    return frame_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract frames from a video file.")
    parser.add_argument("--video", default=str(DEFAULT_VIDEO_PATH), help="Input video path.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for extracted frames.")
    parser.add_argument("--format", default="jpg", choices=["jpg", "jpeg", "png"], help="Output image format.")
    args = parser.parse_args()

    extract_frames(args.video, args.output_dir, args.format)


if __name__ == "__main__":
    main()
