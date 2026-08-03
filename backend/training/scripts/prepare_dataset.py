"""Prepare dataset for transformer training"""
from pathlib import Path
import numpy as np

BEHAVIOR_TYPES = {
    "normal": 0,
    "suicide_risk": 1,
    "pickpocketing": 2,
    "loitering": 3,
    "track_intrusion": 4,
    "suspicious_following": 5,
}

DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets"
OUTPUT_DIR = DATASET_DIR


def prepare_sequences():
    """Prepare training sequences from available dataset files."""
    all_sequences = []
    all_labels = []

    for behavior_type, label in BEHAVIOR_TYPES.items():
        behavior_dir = DATASET_DIR / behavior_type
        print(f"Processing {behavior_type} data from {behavior_dir}")
        if not behavior_dir.exists():
            print(f"  skipping missing folder: {behavior_dir}")
            continue

        for file_path in sorted(behavior_dir.glob("*.npy")):
            try:
                data = np.load(str(file_path))
                if data.size == 0:
                    continue
                all_sequences.append(data)
                all_labels.append(label)
            except Exception as exc:
                print(f"  failed to load {file_path}: {exc}")

    if not all_sequences:
        raise RuntimeError("No sequence files found in dataset directories")

    all_sequences = np.asarray(all_sequences, dtype=object)
    sequence_lengths = [seq.shape[0] for seq in all_sequences]
    max_length = max(sequence_lengths)
    feature_dim = all_sequences[0].shape[1] if all_sequences[0].ndim > 1 else 1

    padded_sequences = np.zeros((len(all_sequences), max_length, feature_dim), dtype=float)
    for index, seq in enumerate(all_sequences):
        seq_array = np.asarray(seq, dtype=float)
        padded_sequences[index, : seq_array.shape[0], : seq_array.shape[1]] = seq_array

    labels = np.asarray(all_labels, dtype=int)
    split_idx = int(0.8 * len(padded_sequences))
    np.save(OUTPUT_DIR / "train_sequences.npy", padded_sequences[:split_idx])
    np.save(OUTPUT_DIR / "train_labels.npy", labels[:split_idx])
    np.save(OUTPUT_DIR / "test_sequences.npy", padded_sequences[split_idx:])
    np.save(OUTPUT_DIR / "test_labels.npy", labels[split_idx:])

    print(f"Saved train/test sequences to {OUTPUT_DIR}")
    print(f"Train count: {split_idx}, Test count: {len(padded_sequences) - split_idx}")


def load_video_frames(video_path):
    """Load frames from video file"""
    raise NotImplementedError("Video loading is not implemented in this script")


def extract_poses_from_frames(frames):
    """Extract pose keypoints from video frames"""
    raise NotImplementedError("Pose extraction is not implemented in this script")


if __name__ == "__main__":
    prepare_sequences()
