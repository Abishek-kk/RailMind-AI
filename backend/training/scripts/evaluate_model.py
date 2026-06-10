"""Evaluate trained LSTM models"""
from pathlib import Path
import numpy as np

try:
    from tensorflow.keras.models import load_model
except ImportError:
    load_model = None

MODEL_PATH = Path(__file__).resolve().parents[2] / "app" / "lstm" / "saved_models" / "behavior_classifier.h5"
DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets"


def evaluate_all_models():
    """Evaluate behavior classifier model"""
    if load_model is None:
        raise ImportError("TensorFlow/Keras is required to evaluate the model")

    print("Loading test data...")
    test_data = np.load(DATASET_DIR / "test_sequences.npy")
    test_labels = np.load(DATASET_DIR / "test_labels.npy")

    print(f"Evaluating model from {MODEL_PATH}")
    print(f"Test data shape: {test_data.shape}")
    print(f"Test labels shape: {test_labels.shape}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

    model = load_model(str(MODEL_PATH))
    if test_data.ndim == 2:
        test_data = test_data.reshape(test_data.shape[0], test_data.shape[1], 1)

    loss, accuracy = model.evaluate(test_data, test_labels, verbose=0)
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
