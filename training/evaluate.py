"""Comprehensive test set evaluation and metrics reporting."""

import argparse
import csv
import json
import os
import sys
from typing import Dict, List

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import numpy as np
import torch
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.moderation.labels import ID2LABEL


def evaluate_model(
    model_dir: str = "models/pytorch",
    test_csv: str = "data/processed/test.csv",
    output_dir: str = "models/pytorch",
    max_length: int = 128,
    batch_size: int = 64,
) -> Dict[str, any]:
    """Run full evaluation on the test dataset and generate reports."""
    os.makedirs(output_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"Loading trained model and tokenizer from '{model_dir}'...")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)  # nosec B615
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)  # nosec B615
    model.to(device)
    model.eval()

    # Load test dataset
    texts: List[str] = []
    labels: List[int] = []
    with open(test_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["cleaned_text"])
            labels.append(int(row["label"]))

    print(f"Loaded {len(texts)} test examples from {test_csv}.")

    all_preds: List[int] = []
    all_probs: List[float] = []

    # Inference loop
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        encoded = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            logits = model(**encoded).logits
            probs = torch.softmax(logits, dim=1)
            preds = torch.argmax(probs, dim=1)

            all_preds.extend(preds.cpu().numpy().tolist())
            all_probs.extend(probs[:, 1].cpu().numpy().tolist())

    y_true = np.array(labels)
    y_pred = np.array(all_preds)

    # 1. Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # 2. Metrics calculation
    accuracy = float((tp + tn) / max(len(y_true), 1))
    precision_toxic = float(tp / max(tp + fp, 1))
    recall_toxic = float(tp / max(tp + fn, 1))
    f1_toxic = float(
        2 * precision_toxic * recall_toxic / max(precision_toxic + recall_toxic, 1e-8)
    )

    precision_nontoxic = float(tn / max(tn + fn, 1))
    recall_nontoxic = float(tn / max(tn + fp, 1))

    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted"))

    fpr = float(fp / max(fp + tn, 1))
    fnr = float(fn / max(fn + tp, 1))

    # Target comparison
    precision_target_met = precision_toxic >= 0.91
    fpr_target_met = fpr <= 0.05

    metrics = {
        "dataset_size": len(y_true),
        "accuracy": round(accuracy, 4),
        "precision": round(precision_toxic, 4),
        "recall": round(recall_toxic, 4),
        "f1": round(f1_toxic, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "per_class": {
            "non_toxic": {
                "precision": round(precision_nontoxic, 4),
                "recall": round(recall_nontoxic, 4),
                "support": int(tn + fp),
            },
            "toxic": {
                "precision": round(precision_toxic, 4),
                "recall": round(recall_toxic, 4),
                "support": int(tp + fn),
            },
        },
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
        "targets": {
            "precision_target_91_pct": {
                "target": 0.91,
                "measured": round(precision_toxic, 4),
                "status": "PASS" if precision_target_met else "FAIL",
            },
            "fpr_target_5_pct": {
                "target": 0.05,
                "measured": round(fpr, 4),
                "status": "PASS" if fpr_target_met else "FAIL",
            },
        },
    }

    # Save metrics.json
    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Save confusion_matrix.csv
    cm_path = os.path.join(output_dir, "confusion_matrix.csv")
    with open(cm_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["actual", "pred_non_toxic", "pred_toxic"])
        writer.writerow(["actual_non_toxic", tn, fp])
        writer.writerow(["actual_toxic", fn, tp])

    # Save classification_report.txt
    target_names = [ID2LABEL[0], ID2LABEL[1]]
    report_text = classification_report(
        y_true, y_pred, target_names=target_names, digits=4
    )
    report_path = os.path.join(output_dir, "classification_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("CONTENT MODERATION CLASSIFICATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(report_text)
        f.write("\n\nCONFUSION MATRIX:\n")
        f.write(f"TN: {tn} | FP: {fp}\n")
        f.write(f"FN: {fn} | TP: {tp}\n\n")
        f.write(
            f"False Positive Rate (FPR): {fpr:.4f} (Target < 0.05: {metrics['targets']['fpr_target_5_pct']['status']})\n"
        )
        f.write(
            f"Toxic Precision:          {precision_toxic:.4f} (Target >= 0.91: {metrics['targets']['precision_target_91_pct']['status']})\n"
        )

    print("\n" + "=" * 60)
    print("MODEL EVALUATION SUMMARY ON TEST SET")
    print("=" * 60)
    print(report_text)
    print(f"Accuracy:                {accuracy * 100:.2f}%")
    print(
        f"Toxic Precision:         {precision_toxic * 100:.2f}% (Target >= 91%: {metrics['targets']['precision_target_91_pct']['status']})"
    )
    print(f"Toxic Recall:            {recall_toxic * 100:.2f}%")
    print(f"Toxic F1:                {f1_toxic * 100:.2f}%")
    print(
        f"False Positive Rate:     {fpr * 100:.2f}% (Target < 5%: {metrics['targets']['fpr_target_5_pct']['status']})"
    )
    print(f"False Negative Rate:     {fnr * 100:.2f}%")
    print(f"Confusion Matrix:        TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"Saved metrics:           {metrics_path}")
    print(f"Saved confusion matrix:  {cm_path}")
    print(f"Saved report:            {report_path}")
    print("=" * 60 + "\n")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate model on test dataset.")
    parser.add_argument("--model_dir", type=str, default="models/pytorch")
    parser.add_argument("--test_csv", type=str, default="data/processed/test.csv")
    parser.add_argument("--output_dir", type=str, default="models/pytorch")
    args = parser.parse_args()

    evaluate_model(
        model_dir=args.model_dir,
        test_csv=args.test_csv,
        output_dir=args.output_dir,
    )
