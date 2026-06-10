import os
os.environ.setdefault("KERAS_BACKEND", "torch")
from keras_core.models import Sequential
from keras_core.layers import LSTM, Dense, Dropout

def build_lstm_model(sequence_length: int = 30, num_features: int = 7, num_classes: int = 1) -> Sequential:
    """
    Builds a stacked LSTM neural network for temporal skeletal sequence classification.
    Input Shape: (Batch_Size, Sequence_Length, Num_Features) -> e.g., (None, 30, 34)
    """
    model = Sequential([
        # Layer 1: Processes individual frame vectors sequentially, maintaining sequence memory
        LSTM(64, input_shape=(sequence_length, num_features), return_sequences=True),
        Dropout(0.2),
        
        # Layer 2: Condenses temporal outputs into a single aggregated feature vector
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        
        # Dense Layer Context Mapping
        Dense(16, activation='relu'),
        
        # Classification Output Layer (Sigmoid output boundary for binary anomaly risk probabilities)
        Dense(num_classes, activation='sigmoid' if num_classes == 1 else 'softmax')
    ])
    
    loss_function = 'binary_crossentropy' if num_classes == 1 else 'categorical_crossentropy'
    
    model.compile(
        optimizer='adam',
        loss=loss_function,
        metrics=['accuracy']
    )
    
    return model