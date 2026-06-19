"""LSTM model tests"""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.lstm.model import build_lstm_model
from app.lstm.predictor import LSTMPredictor
from app.lstm.sequence_builder import SequenceBuilder
from app.lstm.train import SyntheticDataGenerator


def test_lstm_training():
    """Test LSTM training"""
    builder = SequenceBuilder(sequence_length=5)
    for i in range(5):
        sequence = builder.add_frame("track_1", [float(i), float(i + 1)])
    assert builder.is_sequence_complete("track_1")
    assert builder.get_sequence("track_1").shape == (5, 2)


def test_lstm_prediction():
    """Test LSTM prediction"""
    builder = SequenceBuilder(sequence_length=3)
    builder.add_frame("track_2", [1.0, 2.0])
    builder.add_frame("track_2", [2.0, 3.0])
    seq = builder.get_sequence("track_2")
    assert isinstance(seq, np.ndarray)
    assert seq.shape == (3, 2)


def test_trained_lstm_artifacts_load_and_score_non_neutral(monkeypatch):
    """Guard against shipping neutral/random LSTM stubs in the live demo path."""
    model_dir = Path(settings.MODEL_DIR)
    expected_files = [
        "behavior_classifier.pt",
        "behavior_classifier_scaler.pkl",
    ]

    for filename in expected_files:
        artifact_path = model_dir / filename
        assert artifact_path.exists(), f"Missing trained LSTM artifact: {artifact_path}"
        assert artifact_path.stat().st_size > 0

    monkeypatch.setattr(settings, "MODEL_DIR", str(model_dir))
    predictor = LSTMPredictor(device="cpu")

    assert predictor.unavailable_models == set()
    assert set(predictor.models) == {"normal", "suicide", "pickpocket", "anomaly"}

    model = build_lstm_model(
        sequence_length=settings.LSTM_SEQUENCE_LENGTH,
        num_features=settings.LSTM_FEATURE_COUNT,
        num_classes=4,
    )
    assert model.fc2.out_features == 4

    generator = SyntheticDataGenerator(
        sequence_length=settings.LSTM_SEQUENCE_LENGTH,
        num_features=settings.LSTM_FEATURE_COUNT,
        seed=123,
    )
    normal = generator.generate_normal_sequences(num_sequences=1)[0]
    threat_sequences = {
        "suicide": generator.generate_suicide_risk_sequences(num_sequences=1)[0],
        "pickpocket": generator.generate_pickpocket_sequences(num_sequences=1)[0],
        "anomaly": generator.generate_security_threat_sequences(num_sequences=1)[0],
    }

    for target, threat_sequence in threat_sequences.items():
        normal_score = predictor.run_inference(target, normal)
        threat_score = predictor.run_inference(target, threat_sequence)

        assert threat_score != 0.0
        assert threat_score > normal_score + 0.2

    normal_probability = sum(
        predictor.run_inference(target, normal)
        for target in ("normal", "suicide", "pickpocket", "anomaly")
    )
    assert normal_probability == pytest.approx(1.0, abs=1e-5)
