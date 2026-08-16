from __future__ import annotations

import argparse
import random
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.metrics import classification_report
from torch import nn
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

from .dataset import BehaviourSequenceDataset, CLASS_NAMES
from .model import TemporalTransformer


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def evaluate(model: TemporalTransformer, loader: DataLoader, criterion: nn.Module, device: torch.device) -> tuple[float, float, list[int], list[int]]:
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    all_preds: list[int] = []
    all_targets: list[int] = []

    with torch.no_grad():
        for sequence_batch, label_batch in loader:
            sequence_batch = sequence_batch.to(device)
            label_batch = label_batch.to(device)
            logits = model(sequence_batch)
            loss = criterion(logits, label_batch)
            total_loss += loss.item() * label_batch.size(0)
            pred = logits.argmax(dim=1)
            correct += (pred == label_batch).sum().item()
            total += label_batch.size(0)
            all_preds.extend(pred.detach().cpu().tolist())
            all_targets.extend(label_batch.detach().cpu().tolist())

    accuracy = correct / max(total, 1)
    mean_loss = total_loss / max(total, 1)
    return mean_loss, accuracy, all_targets, all_preds


def train_model(args: argparse.Namespace) -> None:
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = BehaviourSequenceDataset(
        data_path=args.data_path,
        scaler_path=output_dir / "feature_scaler.pkl",
        val_split=args.val_split,
    )

    train_loader = DataLoader(dataset.train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(dataset.val_dataset, batch_size=args.batch_size, shuffle=False)

    model = TemporalTransformer()
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = Adam(model.parameters(), lr=args.lr)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)

    best_val_accuracy = -1.0

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        correct = 0
        total = 0

        for sequence_batch, label_batch in train_loader:
            sequence_batch = sequence_batch.to(device)
            label_batch = label_batch.to(device)

            optimizer.zero_grad()
            logits = model(sequence_batch)
            loss = criterion(logits, label_batch)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * label_batch.size(0)
            pred = logits.argmax(dim=1)
            correct += (pred == label_batch).sum().item()
            total += label_batch.size(0)

        train_loss = train_loss / max(total, 1)
        train_accuracy = correct / max(total, 1)

        val_loss, val_accuracy, val_targets, val_preds = evaluate(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        print(f"Epoch {epoch + 1}/{args.epochs} | train_loss={train_loss:.4f} train_acc={train_accuracy:.4f} | val_loss={val_loss:.4f} val_acc={val_accuracy:.4f}")

        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            torch.save(model.state_dict(), output_dir / "behaviour_transformer.pt")
            joblib_path = output_dir / "feature_scaler.pkl"
            joblib.dump(dataset.scaler, joblib_path)

    model.eval()
    _, _, val_targets, val_preds = evaluate(model, val_loader, criterion, device)
    print(classification_report(
        val_targets,
        val_preds,
        target_names=CLASS_NAMES,
        digits=4,
    ))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a temporal transformer for railway behaviour classification.")
    parser.add_argument("--data_path", type=str, required=True, help="Path to the JSONL training file.")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate.")
    parser.add_argument("--val_split", type=float, default=0.2, help="Validation split proportion.")
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "transformer" / "saved_models"),
        help="Directory to save model and scaler artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    train_model(parse_args())


if __name__ == "__main__":
    main()
