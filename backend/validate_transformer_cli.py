import json
from argparse import Namespace
from pathlib import Path

from app.transformer.dataset import BehaviourSequenceDataset
from app.transformer.infer import load_model, predict
from app.transformer.train import train_model

FEATURE_KEYS = [
    "edge_proximity",
    "loitering_time",
    "pacing_count",
    "movement_speed",
    "direction_changes",
    "following_distance",
    "crowd_interactions",
]

LABELS = ["Normal", "Suicide Risk", "Pickpocketing", "Security Threat"]


def build_jsonl(path: Path) -> None:
    rows = []
    for label in LABELS:
        for _ in range(8):
            features = []
            for t in range(30):
                sample = {key: float((t + 1) % 5) for key in FEATURE_KEYS}
                sample["crowd_interactions"] = float((LABELS.index(label) + 1) * 0.5)
                features.append(sample)
            rows.append({"features": features, "label": label})
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def main() -> None:
    base = Path(__file__).resolve().parent
    data_path = base / "tmp_behavior_data.jsonl"
    output_dir = base / "app" / "transformer" / "saved_models"
    output_dir.mkdir(parents=True, exist_ok=True)
    build_jsonl(data_path)

    dataset = BehaviourSequenceDataset(data_path=data_path, scaler_path=output_dir / "feature_scaler.pkl")
    seq, label = dataset[0]
    assert seq.shape == (30, 7)
    assert label.item() in {0, 1, 2, 3}

    train_model(
        Namespace(
            data_path=str(data_path),
            epochs=2,
            batch_size=8,
            lr=1e-3,
            val_split=0.2,
            output_dir=str(output_dir),
        )
    )

    checkpoint_path = output_dir / "behaviour_transformer.pt"
    scaler_path = output_dir / "feature_scaler.pkl"
    assert checkpoint_path.exists(), "Model checkpoint was not created."
    assert scaler_path.exists(), "Scaler artifact was not created."

    model, scaler = load_model(checkpoint_path, scaler_path)
    feature_dicts = [
        {key: float(value) for key, value in zip(FEATURE_KEYS, row)}
        for row in seq.detach().cpu().tolist()
    ]
    result = predict(model, scaler, feature_dicts)
    assert result["predicted_class"] in LABELS
    assert 0.0 <= result["confidence"] <= 1.0
    print("VALIDATION_OK")
    print(result)


if __name__ == "__main__":
    main()
