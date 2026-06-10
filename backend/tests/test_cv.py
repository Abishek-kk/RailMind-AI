"""Computer vision tests"""
import os
import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.cv import PoseEstimator, VideoProcessor
from app.cv.lstm_behavior import BehaviorAnalyzer
from app.core.config import settings
from app.lstm.predictor import LSTMPredictor


def test_pose_estimator_import():
    """Test that PoseEstimator is available"""
    assert PoseEstimator is not None


def test_video_processor_import():
    """Test that VideoProcessor is available"""
    assert VideoProcessor is not None


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


def test_lstm_predictor_does_not_create_default_models(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MODEL_DIR", str(tmp_path))

    predictor = LSTMPredictor(device="cpu")

    assert predictor.models == {}
    assert predictor.unavailable_models == {"suicide", "pickpocket", "anomaly"}
    assert predictor.run_inference("anomaly", np.zeros((1, 30, 7), dtype=np.float32)) == 0.0
    assert list(tmp_path.glob("*.pt")) == []
