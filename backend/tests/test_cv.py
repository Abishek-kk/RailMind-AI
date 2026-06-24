"""Computer vision tests"""
import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.cv import PoseEstimator, VideoProcessor
from app.cv.lstm_behavior import BehaviorAnalyzer
from app.core.config import settings
from app.features.following_detector import FollowingDetector
from app.features.pacing_detector import PacingDetector
from app.features.temporal_confirmation_tracker import TemporalConfirmationTracker
from app.services.context_suppression_service import ContextSuppressionService
from app.lstm.predictor import LSTMPredictor


def test_pose_estimator_import():
    """Test that PoseEstimator is available"""
    assert PoseEstimator is not None


def test_video_processor_import():
    """Test that VideoProcessor is available"""
    assert VideoProcessor is not None


def test_video_processor_missing_pose_model_degrades_cleanly(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "POSE_MODEL_PATH", str(tmp_path / "missing-yolov8n-pose.pt"))

    processor = VideoProcessor(feed_source="missing.mp4", camera_id="CAM_MISSING_POSE", platform="Platform 1")

    assert processor.pose_estimator.is_available is False
    assert processor.cv_available is False
    asyncio.run(processor.start_processing_loop())
    assert processor.is_running is False


def test_default_pose_model_weights_are_packaged():
    pose_model = Path(settings.POSE_MODEL_PATH)

    assert pose_model.exists(), f"Missing default YOLOv8 pose weights: {pose_model}"
    assert pose_model.stat().st_size > 0

    estimator = PoseEstimator(device="cpu")
    assert estimator.is_available is True
    assert estimator.unavailable_reason == ""


def test_video_processor_cv_available_with_packaged_pose_model():
    processor = VideoProcessor(feed_source="missing.mp4", camera_id="CAM_PACKAGED_POSE", platform="Platform 1")

    assert processor.pose_estimator.is_available is True
    assert processor.tracker is not None
    assert processor.cv_available is True


def test_behavior_analyzer_maps_scores_to_pose_labels():
    analyzer = BehaviorAnalyzer()
    # high suicide score should map to distress
    label = analyzer.determine_behavior_label({"suicide": 0.8, "pickpocket": 0.1, "anomaly": 0.1})
    assert label == "distress"

    # close following distance with pickpocket risk should map to following
    label = analyzer.determine_behavior_label({"suicide": 0.1, "pickpocket": 0.7, "anomaly": 0.2}, following_distance=0.9)
    assert label == "following"

    # suspicious or anomaly scores above threshold should map to suspicious
    label = analyzer.determine_behavior_label({"suicide": 0.1, "pickpocket": 0.7, "anomaly": 0.1})
    assert label == "suspicious"

    label = analyzer.determine_behavior_label({"suicide": 0.1, "pickpocket": 0.1, "anomaly": 0.8})
    assert label == "suspicious"

    # moderate values should map to erratic
    label = analyzer.determine_behavior_label({"suicide": 0.3, "pickpocket": 0.4, "anomaly": 0.4})
    assert label == "erratic"

    # low scores should map to normal
    label = analyzer.determine_behavior_label({"suicide": 0.2, "pickpocket": 0.1, "anomaly": 0.1})
    assert label == "normal"


def test_behavior_label_thresholds_are_configurable(monkeypatch):
    monkeypatch.setattr(settings, "BEHAVIOR_HIGH_SCORE_THRESHOLD", 0.75)
    monkeypatch.setattr(settings, "BEHAVIOR_ERRATIC_SCORE_THRESHOLD", 0.45)
    monkeypatch.setattr(settings, "BEHAVIOR_FOLLOWING_DISTANCE_METERS", 0.8)

    analyzer = BehaviorAnalyzer()

    assert analyzer.determine_behavior_label({"suicide": 0.7, "pickpocket": 0.1, "anomaly": 0.1}) == "erratic"
    assert analyzer.determine_behavior_label({"suicide": 0.75, "pickpocket": 0.1, "anomaly": 0.1}) == "distress"
    assert (
        analyzer.determine_behavior_label(
            {"suicide": 0.1, "pickpocket": 0.75, "anomaly": 0.1},
            following_distance=0.9,
        )
        == "suspicious"
    )
    assert (
        analyzer.determine_behavior_label(
            {"suicide": 0.1, "pickpocket": 0.75, "anomaly": 0.1},
            following_distance=0.7,
        )
        == "following"
    )


def test_following_detector_returns_distance_in_meters(monkeypatch):
    monkeypatch.setattr(settings, "PIXELS_PER_METER", 100.0)

    detector = FollowingDetector(distance_threshold=1.2)
    distance = detector.calculate_distance_between_tracks(
        {"center": (0.0, 0.0)},
        {"center": (120.0, 0.0)},
    )

    assert distance == 1.2


def test_following_detector_uses_meter_threshold(monkeypatch):
    monkeypatch.setattr(settings, "PIXELS_PER_METER", 100.0)

    detector = FollowingDetector(distance_threshold=1.2)
    tracks = {
        1: {"center": (0.0, 0.0), "trajectory": [(0.0, 0.0), (10.0, 0.0)]},
        2: {"center": (119.0, 0.0), "trajectory": [(100.0, 0.0), (119.0, 0.0)]},
        3: {"center": (121.0, 0.0), "trajectory": [(100.0, 0.0), (121.0, 0.0)]},
    }

    assert detector.get_following_distance(1, tracks) == 1.19
    assert detector.get_crowd_interaction_count(1, tracks) == 1


def test_pacing_detector_returns_window_cycles_not_cumulative_count():
    detector = PacingDetector(window_size=6, movement_threshold=1.0)
    positions = [(0, 0), (10, 0), (20, 0), (10, 0), (0, 0), (10, 0)]

    outputs = [detector.detect(1, {"center": position}) for position in positions]

    assert outputs[-1] == 1
    assert detector.detect(1, {"center": (20, 0)}) == 1


def test_pacing_detector_does_not_count_stationary_person():
    detector = PacingDetector(window_size=6, movement_threshold=1.0)

    outputs = [detector.detect(1, {"center": (10, 10)}) for _ in range(20)]

    assert outputs[-1] == 0


def test_lstm_predictor_does_not_create_default_models(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MODEL_DIR", str(tmp_path))

    predictor = LSTMPredictor(device="cpu")

    assert predictor.models == {}
    assert predictor.unavailable_models == {"normal", "suicide", "pickpocket", "anomaly"}
    assert predictor.run_inference("anomaly", np.zeros((1, 30, 7), dtype=np.float32)) == 0.0
    assert list(tmp_path.glob("*.pt")) == []


def test_temporal_confirmation_single_frame_does_not_trigger():
    tracker = TemporalConfirmationTracker(confirmation_seconds=15)

    tracker.update(1, True, 0.0)
    tracker.update(1, True, 1.0)

    assert not tracker.is_confirmed(1)


def test_temporal_confirmation_confirms_after_sustained_high_score():
    tracker = TemporalConfirmationTracker(confirmation_seconds=15)

    for i in range(16):
        tracker.update(1, True, float(i))

    assert tracker.is_confirmed(1)


def test_temporal_confirmation_resets_when_score_drops():
    tracker = TemporalConfirmationTracker(confirmation_seconds=15)

    for i in range(10):
        tracker.update(1, True, float(i))
    tracker.update(1, False, 10.0)
    tracker.update(1, False, 11.0)

    assert not tracker.is_confirmed(1)


def test_temporal_confirmation_clears_disappeared_tracks():
    tracker = TemporalConfirmationTracker(confirmation_seconds=15)

    for i in range(16):
        tracker.update(1, True, float(i))
    assert tracker.is_confirmed(1)

    tracker.clear_track(1)

    assert not tracker.is_confirmed(1)
    assert 1 not in tracker.consecutive_seconds
    assert 1 not in tracker.last_update_time


def test_video_processor_instantiates_temporal_confirmation_tracker():
    processor = VideoProcessor(feed_source="missing.mp4", camera_id="CAM_TRACKER", platform="Platform 1")

    from app.features.temporal_confirmation_tracker import TemporalConfirmationTracker
    assert isinstance(processor.temporal_confirmation_tracker, TemporalConfirmationTracker)


def test_frame_skip_interval_setting():
    from app.core.config import settings
    import app.cv.video_processor as vp
    import inspect

    assert settings.FRAME_SKIP_INTERVAL == 2

    original = settings.FRAME_SKIP_INTERVAL
    try:
        settings.FRAME_SKIP_INTERVAL = 1
        source = inspect.getsource(vp.VideoProcessor.start_processing_loop)
        assert "settings.FRAME_SKIP_INTERVAL" in source

        for frame_count in [1, 2, 3, 4, 5]:
            assert not (frame_count % settings.FRAME_SKIP_INTERVAL != 0)

        settings.FRAME_SKIP_INTERVAL = 3
        for frame_count in [1, 2, 3, 4, 5, 6]:
            assert (frame_count % settings.FRAME_SKIP_INTERVAL != 0) == (frame_count % 3 != 0)
    finally:
        settings.FRAME_SKIP_INTERVAL = original


def test_context_suppression_returns_normal_multiplier_for_no_data():
    service = ContextSuppressionService(db=SimpleNamespace())

    service._compute_peak_hours = lambda: {}

    assert service.get_threshold_adjustment("Platform 1", 14, db=SimpleNamespace()) == 1.0


def test_context_suppression_returns_peak_multiplier_for_elevated_hour():
    db = SimpleNamespace()

    def mock_query(*args, **kwargs):
        return SimpleNamespace(
            group_by=lambda *args, **kwargs: SimpleNamespace(
                all=lambda: [
                    ("Platform 1", "09", 50),
                    ("Platform 1", "10", 200),
                    ("Platform 1", "11", 20),
                    ("Platform 1", "14", 180),
                    ("Platform 1", "15", 15),
                ]
            )
        )

    db.query = mock_query

    service = ContextSuppressionService(db=db)

    assert service.get_threshold_adjustment("Platform 1", 10, db=db) == 1.3
    assert service.get_threshold_adjustment("Platform 1", 14, db=db) == 1.3
    assert service.get_threshold_adjustment("Platform 1", 9, db=db) == 1.0
    assert service.get_threshold_adjustment("Platform 1", 11, db=db) == 1.0


def test_context_suppression_is_confirmed_at_peak_hours():
    service = ContextSuppressionService(db=SimpleNamespace())
    service._peak_hours_cache = {"Platform 1": {8, 9, 17, 18}}
    service._cache_expires_at = float("inf")

    for hour in [8, 9, 17, 18]:
        assert service.get_threshold_adjustment("Platform 1", hour) == 1.3

    for hour in [0, 1, 10, 12, 23]:
        assert service.get_threshold_adjustment("Platform 1", hour) == 1.0
