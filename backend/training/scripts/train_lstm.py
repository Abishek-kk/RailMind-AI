"""Train LSTM models for behavior classification"""
import sys
from pathlib import Path
import numpy as np

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.utils import to_categorical
except ImportError:
    Sequential = None
    LSTM = None
    Dense = None
    Dropout = None
    to_categorical = None

MODEL_OUTPUT_PATH = Path(__file__).resolve().parents[2] / "app" / "lstm" / "saved_models" / "behavior_classifier.h5"
DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets"


def build_model(input_shape, num_classes):
    """Build a simple LSTM classifier."""
    if Sequential is None:
        raise ImportError("TensorFlow/Keras is required to build the model")

    model = Sequential(
        [
            LSTM(64, input_shape=input_shape, return_sequences=True),
            Dropout(0.3),
            LSTM(32),
            Dropout(0.2),
            Dense(32, activation="relu"),
            Dense(num_classes, activation="softmax"),
        ]
    )
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def train_model(model_type="behavior"):
    """Train LSTM model for behavior classification"""
    print(f"Training {model_type} model...")

    train_data = np.load(DATASET_DIR / "train_sequences.npy")
    train_labels = np.load(DATASET_DIR / "train_labels.npy")

    print(f"Training data shape: {train_data.shape}")
    print(f"Training labels shape: {train_labels.shape}")

    if train_data.ndim == 2:
        train_data = train_data.reshape(train_data.shape[0], train_data.shape[1], 1)

    num_classes = int(np.max(train_labels) + 1) if train_labels.size > 0 else 2
    model = build_model(input_shape=train_data.shape[1:], num_classes=num_classes)
    model.fit(train_data, train_labels, epochs=10, batch_size=16, validation_split=0.1, verbose=1)

    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_OUTPUT_PATH))
    print(f"Saved trained model to {MODEL_OUTPUT_PATH}")


def evaluate_model(model_path):
    """Evaluate trained model on test set"""
    if Sequential is None:
        raise ImportError("TensorFlow/Keras is required for evaluation")

    from tensorflow.keras.models import load_model

    test_data = np.load(DATASET_DIR / "test_sequences.npy")
    test_labels = np.load(DATASET_DIR / "test_labels.npy")
    print(f"Evaluating model from {model_path}")
    print(f"Test data shape: {test_data.shape}")
    print(f"Test labels shape: {test_labels.shape}")

    if test_data.ndim == 2:
        test_data = test_data.reshape(test_data.shape[0], test_data.shape[1], 1)

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")

    model = load_model(str(model_path))
    result = model.evaluate(test_data, test_labels, verbose=0)
    print({"loss": float(result[0]), "accuracy": float(result[1])})


if __name__ == "__main__":
    model_type = sys.argv[1] if len(sys.argv) > 1 else "behavior"
    train_model(model_type)
