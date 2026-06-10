"""
Synthetic data generator and LSTM training script for behavior classification.

Generates synthetic behavioral sequences for 4 behavior classes:
1. Normal Activity
2. Suicide Risk
3. Pickpocketing
4. Security Threat (Anomaly)

Trains separate binary classifiers for each threat type vs. normal activity.
"""

import os
import sys
import logging
from pathlib import Path

import numpy as np
import torch

from app.lstm.trainer import LSTMTrainer
from app.core.config import settings

logger = logging.getLogger("railmind")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class SyntheticDataGenerator:
    """Generates realistic synthetic behavioral sequences for LSTM training."""

    def __init__(self, sequence_length: int = 30, num_features: int = 7, seed: int = 42):
        """
        Initialize the synthetic data generator.
        
        Args:
            sequence_length: Number of frames per sequence (default: 30)
            num_features: Number of behavioral features per frame (default: 7)
            seed: Random seed for reproducibility
        """
        self.sequence_length = sequence_length
        self.num_features = num_features
        np.random.seed(seed)

    def generate_normal_sequences(self, num_sequences: int = 200) -> np.ndarray:
        """
        Generate normal activity sequences.
        
        Characteristics:
        - Low edge proximity (person away from edges)
        - Minimal loitering
        - Regular pacing patterns
        - Moderate, consistent movement speed
        - Few direction changes
        - Isolated movement (not following anyone)
        - No crowd interactions
        """
        sequences = []
        for _ in range(num_sequences):
            sequence = np.zeros((self.sequence_length, self.num_features))
            
            for t in range(self.sequence_length):
                # Feature layout: [edge_proximity, loitering, pacing, speed, direction_changes, following_distance, crowd_interactions]
                sequence[t, 0] = np.random.uniform(20, 50)  # edge_proximity_seconds (high = safe)
                sequence[t, 1] = np.random.uniform(0, 5)    # loitering_time
                sequence[t, 2] = np.random.uniform(0, 2)    # pacing_count
                sequence[t, 3] = np.random.uniform(0.5, 2.0)  # movement_speed
                sequence[t, 4] = np.random.uniform(0, 3)    # direction_changes
                sequence[t, 5] = np.random.uniform(200, 1000)  # following_distance
                sequence[t, 6] = np.random.uniform(0, 1)    # crowd_interactions
            
            sequences.append(sequence)
        
        return np.array(sequences)

    def generate_suicide_risk_sequences(self, num_sequences: int = 150) -> np.ndarray:
        """
        Generate suicide risk sequences.
        
        Characteristics:
        - Very close to edge (high edge proximity alert)
        - Prolonged loitering at platform edge
        - Irregular pacing
        - Unpredictable movement speed changes
        - Multiple direction changes (nervous behavior)
        - Avoidance of crowds
        - No following patterns
        """
        sequences = []
        for _ in range(num_sequences):
            sequence = np.zeros((self.sequence_length, self.num_features))
            
            # Create a dangerous trajectory pattern
            danger_start = np.random.randint(5, 15)
            
            for t in range(self.sequence_length):
                if t < danger_start:
                    # Normal approach phase
                    sequence[t, 0] = np.random.uniform(15, 35)
                    sequence[t, 1] = np.random.uniform(0, 3)
                else:
                    # Danger phase: very close to edge
                    sequence[t, 0] = np.random.uniform(0, 10)  # Extremely close to edge
                    sequence[t, 1] = np.random.uniform(10, 30)  # Prolonged loitering
                
                sequence[t, 2] = np.random.uniform(2, 8)      # Irregular pacing
                sequence[t, 3] = np.random.uniform(0.1, 3.5)  # Erratic speed
                sequence[t, 4] = np.random.uniform(5, 15)     # High direction changes
                sequence[t, 5] = np.random.uniform(500, 2000) # Isolated
                sequence[t, 6] = np.random.uniform(0, 0.5)    # Minimal interactions
            
            sequences.append(sequence)
        
        return np.array(sequences)

    def generate_pickpocket_sequences(self, num_sequences: int = 150) -> np.ndarray:
        """
        Generate pickpocketing/theft sequences.
        
        Characteristics:
        - Close proximity to victims (low following distance)
        - Persistent following behavior
        - Frequent direction changes
        - Crowd interaction
        - Moderate loitering
        - Unpredictable movement patterns
        """
        sequences = []
        for _ in range(num_sequences):
            sequence = np.zeros((self.sequence_length, self.num_features))
            
            # Create a stalking/following pattern
            target_distance = np.random.uniform(50, 150)
            
            for t in range(self.sequence_length):
                sequence[t, 0] = np.random.uniform(10, 40)    # Variable edge proximity
                sequence[t, 1] = np.random.uniform(1, 10)     # Moderate loitering
                sequence[t, 2] = np.random.uniform(1, 5)      # Active movement
                sequence[t, 3] = np.random.uniform(0.3, 2.0)  # Cautious speed
                sequence[t, 4] = np.random.uniform(2, 10)     # Frequent direction changes
                sequence[t, 5] = target_distance + np.random.normal(0, 20)  # Close following
                sequence[t, 6] = np.random.uniform(0.5, 2.0)  # Crowd interaction
            
            sequences.append(sequence)
        
        return np.array(sequences)

    def generate_security_threat_sequences(self, num_sequences: int = 150) -> np.ndarray:
        """
        Generate security threat/anomaly sequences.
        
        Characteristics:
        - Suspicious movement patterns
        - Frequent stops and starts
        - Multiple loitering incidents
        - Erratic speed changes
        - Excessive direction changes
        - Crowd avoidance
        - Possible edge proximity (suspicious behavior)
        """
        sequences = []
        for _ in range(num_sequences):
            sequence = np.zeros((self.sequence_length, self.num_features))
            
            # Create an erratic pattern
            stop_events = [np.random.randint(5, 25) for _ in range(2)]
            
            for t in range(self.sequence_length):
                # Random stops at various points
                if t in stop_events:
                    sequence[t, 1] = np.random.uniform(15, 40)  # Extended loitering
                    sequence[t, 3] = 0.0  # Stop moving
                else:
                    sequence[t, 1] = np.random.uniform(0, 5)
                    sequence[t, 3] = np.random.uniform(0.5, 3.0)
                
                sequence[t, 0] = np.random.uniform(5, 50)     # Unpredictable edge proximity
                sequence[t, 2] = np.random.uniform(2, 12)     # Erratic pacing
                sequence[t, 4] = np.random.uniform(4, 12)     # High direction changes
                sequence[t, 5] = np.random.uniform(100, 800)  # Variable following
                sequence[t, 6] = np.random.uniform(0, 1.5)    # Some interactions
            
            sequences.append(sequence)
        
        return np.array(sequences)

    def generate_all_data(self) -> dict:
        """Generate all behavioral sequence data."""
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


def create_binary_dataset(normal_sequences: np.ndarray, 
                         threat_sequences: np.ndarray,
                         val_split: float = 0.15,
                         test_split: float = 0.15) -> tuple:
    """
    Create binary classification dataset (Normal vs Threat).
    
    Returns:
        (X_train, y_train, X_val, y_val, X_test, y_test)
    """
    # Combine sequences
    X = np.vstack([normal_sequences, threat_sequences])
    y = np.hstack([np.zeros(len(normal_sequences)), np.ones(len(threat_sequences))])
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    # Split
    n = len(X)
    n_val = int(n * val_split)
    n_test = int(n * test_split)
    n_train = n - n_val - n_test
    
    X_train = X[:n_train]
    y_train = y[:n_train]
    
    X_val = X[n_train:n_train + n_val]
    y_val = y[n_train:n_train + n_val]
    
    X_test = X[n_train + n_val:]
    y_test = y[n_train + n_val:]
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    return X_train, y_train, X_val, y_val, X_test, y_test


def train_model(model_name: str, X_train: np.ndarray, y_train: np.ndarray,
                X_val: np.ndarray, y_val: np.ndarray, output_filename: str):
    """Train and save a binary LSTM classifier."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Training {model_name} classifier...")
    logger.info(f"{'='*60}")
    
    trainer = LSTMTrainer(
        sequence_length=30,
        num_features=7,
    )
    
    history = trainer.execute_training_run(
        X_train, y_train,
        X_val, y_val,
        target_output_filename=output_filename,
        epochs=50,
        batch_size=32
    )
    
    logger.info(f"✓ {model_name} model saved to {output_filename}")
    return history


def main():
    """Main training pipeline."""
    logger.info("="*70)
    logger.info("LSTM Behavior Classification Training Pipeline")
    logger.info("="*70)
    
    # Generate synthetic data
    generator = SyntheticDataGenerator(sequence_length=30, num_features=7)
    data = generator.generate_all_data()
    
    # Ensure model directory exists
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    logger.info(f"Model directory: {settings.MODEL_DIR}")
    
    # Train Suicide Risk Classifier (Normal vs Suicide Risk)
    logger.info("\n" + "="*70)
    logger.info("1. Training Suicide Risk Classifier")
    logger.info("="*70)
    X_train, y_train, X_val, y_val, X_test, y_test = create_binary_dataset(
        data["normal"], data["suicide"]
    )
    train_model(
        "Suicide Risk",
        X_train, y_train, X_val, y_val,
        "suicide_classifier.pt"
    )
    
    # Train Pickpocket Classifier (Normal vs Pickpocketing)
    logger.info("\n" + "="*70)
    logger.info("2. Training Pickpocket Classifier")
    logger.info("="*70)
    X_train, y_train, X_val, y_val, X_test, y_test = create_binary_dataset(
        data["normal"], data["pickpocket"]
    )
    train_model(
        "Pickpocket",
        X_train, y_train, X_val, y_val,
        "pickpocket_classifier.pt"
    )
    
    # Train Anomaly/Security Threat Classifier (Normal vs Security Threat)
    logger.info("\n" + "="*70)
    logger.info("3. Training Anomaly/Security Threat Classifier")
    logger.info("="*70)
    X_train, y_train, X_val, y_val, X_test, y_test = create_binary_dataset(
        data["normal"], data["security_threat"]
    )
    train_model(
        "Security Threat/Anomaly",
        X_train, y_train, X_val, y_val,
        "anomaly_classifier.pt"
    )
    
    logger.info("\n" + "="*70)
    logger.info("✓ All models trained and saved successfully!")
    logger.info("="*70)
    logger.info(f"Models saved in: {settings.MODEL_DIR}")
    logger.info("\nGenerated models:")
    logger.info("  - suicide_classifier.pt")
    logger.info("  - pickpocket_classifier.pt")
    logger.info("  - anomaly_classifier.pt")


if __name__ == "__main__":
    main()
