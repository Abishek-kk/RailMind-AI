import os
import sys
import logging

import torch

script_dir = os.path.dirname(__file__)
sys.path.insert(0, script_dir)
from model import build_lstm_model

logger = logging.getLogger("railmind")
logging.basicConfig(level=logging.INFO)

MODEL_DIR = os.path.join(script_dir, "saved_models")
MODEL_FILES = [
    "suicide_classifier.pt",
    "pickpocket_classifier.pt",
    "anomaly_classifier.pt",
]

SEQUENCE_LENGTH = 30
NUM_FEATURES = 7


def create_default_model(model_file_path: str):
    os.makedirs(os.path.dirname(model_file_path), exist_ok=True)
    model = build_lstm_model(sequence_length=SEQUENCE_LENGTH, num_features=NUM_FEATURES)
    torch.save(model.state_dict(), model_file_path)
    logger.info("Saved default LSTM model: %s", model_file_path)


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for model_file in MODEL_FILES:
        model_file_path = os.path.join(MODEL_DIR, model_file)
        if os.path.exists(model_file_path):
            logger.info("Model already exists, skipping: %s", model_file_path)
            continue
        create_default_model(model_file_path)

    logger.info("Default LSTM model generation complete.")


if __name__ == "__main__":
    main()
