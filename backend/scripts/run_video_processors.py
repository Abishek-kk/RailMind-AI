"""Start VideoProcessor instances for all videos in backend/data/mock_feeds.

This launches the real CV pipeline using the project's `VideoProcessor` class,
which will perform YOLOv8-Pose inference, ByteTrack tracking, feature extraction,
and invoke the LangGraph agent pipeline per-frame. WARNING: this runs actual
model inference and may be CPU/GPU intensive.

Usage:
  f:/teamaccelerate/.venv/Scripts/python.exe backend/scripts/run_video_processors.py
"""
import sys
import os
import glob
import asyncio
import argparse

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.cv.video_processor import VideoProcessor
from app.core.config import settings


def find_videos(mock_dir: str):
    patterns = ["*.mp4", "*.mov", "*.mkv", "*.avi"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(mock_dir, p)))
    return sorted(files)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=str, default=None, help="Device for pose inference, e.g. 'cpu' or 'cuda:0'")
    args = parser.parse_args()

    if args.device:
        # Override runtime device selection
        settings.POSE_DEVICE = args.device

    video_dir = settings.MOCK_FEED_DIR
    videos = find_videos(video_dir)
    if not videos:
        print(f"No mock videos found in {video_dir}. Add sample MP4 files and re-run.")
        return

    tasks = []
    for idx, v in enumerate(videos):
        cam_id = f"CAM_{idx+1:03d}"
        vp = VideoProcessor(feed_source=v, camera_id=cam_id, platform=f"Platform_{idx+1}")
        tasks.append(asyncio.create_task(vp.start_processing_loop()))

    print(f"Started {len(tasks)} VideoProcessor tasks. Press Ctrl-C to stop.")
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped video processors.")
