import asyncio
import logging
from typing import Dict

from app.cv.video_processor import VideoProcessor

# Simple manager to track running VideoProcessor tasks started via uploads
_processors: Dict[str, Dict] = {}
logger = logging.getLogger("railmind")


def start_processor(file_path: str, camera_id: str, platform: str):
    """Start a VideoProcessor for the given file if not already running.

    Returns the task object.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError as err:
        raise RuntimeError(
            "start_processor must be called from a running asyncio event loop. "
            "Use it from FastAPI async handlers, lifespan startup, or an async runner."
        ) from err

    if camera_id in _processors:
        task = _processors[camera_id]["task"]
        if task.done():
            del _processors[camera_id]
        elif task.get_loop() is not loop:
            raise RuntimeError(
                f"Processor for camera {camera_id} is already running on a different asyncio event loop."
            )
        else:
            return task

    vp = VideoProcessor(feed_source=file_path, camera_id=camera_id, platform=platform)
    task = loop.create_task(vp.start_processing_loop())
    task.add_done_callback(lambda completed_task: _handle_processor_done(camera_id, completed_task))
    _processors[camera_id] = {"processor": vp, "task": task, "path": file_path}
    return task


def _handle_processor_done(camera_id: str, task: asyncio.Task):
    """Log processor task failures and clean the registry when a task exits."""
    info = _processors.get(camera_id)
    if info and info.get("task") is task:
        del _processors[camera_id]

    if task.cancelled():
        logger.info("VideoProcessor task cancelled for camera %s", camera_id)
        return

    error = task.exception()
    if error is not None:
        logger.error(
            "VideoProcessor task failed for camera %s",
            camera_id,
            exc_info=(type(error), error, error.__traceback__),
        )
    else:
        logger.info("VideoProcessor task stopped for camera %s", camera_id)


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
