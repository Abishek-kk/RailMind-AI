import numpy as np
from typing import List

def preprocess_sequence(sequence: List[List[float]], target_length: int = 30) -> np.ndarray:
    """
    Pads or truncates historical list inputs to output valid multidimensional numpy arrays.
    Pads tracking sequences that are too short with zeros at the front.
    """
    processed_matrix = np.array(sequence)
    current_length = len(processed_matrix)
    
    if current_length < target_length:
        # Pre-pad empty timestamps up to requirements threshold limits
        padding_mask = np.zeros((target_length - current_length, processed_matrix.shape[1]))
        processed_matrix = np.vstack((padding_mask, processed_matrix))
    elif current_length > target_length:
        # Discard older tracking rows to capture immediate operational context windows
        processed_matrix = processed_matrix[-target_length:]
        
    # Expand array dimensions to append required network Batch parameters: (1, 30, 34)
    return np.expand_dims(processed_matrix, axis=0)