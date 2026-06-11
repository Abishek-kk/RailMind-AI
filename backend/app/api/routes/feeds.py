import asyncio
import logging
import re
from typing import List, Optional
import os
from fastapi import UploadFile, File
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedRead
from app.cv.video_processor import VideoProcessor
from app.core.config import settings

logger = logging.getLogger("railmind.feeds")
router = APIRouter()

# Global registry of active VideoProcessor instances
# Key: feed_id, Value: VideoProcessor instance
active_processors = {}


def derive_platform_from_feed_id(feed_id: str) -> str:
    """Derive a platform label from common camera ID formats without assuming one shape."""
    match = re.search(r"(?:^|[_-])P(?:LATFORM)?\s*0*(\d+)(?:$|[_-])", feed_id, re.IGNORECASE)
    if match:
        return f"Platform {int(match.group(1))}"

    numeric_tokens = re.findall(r"\d+", feed_id)
    if len(numeric_tokens) == 1:
        platform_number = int(numeric_tokens[0])
        logger.info(
            "Derived platform %s from single numeric token in feed id '%s'.",
            platform_number,
            feed_id,
        )
        return f"Platform {platform_number}"

    logger.warning(
        "Unable to derive platform from feed id '%s'; using 'Unknown Platform'.",
        feed_id,
    )
    return "Unknown Platform"


@router.get("", response_model=List[FeedRead])
async def list_feeds(db: Session = Depends(get_db)):
    """List all connected station CCTV streams alongside operational health checks."""
    feeds = db.query(Feed).all()
    return feeds


@router.post("", response_model=FeedRead, status_code=status.HTTP_201_CREATED)
async def register_feed(feed: FeedCreate, db: Session = Depends(get_db)):
    """Register a new active IP Camera RTSP protocol stream network node into RailMind."""
    # Check if feed already exists
    existing = db.query(Feed).filter(Feed.id == feed.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feed with id '{feed.id}' already exists"
        )
    
    # Create new feed record
    db_feed = Feed(
        id=feed.id,
        name=feed.name,
        status="active",
        fps=feed.fps or 30.0
    )
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    
    platform = derive_platform_from_feed_id(feed.id)

    # Start VideoProcessor as background task
    try:
        processor = VideoProcessor(feed_source=feed.source_url, camera_id=feed.id, platform=platform)
        task = asyncio.create_task(processor.start_processing_loop())
        active_processors[feed.id] = {"processor": processor, "task": task}
        logger.info("Started VideoProcessor for feed %s on %s", feed.id, platform)
    except Exception as e:
        logger.error(f"Failed to start VideoProcessor for feed {feed.id}: {e}")
        # Don't fail the entire feed registration if processor startup fails
    
    return db_feed


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...), feed_id: Optional[str] = None, name: Optional[str] = None, db: Session = Depends(get_db)):
    """Upload a video file and start processing it as a new feed.

    The uploaded file is saved to `settings.MOCK_FEED_DIR` and a VideoProcessor
    is started in the background to process the file.
    """
    # Ensure storage directory exists
    storage_dir = settings.MOCK_FEED_DIR
    os.makedirs(storage_dir, exist_ok=True)

    # Derive filename and feed id
    original_name = os.path.basename(file.filename)
    if feed_id is None:
        base_id = os.path.splitext(original_name)[0]
        # Ensure unique feed id by appending a numeric suffix if necessary
        candidate = base_id
        suffix = 1
        while db.query(Feed).filter(Feed.id == candidate).first():
            candidate = f"{base_id}_{suffix}"
            suffix += 1
        feed_id = candidate
    if name is None:
        name = original_name

    dest_path = os.path.join(storage_dir, original_name)
    # Save uploaded file
    with open(dest_path, "wb") as out_f:
        content = await file.read()
        out_f.write(content)

    # Create DB record
    db_feed = Feed(id=feed_id, name=name, status="active", fps=30.0)
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)

    platform = derive_platform_from_feed_id(feed_id)

    # Start VideoProcessor
    try:
        processor = VideoProcessor(feed_source=dest_path, camera_id=feed_id, platform=platform)
        task = asyncio.create_task(processor.start_processing_loop())
        active_processors[feed_id] = {"processor": processor, "task": task}
        logger.info("Started VideoProcessor for uploaded feed %s", feed_id)
    except Exception as e:
        logger.error(f"Failed to start VideoProcessor for uploaded feed {feed_id}: {e}")

    return {"feed_id": feed_id, "name": name, "path": dest_path}


@router.get("/{id}/stream")
async def get_live_stream_metadata(id: str, db: Session = Depends(get_db)):
    """Returns endpoint stream pipeline specifications for client rendering loops."""
    feed = db.query(Feed).filter(Feed.id == id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with id '{id}' not found"
        )
    
    return {
        "feed_id": id,
        "stream_protocol": "HLS/WebRTC",
        "endpoint_url": f"/api/v1/feeds/{id}/live.m3u8",
        "inference_overlay": True,
        "status": feed.status
    }


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_feed(id: str, db: Session = Depends(get_db)):
    """Safely stop parsing frames and tear down ingestion threads for a specified camera."""
    feed = db.query(Feed).filter(Feed.id == id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with id '{id}' not found"
        )
    
    # Stop and cleanup VideoProcessor
    if id in active_processors:
        try:
            processor_info = active_processors[id]
            processor = processor_info["processor"]
            task = processor_info["task"]
            
            # Signal processor to stop
            processor.stop_processing_loop()
            
            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"VideoProcessor task for feed {id} cancelled")
            
            del active_processors[id]
            logger.info(f"Stopped VideoProcessor for feed {id}")
        except Exception as e:
            logger.error(f"Error stopping VideoProcessor for feed {id}: {e}")
    
    # Delete from database
    db.delete(feed)
    db.commit()
    
    return None
