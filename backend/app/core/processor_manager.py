import asyncio
import os
from typing import Dict
from app.cv.video_processor import VideoProcessor
from app.core.config import settings

# Simple manager to track running VideoProcessor tasks started via uploads
_processors: Dict[str, Dict] = {}


def start_processor(file_path: str, camera_id: str, platform: str):
    """Start a VideoProcessor for the given file if not already running.

    Returns the task object.
    """
    if camera_id in _processors:
        return _processors[camera_id]["task"]

    vp = VideoProcessor(feed_source=file_path, camera_id=camera_id, platform=platform)
    loop = asyncio.get_event_loop()
    task = loop.create_task(vp.start_processing_loop())
    _processors[camera_id] = {"processor": vp, "task": task, "path": file_path}
    return task


def stop_processor(camera_id: str):
    info = _processors.get(camera_id)
    if not info:
        return False
    proc: VideoProcessor = info["processor"]
    proc.stop_processing_loop()
    # Cancel the asyncio task if still running
    task = info.get("task")
    if task and not task.done():
        task.cancel()
    del _processors[camera_id]
    return True


def list_processors():
    return {k: {"path": v["path"], "running": not v["task"].done()} for k, v in _processors.items()}
