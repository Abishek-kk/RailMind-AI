"""Extract features from pose keypoints for LSTM training"""
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.features.feature_extractor import FeatureExtractor
from app.lstm.preprocessor import LSTMPreprocessor

def extract_features_from_dataset():
    """Extract features from all behavior categories"""
    dataset_dir = Path("../datasets")
    output_dir = Path("../datasets")
    
    feature_extractor = FeatureExtractor()
    preprocessor = LSTMPreprocessor()
    
    behavior_types = [
        "normal",
        "suicide_risk", 
        "pickpocketing",
        "loitering",
        "track_intrusion",
        "suspicious_following"
    ]
    
    all_features = []
    all_labels = []
    
    for idx, behavior_type in enumerate(behavior_types):
        behavior_dir = dataset_dir / behavior_type
        print(f"Extracting features from {behavior_type}...")
        
        if behavior_dir.exists():
            # Load and process files
            for file in behavior_dir.glob("*.npy"):
                data = np.load(file)
                features = feature_extractor.extract_features(data)
                all_features.append(features)
                all_labels.append(idx)
        
        print(f"  Processed {behavior_type}")
    
    # Save extracted features
    all_features = np.array(all_features)
    all_labels = np.array(all_labels)
    
    # Split train/test
    split_idx = int(0.8 * len(all_features))
    
    np.save(output_dir / "train_sequences.npy", all_features[:split_idx])
    np.save(output_dir / "train_labels.npy", all_labels[:split_idx])
    np.save(output_dir / "test_sequences.npy", all_features[split_idx:])
    np.save(output_dir / "test_labels.npy", all_labels[split_idx:])
    
    print(f"Features saved: train={all_features[:split_idx].shape}, test={all_features[split_idx:].shape}")

if __name__ == "__main__":
    extract_features_from_dataset()
