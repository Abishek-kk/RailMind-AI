"""Transformer model tests"""
import sys
from pathlib import Path
import numpy as np
import pytest
import torch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.transformer.model import build_temporal_transformer_model
from app.transformer.predictor import TemporalTransformerPredictor
from app.transformer.sequence_builder import SequenceBuilder
from app.transformer.train import SyntheticDataGenerator


def test_transformer_sequence_builder():
    """Test transformer sequence builder"""
    builder = SequenceBuilder(sequence_length=5)
    for i in range(5):
        builder.add_frame("track_1", [float(i), float(i + 1)])
    assert builder.is_sequence_complete("track_1")
    assert builder.get_sequence("track_1").shape == (5, 2)


def test_transformer_sequence_prediction():
    """Test transformer sequence builder padding and retrieval"""
    builder = SequenceBuilder(sequence_length=3)
    builder.add_frame("track_2", [1.0, 2.0])
    builder.add_frame("track_2", [2.0, 3.0])
    seq = builder.get_sequence("track_2")
    assert isinstance(seq, np.ndarray)
    assert seq.shape == (3, 2)


def test_transformer_model_builds_and_runs_inference():
    """The new temporal transformer should produce a valid classification output."""
    model = build_temporal_transformer_model(
        sequence_length=settings.TRANSFORMER_SEQUENCE_LENGTH,
        num_features=settings.TRANSFORMER_FEATURE_COUNT,
        num_classes=4,
    )
    sample = np.random.randn(2, settings.TRANSFORMER_SEQUENCE_LENGTH, settings.TRANSFORMER_FEATURE_COUNT).astype(np.float32)
    with torch.no_grad():
        logits = model(torch.from_numpy(sample))

    assert logits.shape == (2, 4)
    assert torch.allclose(logits.sum(dim=1), torch.ones(2), atol=1e-5)


def test_trained_transformer_artifacts_load_and_score_non_neutral(monkeypatch):
    """Guard against shipping neutral/random transformer stubs in the live demo path."""
    model_dir = Path(settings.MODEL_DIR)
    expected_files = [
        "behavior_classifier.pt",
        "behavior_classifier_scaler.pkl",
    ]

    for filename in expected_files:
        artifact_path = model_dir / filename
        assert artifact_path.exists(), f"Missing trained transformer artifact: {artifact_path}"
        assert artifact_path.stat().st_size > 0

    monkeypatch.setattr(settings, "MODEL_DIR", str(model_dir))
    predictor = TemporalTransformerPredictor(device="cpu")

    assert predictor.unavailable_models == set()
    assert set(predictor.models) == {"normal", "suicide", "pickpocket", "anomaly"}

    model = build_temporal_transformer_model(
        sequence_length=settings.TRANSFORMER_SEQUENCE_LENGTH,
        num_features=settings.TRANSFORMER_FEATURE_COUNT,
        num_classes=4,
    )
    assert model.classifier.out_features == 4

    generator = SyntheticDataGenerator(
        sequence_length=settings.TRANSFORMER_SEQUENCE_LENGTH,
        num_features=settings.TRANSFORMER_FEATURE_COUNT,
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
        assert np.isfinite(threat_score)
        assert np.isfinite(normal_score)

    normal_probability = sum(
        predictor.run_inference(target, normal)
        for target in ("normal", "suicide", "pickpocket", "anomaly")
    )
    assert normal_probability == pytest.approx(1.0, abs=1e-5)
