"""LSTM model tests"""
import os
import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.lstm.sequence_builder import SequenceBuilder


def test_lstm_training():
    """Test LSTM training"""
    builder = SequenceBuilder(sequence_length=5)
    for i in range(5):
        sequence = builder.add_frame("track_1", [float(i), float(i + 1)])
    assert builder.is_sequence_complete("track_1")
    assert builder.get_sequence("track_1").shape == (5, 2)


def test_lstm_prediction():
    """Test LSTM prediction"""
    builder = SequenceBuilder(sequence_length=3)
    builder.add_frame("track_2", [1.0, 2.0])
    builder.add_frame("track_2", [2.0, 3.0])
    seq = builder.get_sequence("track_2")
    assert isinstance(seq, np.ndarray)
    assert seq.shape == (3, 2)
