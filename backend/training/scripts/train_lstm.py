"""Train LSTM models for behavior classification"""
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.lstm.model import build_lstm_model

MODEL_OUTPUT_PATH = Path(__file__).resolve().parents[2] / "app" / "lstm" / "saved_models" / "behavior_classifier.pt"
DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def build_model(sequence_length, num_features, num_classes):
    """Build LSTM classifier."""
    return build_lstm_model(sequence_length=sequence_length, num_features=num_features, num_classes=num_classes)


def train_model(model_type="behavior"):
    """Train LSTM model for behavior classification"""
    print(f"Training {model_type} model...")

    train_data = np.load(DATASET_DIR / "train_sequences.npy")
    train_labels = np.load(DATASET_DIR / "train_labels.npy")

    print(f"Training data shape: {train_data.shape}")
    print(f"Training labels shape: {train_labels.shape}")

    # Reshape data if needed (add feature dimension)
    if train_data.ndim == 2:
        train_data = train_data.reshape(train_data.shape[0], train_data.shape[1], 1)

    num_classes = int(np.max(train_labels) + 1) if train_labels.size > 0 else 2
    sequence_length = train_data.shape[1]
    num_features = train_data.shape[2] if train_data.ndim == 3 else 1

    model = build_model(sequence_length, num_features, num_classes).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Convert to tensors
    train_data_tensor = torch.tensor(train_data, dtype=torch.float32)
    train_labels_tensor = torch.tensor(train_labels, dtype=torch.long)

    # Create dataloader
    dataset = TensorDataset(train_data_tensor, train_labels_tensor)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)

    # Training loop
    for epoch in range(10):
        model.train()
        total_loss = 0.0

        for batch_data, batch_labels in dataloader:
            batch_data = batch_data.to(DEVICE)
            batch_labels = batch_labels.to(DEVICE)

            optimizer.zero_grad()
            outputs = model(batch_data)
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch + 1}/10, Loss: {avg_loss:.4f}")

    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), str(MODEL_OUTPUT_PATH))
    print(f"Saved trained model to {MODEL_OUTPUT_PATH}")


def evaluate_model(model_path):
    """Evaluate trained model on test set"""
    test_data = np.load(DATASET_DIR / "test_sequences.npy")
    test_labels = np.load(DATASET_DIR / "test_labels.npy")
    print(f"Evaluating model from {model_path}")
    print(f"Test data shape: {test_data.shape}")
    print(f"Test labels shape: {test_labels.shape}")

    if test_data.ndim == 2:
        test_data = test_data.reshape(test_data.shape[0], test_data.shape[1], 1)

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")

    num_classes = int(np.max(test_labels) + 1) if test_labels.size > 0 else 2
    sequence_length = test_data.shape[1]
    num_features = test_data.shape[2] if test_data.ndim == 3 else 1

    model = build_model(sequence_length, num_features, num_classes).to(DEVICE)
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.eval()

    # Convert to tensors
    test_data_tensor = torch.tensor(test_data, dtype=torch.float32).to(DEVICE)
    test_labels_tensor = torch.tensor(test_labels, dtype=torch.long).to(DEVICE)

    # Evaluate
    criterion = nn.CrossEntropyLoss()
    with torch.no_grad():
        outputs = model(test_data_tensor)
        loss = criterion(outputs, test_labels_tensor).item()
        predictions = torch.argmax(outputs, dim=1)
        accuracy = (predictions == test_labels_tensor).float().mean().item()

    print({"loss": float(loss), "accuracy": float(accuracy)})


if __name__ == "__main__":
    model_type = sys.argv[1] if len(sys.argv) > 1 else "behavior"
    train_model(model_type)
