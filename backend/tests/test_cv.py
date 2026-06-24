"""Computer vision tests"""
import asyncio
import os
import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.cv import PoseEstimator, VideoProcessor
from app.cv.lstm_behavior import BehaviorAnalyzer
from app.core.config import settings
from app.features.following_detector import FollowingDetector
from app.features.pacing_detector import PacingDetector
from app.features.temporal_confirmation_tracker import TemporalConfirmationTracker
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
