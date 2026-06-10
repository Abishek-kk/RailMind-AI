import os
import numpy as np
os.environ.setdefault("KERAS_BACKEND", "torch")

try:
    from keras_core.callbacks import EarlyStopping, ModelCheckpoint
except ImportError:
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from app.lstm.model import build_lstm_model
from app.core.config import settings

class LSTMTrainer:
    def __init__(self, sequence_length: int = 30, num_features: int = 34):
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.model = build_lstm_model(sequence_length, num_features)

    def execute_training_run(self, X_train: np.ndarray, y_train: np.ndarray, 
                               X_val: np.ndarray, y_val: np.ndarray, 
                               target_output_filename: str, epochs: int = 40, batch_size: int = 32):
        """
        Compiles dataset inputs, runs the training loop, and saves the top-performing
        epoch matrix to disk.
        """
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        destination_save_path = os.path.join(settings.MODEL_DIR, target_output_filename)

        # EarlyStopping prevents model overfitting if training loss values plateau
        training_callbacks = [
            EarlyStopping(monitor='val_loss', patience=6, restore_best_weights=True),
            ModelCheckpoint(destination_save_path, monitor='val_loss', save_best_only=True, verbose=1)
        ]

        history_metrics = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=training_callbacks,
            verbose=1
        )
        
        return history_metrics