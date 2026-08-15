import json
import tempfile
from pathlib import Path

import torch

from app.transformer.dataset import BehaviourSequenceDataset
from app.transformer.infer import predict
from app.transformer.model import TemporalTransformer


FEATURE_KEYS = [
    "edge_proximity",
    "loitering_time",
    "pacing_count",
    "movement_speed",
    "direction_changes",
    "following_distance",
    "crowd_interactions",
]


def _write_jsonl(path: Path, labels: list[str]) -> None:
    rows = []
    for label in labels:
        features = []
        for _ in range(30):
            sample = {key: float((idx + 1) % 5) for idx, key in enumerate(FEATURE_KEYS)}
            features.append(sample)
        rows.append({"features": features, "label": label})
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_dataset_and_model_contract():
    with tempfile.TemporaryDirectory(dir=str(Path(__file__).resolve().parent.parent)) as tmp_dir:
        tmp_path = Path(tmp_dir)
        data_path = tmp_path / "train.jsonl"
        _write_jsonl(data_path, ["Normal", "Suicide Risk", "Pickpocketing", "Security Threat"])

        dataset = BehaviourSequenceDataset(data_path=str(data_path), scaler_path=tmp_path / "feature_scaler.pkl")
        seq, label = dataset[0]

        assert seq.shape == (30, 7)
        assert label in torch.tensor([0, 1, 2, 3])

        model = TemporalTransformer()
        logits = model(seq.unsqueeze(0))
        assert logits.shape == (1, 4)


def test_inference_prediction_structure():
    with tempfile.TemporaryDirectory(dir=str(Path(__file__).resolve().parent.parent)) as tmp_dir:
        tmp_path = Path(tmp_dir)
        data_path = tmp_path / "train.jsonl"
        _write_jsonl(data_path, ["Normal", "Suicide Risk", "Pickpocketing", "Security Threat"])

        dataset = BehaviourSequenceDataset(data_path=str(data_path), scaler_path=tmp_path / "feature_scaler.pkl")
        model = TemporalTransformer()
        model.eval()

feature_dicts = [
        {key: float(value) for key, value in zip(FEATURE_KEYS, row)}
        for row in dataset[0][0].detach().cpu().tolist()
    ]
    result = predict(model, dataset.scaler, feature_dicts)

        assert set(result.keys()) == {"predicted_class", "confidence", "probabilities"}
        assert result["predicted_class"] in {"Normal", "Suicide Risk", "Pickpocketing", "Security Threat"}
        assert 0.0 <= result["confidence"] <= 1.0
        assert set(result["probabilities"].keys()) == {"Normal", "Suicide Risk", "Pickpocketing", "Security Threat"}
