"""
LSTM Temporal Behavior Modeling Package
Exposes sequence preprocessors, coordinate normalizers, and the master prediction engine.
"""

from .preprocessor import preprocess_sequence
from .feature_extractor import extract_pose_features
from .sequence_builder import SequenceBuilder

try:
    from .model import build_lstm_model
except ImportError:
    build_lstm_model = None

try:
    from .predictor import LSTMPredictor
except ImportError:
    LSTMPredictor = None

__all__ = [
    "build_lstm_model",
    "preprocess_sequence",
    "extract_pose_features",
    "LSTMPredictor",
    "SequenceBuilder",
]