import shutil
import tempfile

from app import main
from pipeline import results_store


def test_delete_feed_removes_processed_result_and_feed_registry(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="railmind-delete-")
    try:
        monkeypatch.setattr(main, "FEEDS", [{"id": "cam-1", "name": "Cam 1", "status": "active"}])
        monkeypatch.setattr(main, "PIPELINE_DATA_DIR", temp_dir)

        results_store.save_result(
            temp_dir,
            video_id="vid-1",
            feed_id="cam-1",
            feed_name="Cam 1",
            camera_id="cam-1",
            source_filename="demo.mp4",
            annotated_video_path="annotated/cam-1.mp4",
            tracks={"1": {"risk": "low"}},
        )

        response = main.delete_feed("cam-1")

        assert response == {"status": "deleted", "feed_id": "cam-1"}
        assert main.FEEDS == []
        assert results_store.get_by_feed_id(temp_dir, "cam-1") is None
        assert main.feeds() == []
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_feeds_include_track_count_from_processed_results(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="railmind-count-")
    try:
        monkeypatch.setattr(main, "FEEDS", [{"id": "cam-2", "name": "Cam 2", "status": "active"}])
        monkeypatch.setattr(main, "PIPELINE_DATA_DIR", temp_dir)

        results_store.save_result(
            temp_dir,
            video_id="vid-2",
            feed_id="cam-2",
            feed_name="Cam 2",
            camera_id="cam-2",
            source_filename="demo2.mp4",
            annotated_video_path="annotated/cam-2.mp4",
            tracks={"1": {"activity": "NORMAL"}, "2": {"activity": "NORMAL"}, "3": {"activity": "NORMAL"}},
        )

        feeds = main.feeds()

        assert len(feeds) == 1
        assert feeds[0]["id"] == "cam-2"
        assert feeds[0]["track_count"] == 3
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
