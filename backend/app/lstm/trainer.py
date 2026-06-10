import os
import logging

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

from app.core.config import settings
from app.lstm.model import build_lstm_model

logger = logging.getLogger("railmind")


class LSTMTrainer:
    def __init__(self, sequence_length: int = 30, num_features: int = 7, device: str = None):
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = build_lstm_model(sequence_length, num_features).to(self.device)
        logger.info(f"Using device: {self.device}")

    def execute_training_run(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        target_output_filename: str,
        epochs: int = 40,
        batch_size: int = 32,
    ):
        """
        Compiles dataset inputs, runs the training loop, and saves the top-performing
        epoch matrix to disk.
        """
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        destination_save_path = os.path.join(settings.MODEL_DIR, target_output_filename)

        # Convert numpy arrays to torch tensors
        X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
        y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
        X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
        y_val_tensor = torch.tensor(y_val, dtype=torch.float32)

        # Create dataloaders
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # Setup training
        criterion = nn.BCELoss()  # Binary cross-entropy for binary classification
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        best_val_loss = float("inf")
        patience = 6
        patience_counter = 0

        history_metrics = {
            "train_loss": [],
            "val_loss": [],
            "train_accuracy": [],
            "val_accuracy": [],
        }

        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device).unsqueeze(1)  # Reshape for BCELoss

                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

                # Calculate accuracy
                predictions = (outputs > 0.5).float()
                train_correct += (predictions == batch_y).sum().item()
                train_total += batch_y.size(0)

            avg_train_loss = train_loss / len(train_loader)
            train_accuracy = train_correct / train_total if train_total > 0 else 0

            # Validation phase
            self.model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device).unsqueeze(1)

                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()

                    predictions = (outputs > 0.5).float()
                    val_correct += (predictions == batch_y).sum().item()
                    val_total += batch_y.size(0)

            avg_val_loss = val_loss / len(val_loader)
            val_accuracy = val_correct / val_total if val_total > 0 else 0

            # Record metrics
            history_metrics["train_loss"].append(avg_train_loss)
            history_metrics["val_loss"].append(avg_val_loss)
            history_metrics["train_accuracy"].append(train_accuracy)
            history_metrics["val_accuracy"].append(val_accuracy)

            logger.info(
                f"Epoch {epoch + 1}/{epochs} - "
                f"Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f} - "
                f"Train Acc: {train_accuracy:.4f}, Val Acc: {val_accuracy:.4f}"
            )

            # Early stopping + checkpoint
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                torch.save(self.model.state_dict(), destination_save_path)
                logger.info(f"Saved model to {destination_save_path}")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"Early stopping triggered after {epoch + 1} epochs")
                    break

        return history_metrics