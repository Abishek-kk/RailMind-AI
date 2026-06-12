"""
Synthetic data generator and LSTM training script for behavior classification.

Generates synthetic behavioral sequences for 4 behavior classes:
1. Normal
2. Suicide Risk
3. Pickpocketing
4. Security Threat

Trains separate binary classifiers for each threat type vs. normal activity.
"""

import os
import logging
import pickle
from pathlib import Path

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from app.core.config import settings
from app.lstm.model import LSTMBehaviorModel

logger = logging.getLogger("railmind")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class SyntheticDataGenerator:
    """Generates realistic synthetic behavioral sequences for LSTM training."""

    def __init__(self, sequence_length: int = 30, num_features: int = 7, seed: int = 42):
        self.sequence_length = sequence_length
        self.num_features = num_features
        np.random.seed(seed)

    def _augment_sequence(self, sequence: np.ndarray) -> np.ndarray:
        noise = np.random.normal(loc=0.0, scale=0.05, size=sequence.shape)
        sequence = sequence + noise
        return np.clip(sequence, 0.0, None)

    def generate_normal_sequences(self, num_sequences: int = 2000) -> np.ndarray:
        sequences = []
        for _ in range(num_sequences):
            sequence = np.zeros((self.sequence_length, self.num_features))
            sequence[:, 0] = np.random.uniform(0, 5, size=self.sequence_length)
            sequence[:, 1] = np.random.uniform(0, 30, size=self.sequence_length)
            sequence[:, 2] = np.random.uniform(0, 1, size=self.sequence_length)
            sequence[:, 3] = np.random.uniform(0.5, 2.0, size=self.sequence_length)
            sequence[:, 4] = np.random.uniform(0, 2, size=self.sequence_length)
            sequence[:, 5] = np.random.uniform(2, 10, size=self.sequence_length)
            sequence[:, 6] = np.random.uniform(0, 2, size=self.sequence_length)
            sequences.append(self._augment_sequence(sequence))
        return np.array(sequences)

    def generate_suicide_risk_sequences(self, num_sequences: int = 2000) -> np.ndarray:
        sequences = []
        for _ in range(num_sequences):
            sequence = np.zeros((self.sequence_length, self.num_features))
            sequence[:, 0] = np.random.uniform(20, 30, size=self.sequence_length)
            sequence[:, 1] = np.random.uniform(10, 30, size=self.sequence_length)
            sequence[:, 2] = np.random.uniform(3, 8, size=self.sequence_length)
            sequence[:, 3] = np.random.uniform(0.1, 0.5, size=self.sequence_length)
            sequence[:, 4] = np.random.uniform(4, 10, size=self.sequence_length)
            sequence[:, 5] = np.random.uniform(0, 5, size=self.sequence_length)
            sequence[:, 6] = np.random.uniform(0, 1, size=self.sequence_length)
            sequences.append(self._augment_sequence(sequence))
        return np.array(sequences)

    def generate_pickpocket_sequences(self, num_sequences: int = 2000) -> np.ndarray:
        sequences = []
        for _ in range(num_sequences):
            sequence = np.zeros((self.sequence_length, self.num_features))
            sequence[:, 0] = np.random.uniform(0, 20, size=self.sequence_length)
            sequence[:, 1] = np.random.uniform(0, 20, size=self.sequence_length)
            sequence[:, 2] = np.random.uniform(0, 1, size=self.sequence_length)
            sequence[:, 3] = np.random.uniform(0.8, 1.5, size=self.sequence_length)
            sequence[:, 4] = np.random.uniform(0, 5, size=self.sequence_length)
            sequence[:, 5] = np.random.uniform(0, 0.5, size=self.sequence_length)
            sequence[:, 6] = np.random.uniform(4, 10, size=self.sequence_length)
            sequences.append(self._augment_sequence(sequence))
        return np.array(sequences)

    def generate_security_threat_sequences(self, num_sequences: int = 2000) -> np.ndarray:
        sequences = []
        for _ in range(num_sequences):
            sequence = np.zeros((self.sequence_length, self.num_features))
            sequence[:, 0] = np.random.uniform(0, 20, size=self.sequence_length)
            sequence[:, 1] = np.random.uniform(0, 30, size=self.sequence_length)
            sequence[:, 2] = np.random.uniform(0, 4, size=self.sequence_length)
            sequence[:, 3] = np.random.uniform(2, 5, size=self.sequence_length)
            sequence[:, 4] = np.random.uniform(6, 15, size=self.sequence_length)
            sequence[:, 5] = np.random.uniform(0, 10, size=self.sequence_length)
            sequence[:, 6] = np.random.uniform(2, 6, size=self.sequence_length)
            sequences.append(self._augment_sequence(sequence))
        return np.array(sequences)

    def generate_all_data(self) -> dict:
        logger.info("Generating synthetic behavioral sequences...")
        data = {
            "normal": self.generate_normal_sequences(),
            "suicide": self.generate_suicide_risk_sequences(),
            "pickpocket": self.generate_pickpocket_sequences(),
            "security_threat": self.generate_security_threat_sequences(),
        }
        for behavior, sequences in data.items():
            logger.info(f"Generated {len(sequences)} {behavior} sequences with shape {sequences.shape}")
        return data


def create_binary_dataset(
    normal_sequences: np.ndarray,
    threat_sequences: np.ndarray,
    val_split: float = 0.2,
    seed: int = 42,
):
    X = np.vstack([normal_sequences, threat_sequences])
    y = np.hstack([np.zeros(len(normal_sequences)), np.ones(len(threat_sequences))])

    rng = np.random.RandomState(seed)
    indices = rng.permutation(len(X))
    X = X[indices]
    y = y[indices]

    n_val = int(len(X) * val_split)
    n_train = len(X) - n_val

    X_train = X[:n_train]
    y_train = y[:n_train]
    X_val = X[n_train:]
    y_val = y[n_train:]

    scaler = StandardScaler()
    X_train_flat = X_train.reshape(-1, X_train.shape[-1])
    scaler.fit(X_train_flat)

    X_train = scaler.transform(X_train_flat).reshape(X_train.shape)
    X_val = scaler.transform(X_val.reshape(-1, X_val.shape[-1])).reshape(X_val.shape)

    logger.info(f"Dataset split: Train={len(X_train)}, Val={len(X_val)}")
    return X_train, y_train, X_val, y_val, scaler


def train_classifier(
    target_name: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    output_filename: str,
    scaler: StandardScaler,
    epochs: int = 30,
    batch_size: int = 32,
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = LSTMBehaviorModel(
        sequence_length=settings.LSTM_SEQUENCE_LENGTH,
        num_features=settings.LSTM_FEATURE_COUNT,
        num_classes=1,
    ).to(device)

    criterion = torch.nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    train_dataset = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32).unsqueeze(1),
    )
    val_dataset = TensorDataset(
        torch.tensor(X_val, dtype=torch.float32),
        torch.tensor(y_val, dtype=torch.float32).unsqueeze(1),
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    history = {
        "train_loss": [],
        "val_loss": [],
        "train_accuracy": [],
        "val_accuracy": [],
    }

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for batch_X, batch_y in train_loader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * batch_X.size(0)
            predictions = (outputs > 0.5).float()
            train_correct += (predictions == batch_y).sum().item()
            train_total += batch_X.size(0)

        avg_train_loss = train_loss / train_total if train_total else 0.0
        train_accuracy = train_correct / train_total if train_total else 0.0

        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X = batch_X.to(device)
                batch_y = batch_y.to(device)

                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)

                val_loss += loss.item() * batch_X.size(0)
                predictions = (outputs > 0.5).float()
                val_correct += (predictions == batch_y).sum().item()
                val_total += batch_X.size(0)

        avg_val_loss = val_loss / val_total if val_total else 0.0
        val_accuracy = val_correct / val_total if val_total else 0.0

        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(avg_val_loss)
        history["train_accuracy"].append(train_accuracy)
        history["val_accuracy"].append(val_accuracy)

        logger.info(
            f"Epoch {epoch}/{epochs} - "
            f"Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f} - "
            f"Train Acc: {train_accuracy:.4f}, Val Acc: {val_accuracy:.4f}"
        )

    model_path = Path(settings.MODEL_DIR) / output_filename
    torch.save(model.state_dict(), model_path)
    logger.info(f"✓ Saved {target_name} model to {model_path}")

    scaler_path = model_path.with_suffix("_scaler.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    logger.info(f"✓ Saved scaler to {scaler_path}")

    logger.info(
        f"Final {target_name} Accuracy -> Train: {history['train_accuracy'][-1]:.4f}, "
        f"Val: {history['val_accuracy'][-1]:.4f}"
    )

    return history


def main():
    logger.info("=" * 70)
    logger.info("LSTM Behavior Classification Training Pipeline")
    logger.info("=" * 70)

    generator = SyntheticDataGenerator(
        sequence_length=settings.LSTM_SEQUENCE_LENGTH,
        num_features=settings.LSTM_FEATURE_COUNT,
    )
    data = generator.generate_all_data()

    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    logger.info(f"Model directory: {settings.MODEL_DIR}")

    classifiers = [
        ("Suicide Risk", "suicide_classifier.pt", data["normal"], data["suicide"]),
        ("Pickpocket", "pickpocket_classifier.pt", data["normal"], data["pickpocket"]),
        ("Security Threat/Anomaly", "anomaly_classifier.pt", data["normal"], data["security_threat"]),
    ]

    for display_name, filename, normal_seq, threat_seq in classifiers:
        logger.info("\n" + "=" * 70)
        logger.info(f"Training {display_name} classifier")
        logger.info("=" * 70)

        X_train, y_train, X_val, y_val, scaler = create_binary_dataset(
            normal_seq, threat_seq, val_split=0.2, seed=42
        )

        train_classifier(
            display_name,
            X_train,
            y_train,
            X_val,
            y_val,
            filename,
            scaler,
            epochs=30,
            batch_size=32,
        )

    logger.info("\n" + "=" * 70)
    logger.info("✓ All models trained and saved successfully!")
    logger.info("=" * 70)
    logger.info(f"Models saved in: {settings.MODEL_DIR}")
    logger.info("Generated models:")
    logger.info("  - suicide_classifier.pt")
    logger.info("  - pickpocket_classifier.pt")
    logger.info("  - anomaly_classifier.pt")


if __name__ == "__main__":
    main()
