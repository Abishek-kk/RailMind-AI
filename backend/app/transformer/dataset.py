from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import Dataset

FEATURE_KEYS: list[str] = [
    "edge_proximity",
    "loitering_time",
    "pacing_count",
    "movement_speed",
    "direction_changes",
    "following_distance",
    "crowd_interactions",
]

LABEL_MAP: dict[str, int] = {
    "Normal": 0,
    "Suicide Risk": 1,
    "Pickpocketing": 2,
    "Security Threat": 3,
}

CLASS_NAMES: list[str] = ["Normal", "Suicide Risk", "Pickpocketing", "Security Threat"]
SEQ_LEN: int = 30
N_FEATURES: int = 7


class _SequenceSplitDataset(Dataset):
    """Simple dataset wrapper for a single split of scaled sequences."""

    def __init__(self, sequences: np.ndarray, labels: np.ndarray) -> None:
        self.sequences = sequences.astype(np.float32, copy=False)
        self.labels = labels.astype(np.int64, copy=False)

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        sequence = torch.tensor(self.sequences[index], dtype=torch.float32)
        label = torch.tensor(self.labels[index], dtype=torch.long)
        return sequence, label


class BehaviourSequenceDataset(Dataset):
    """Dataset for railway behaviour classification over 30-second windows.

    Each sample is a sequence of 30 timesteps with 7 behavioural features. The
    dataset fits a StandardScaler on the training split only, saves it to disk,
    and exposes train/validation split datasets for model training.
    """

    def __init__(
        self,
        data_path: str | Path,
        scaler_path: str | Path | None = None,
        val_split: float = 0.2,
        seed: int = 42,
        split: str = "train",
    ) -> None:
        self.data_path = Path(data_path)
        self.scaler_path = Path(scaler_path) if scaler_path is not None else self.data_path.parent / "feature_scaler.pkl"
        self.val_split = val_split
        self.seed = seed
        self.split = split
        self.label_map = LABEL_MAP
        self.class_names = CLASS_NAMES

        sequences, labels = self._load_jsonl_data(self.data_path)
        self.sequences = sequences
        self.labels = labels

        train_idx, val_idx = train_test_split(
            np.arange(len(sequences)),
            test_size=self.val_split,
            stratify=self.labels,
            random_state=self.seed,
        )

        train_sequences = sequences[train_idx]
        val_sequences = sequences[val_idx]
        train_labels = labels[train_idx]
        val_labels = labels[val_idx]

        train_features = train_sequences.reshape(-1, N_FEATURES)
        scaler = StandardScaler()
        scaler.fit(train_features)
        self.scaler = scaler

        self.scaler_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.scaler, self.scaler_path)

        scaled_train = self._apply_scaler(train_sequences)
        scaled_val = self._apply_scaler(val_sequences)

        self.train_dataset = _SequenceSplitDataset(scaled_train, train_labels)
        self.val_dataset = _SequenceSplitDataset(scaled_val, val_labels)

        if self.split == "train":
            self._active_dataset = self.train_dataset
        elif self.split == "val":
            self._active_dataset = self.val_dataset
        else:
            raise ValueError(f"Unsupported split '{split}'. Expected 'train' or 'val'.")

    @staticmethod
    def _load_jsonl_data(data_path: Path) -> tuple[np.ndarray, np.ndarray]:
        if not data_path.exists():
            raise FileNotFoundError(f"JSONL data file not found: {data_path}")

        rows: list[dict[str, Any]] = []
        with data_path.open("r", encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:  # pragma: no cover - defensive error handling
                    raise ValueError(f"Invalid JSON on line {line_number}: {line}") from exc
                rows.append(row)

        if not rows:
            raise ValueError(f"No JSON rows found in {data_path}")

        sequences: list[np.ndarray] = []
        labels: list[int] = []
        for row in rows:
            if "features" not in row or "label" not in row:
                raise ValueError("Each JSON line must contain 'features' and 'label'.")
            features = row["features"]
            if len(features) != SEQ_LEN:
                raise ValueError(f"Expected exactly {SEQ_LEN} feature vectors per sample, got {len(features)}.")

            label_name = row["label"]
            if label_name not in LABEL_MAP:
                raise ValueError(f"Unsupported label '{label_name}'. Allowed labels: {sorted(LABEL_MAP)}")

            sequence = np.zeros((SEQ_LEN, N_FEATURES), dtype=np.float32)
            for step_index, feature_dict in enumerate(features):
                if not isinstance(feature_dict, dict):
                    raise ValueError(f"Feature row {step_index} is not a dict.")
                for feature_index, key in enumerate(FEATURE_KEYS):
                    sequence[step_index, feature_index] = float(feature_dict[key])
            sequences.append(sequence)
            labels.append(LABEL_MAP[label_name])

        return np.stack(sequences), np.asarray(labels, dtype=np.int64)

    def _apply_scaler(self, sequences: np.ndarray) -> np.ndarray:
        flat = sequences.reshape(-1, N_FEATURES)
        scaled = self.scaler.transform(flat)
        return scaled.reshape(sequences.shape[0], SEQ_LEN, N_FEATURES)

    def __len__(self) -> int:
        return len(self._active_dataset)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self._active_dataset[index]

    @property
    def scaler_path_str(self) -> str:
        return str(self.scaler_path)
