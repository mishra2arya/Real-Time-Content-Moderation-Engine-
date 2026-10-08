"""Fine-tuning pipeline for DistilBERT Sequence Classification."""

import argparse
import csv
import json
import os
import random
import sys
import time
from typing import Dict, List, Optional, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import numpy as np
import torch
import torch.nn as nn
import yaml
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)


def set_seed(seed: int = 42) -> None:
    """Ensure deterministic execution across runs."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class ModerationDataset(Dataset):
    """PyTorch Dataset for text moderation classification."""

    def __init__(
        self,
        csv_path: str,
        tokenizer: AutoTokenizer,
        max_length: int = 128,
    ):
        self.texts: List[str] = []
        self.labels: List[int] = []
        self.tokenizer = tokenizer
        self.max_length = max_length

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.texts.append(row["cleaned_text"])
                self.labels.append(int(row["label"]))

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        text = self.texts[idx]
        label = self.labels[idx]

        encoded = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long),
        }


def compute_metrics(preds: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    """Compute accuracy, precision, recall, and F1."""
    tp = np.sum((preds == 1) & (labels == 1))
    fp = np.sum((preds == 1) & (labels == 0))
    fn = np.sum((preds == 0) & (labels == 1))
    tn = np.sum((preds == 0) & (labels == 0))

    accuracy = (tp + tn) / max(len(labels), 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * (precision * recall) / max(precision + recall, 1e-8)
    fpr = fp / max(fp + tn, 1)

    return {
        "accuracy": float(round(accuracy, 4)),
        "precision": float(round(precision, 4)),
        "recall": float(round(recall, 4)),
        "f1": float(round(f1, 4)),
        "fpr": float(round(fpr, 4)),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
    }


def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
) -> Tuple[float, Dict[str, float]]:
    """Evaluate model on validation/test dataloader."""
    model.eval()
    total_loss = 0.0
    criterion = nn.CrossEntropyLoss()
    all_preds: List[int] = []
    all_labels: List[int] = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            loss = criterion(logits, labels)
            total_loss += loss.item()

            preds = torch.argmax(logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / max(len(dataloader), 1)
    metrics = compute_metrics(np.array(all_preds), np.array(all_labels))
    metrics["loss"] = float(round(avg_loss, 4))
    return avg_loss, metrics


def train(
    config_path: str = "configs/training_config.yaml",
    output_dir: Optional[str] = None,
    epochs: Optional[int] = None,
    batch_size: Optional[int] = None,
    max_length: Optional[int] = None,
    learning_rate: Optional[float] = None,
    freeze_backbone: bool = False,
) -> Dict[str, any]:
    """Execute training pipeline."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    seed = config.get("seed", 42)
    set_seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")

    out_dir = output_dir or config.get("output_dir", "models/pytorch")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Load Tokenizer & Model
    model_name = config.get("model_name", "distilbert-base-uncased")
    seq_max_length = max_length or config.get("max_length", 128)
    num_labels = config.get("num_labels", 2)

    print(f"Loading base tokenizer and model from '{model_name}'...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)  # nosec B615
    model = AutoModelForSequenceClassification.from_pretrained(  # nosec B615
        model_name,
        num_labels=num_labels,
    )
    model.to(device)

    # 2. Prepare Datasets & DataLoaders
    train_path = config.get("train_data_path", "data/processed/train.csv")
    val_path = config.get("val_data_path", "data/processed/val.csv")

    train_dataset = ModerationDataset(train_path, tokenizer, seq_max_length)
    val_dataset = ModerationDataset(val_path, tokenizer, seq_max_length)

    b_size = batch_size or config.get("batch_size", 32)
    eval_b_size = config.get("eval_batch_size", 64)

    train_loader = DataLoader(train_dataset, batch_size=b_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=eval_b_size, shuffle=False)

    print(
        f"Loaded {len(train_dataset)} training items, {len(val_dataset)} validation items."
    )

    # 3. Calculate Class Weights for Imbalance
    labels_list = train_dataset.labels
    neg_count = sum(1 for l in labels_list if l == 0)
    pos_count = sum(1 for l in labels_list if l == 1)
    total_samples = len(labels_list)
    weight_0 = total_samples / (2.0 * max(neg_count, 1))
    weight_1 = total_samples / (2.0 * max(pos_count, 1))
    class_weights = torch.tensor([weight_0, weight_1], dtype=torch.float).to(device)
    print(
        f"Class counts: non_toxic={neg_count}, toxic={pos_count}. Loss weights: [0: {weight_0:.2f}, 1: {weight_1:.2f}]"
    )

    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # 4. Optimizer & LR Scheduler
    num_train_epochs = epochs or config.get("num_epochs", 3)
    total_steps = len(train_loader) * num_train_epochs
    warmup_steps = int(total_steps * config.get("warmup_ratio", 0.1))

    if freeze_backbone:
        print("Freezing DistilBERT transformer backbone (fast classifier head training mode)...")
        for param in model.distilbert.parameters():
            param.requires_grad = False
        lr = learning_rate if learning_rate is not None else 1.0e-3
        optimizer = torch.optim.AdamW(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=lr,
            weight_decay=config.get("weight_decay", 0.01),
        )
    else:
        lr = (
            learning_rate
            if learning_rate is not None
            else float(config.get("learning_rate", 3.0e-5))
        )
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=lr,
            weight_decay=config.get("weight_decay", 0.01),
        )

    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    # 5. Training Loop
    best_val_f1 = 0.0
    best_metrics = {}
    patience = config.get("early_stopping_patience", 2)
    patience_counter = 0

    saved_any_checkpoint = False
    print("\n" + "=" * 60)
    print(f"STARTING DISTILBERT FINE-TUNING ({num_train_epochs} Epochs)")
    print("=" * 60)

    start_time = time.time()

    for epoch in range(1, num_train_epochs + 1):
        model.train()
        total_train_loss = 0.0
        epoch_start = time.time()

        for step, batch in enumerate(train_loader, 1):
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = criterion(outputs.logits, labels)
            loss.backward()

            nn.utils.clip_grad_norm_(
                model.parameters(), config.get("max_grad_norm", 1.0)
            )
            optimizer.step()
            scheduler.step()

            total_train_loss += loss.item()

        avg_train_loss = total_train_loss / len(train_loader)
        val_loss, val_metrics = evaluate(model, val_loader, device)
        epoch_dur = time.time() - epoch_start

        print(
            f"Epoch {epoch}/{num_train_epochs} [{epoch_dur:.1f}s] - "
            f"Train Loss: {avg_train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Precision: {val_metrics['precision']:.4f} | "
            f"Val Recall: {val_metrics['recall']:.4f} | "
            f"Val F1: {val_metrics['f1']:.4f} | "
            f"Val FPR: {val_metrics['fpr']:.4f}"
        )

        # Checkpoint Best Model
        if val_metrics["f1"] > best_val_f1 or not saved_any_checkpoint:
            best_val_f1 = val_metrics["f1"]
            best_metrics = val_metrics
            saved_any_checkpoint = True
            patience_counter = 0

            print(
                f"  ★ New best validation F1 ({best_val_f1:.4f}). Saving model to {out_dir}..."
            )
            model.save_pretrained(out_dir)
            tokenizer.save_pretrained(out_dir)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping triggered at epoch {epoch}.")
                break

    total_time = time.time() - start_time
    print("=" * 60)
    print(f"Training completed in {total_time:.2f} seconds.")
    print(f"Best Validation Metrics: {best_metrics}")

    # Save training summary metadata
    metadata = {
        "model_name": model_name,
        "num_labels": num_labels,
        "max_length": seq_max_length,
        "seed": seed,
        "device": str(device),
        "total_train_time_seconds": round(total_time, 2),
        "best_val_metrics": best_metrics,
        "freeze_backbone": freeze_backbone,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(
        os.path.join(out_dir, "training_metadata.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(metadata, f, indent=2)

    return best_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train DistilBERT moderation classifier."
    )
    parser.add_argument("--config", type=str, default="configs/training_config.yaml")
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--max_length", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--freeze_backbone", action="store_true")
    args = parser.parse_args()

    train(
        config_path=args.config,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        max_length=args.max_length,
        learning_rate=args.lr,
        freeze_backbone=args.freeze_backbone,
    )
