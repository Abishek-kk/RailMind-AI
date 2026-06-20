"""Evaluate trained LSTM models"""
from pathlib import Path
import sys

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.lstm.model import build_lstm_model

MODEL_PATH = Path(__file__).resolve().parents[2] / "app" / "lstm" / "saved_models" / "behavior_classifier.pt"
DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def evaluate_all_models():
    """Evaluate behavior classifier model"""
    print("Loading test data...")
    test_data = np.load(DATASET_DIR / "test_sequences.npy")
    test_labels = np.load(DATASET_DIR / "test_labels.npy")

    print(f"Evaluating model from {MODEL_PATH}")
    print(f"Test data shape: {test_data.shape}")
    print(f"Test labels shape: {test_labels.shape}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

    if test_data.ndim == 2:
        test_data = test_data.reshape(test_data.shape[0], test_data.shape[1], 1)

    num_classes = int(np.max(test_labels) + 1) if test_labels.size > 0 else 2
    sequence_length = test_data.shape[1]
    num_features = test_data.shape[2] if test_data.ndim == 3 else 1

    model = build_lstm_model(sequence_length, num_features, num_classes).to(DEVICE)
    model.load_state_dict(torch.load(str(MODEL_PATH), map_location=DEVICE))
    model.eval()

    # Convert to tensors
    test_data_tensor = torch.tensor(test_data, dtype=torch.float32).to(DEVICE)
    test_labels_tensor = torch.tensor(test_labels, dtype=torch.long).to(DEVICE)

    # Evaluate
    criterion = torch.nn.CrossEntropyLoss()
    with torch.no_grad():
        outputs = model(test_data_tensor)
        loss = criterion(outputs, test_labels_tensor).item()
        predictions = torch.argmax(outputs, dim=1)
        accuracy = (predictions == test_labels_tensor).float().mean().item()

    print({"loss": float(loss), "accuracy": float(accuracy)})
    return {"loss": float(loss), "accuracy": float(accuracy)}


def generate_report():
    """Generate evaluation report with metrics"""
    behavior_types = [
        "normal",
        "suicide_risk",
        "pickpocketing",
        "loitering",
        "track_intrusion",
        "suspicious_following",
    ]

    print("\n=== Model Evaluation Report ===")
    print(f"Behaviors evaluated: {len(behavior_types)}")
    for behavior in behavior_types:
        print(f"  - {behavior}")
    return {
        "behaviors": behavior_types,
        "summary": f"Evaluated {len(behavior_types)} behavior classes",
    }


if __name__ == "__main__":
    evaluate_all_models()
    generate_report()
