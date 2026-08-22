import tempfile

from pipeline import aggregation, alert_status_store, results_store


def _save_tracks(data_dir: str) -> None:
    results_store.save_result(
        data_dir,
        video_id="video-1",
        feed_id="feed-1",
        feed_name="Platform 1",
        camera_id="camera-1",
        source_filename="source.mp4",
        annotated_video_path="video-1/annotated.mp4",
        tracks={
            "normal": {"activity": "NORMAL"},
            "medium": {"activity": "ERRATIC_MOVEMENT"},
            "high": {"activity": "IN_DANGER_ZONE"},
        },
    )


def test_alerts_include_normal_medium_and_high_handling_levels():
    with tempfile.TemporaryDirectory() as data_dir:
        _save_tracks(data_dir)

        alerts = aggregation.alerts_list(data_dir)

        assert {alert["handling_level"] for alert in alerts} == {"normal", "medium", "high"}


def test_escalation_persists_across_status_updates():
    with tempfile.TemporaryDirectory() as data_dir:
        alert_status_store.escalate(data_dir, "feed-1-normal", "medium", "Repeated movement")
        alert_status_store.update_status(data_dir, "feed-1-normal", "acknowledged")

        record = alert_status_store.get_status(data_dir, "feed-1-normal")

        assert record["status"] == "acknowledged"
        assert record["handling_level"] == "medium"
        assert record["escalation_reason"] == "Repeated movement"