"""Latency benchmark comparing PyTorch vs ONNX Runtime vs FastAPI API latency."""

import argparse
import json
import os
import sys
import time
from typing import Dict, List

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import numpy as np
import onnxruntime as ort
import torch
from fastapi.testclient import TestClient
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.main import app


def compute_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
    """Calculate statistical distribution percentiles."""
    arr = np.array(latencies_ms)
    return {
        "p50": float(round(np.percentile(arr, 50), 3)),
        "p90": float(round(np.percentile(arr, 90), 3)),
        "p95": float(round(np.percentile(arr, 95), 3)),
        "p99": float(round(np.percentile(arr, 99), 3)),
        "mean": float(round(np.mean(arr), 3)),
        "min": float(round(np.min(arr), 3)),
        "max": float(round(np.max(arr), 3)),
        "std": float(round(np.std(arr), 3)),
    }


def benchmark_latency(
    model_pytorch_dir: str = "models/pytorch",
    model_onnx_path: str = "models/onnx/model.onnx",
    num_runs: int = 100,
    output_dir: str = "benchmarks",
) -> Dict[str, any]:
    """Execute latency benchmarks across PyTorch, ONNX Runtime, and FastAPI."""
    os.makedirs(output_dir, exist_ok=True)
    device = torch.device("cpu")

    test_sentences = [
        "Great job on the presentation today, really enjoyed the key takeaways.",
        "You are an idiot and nobody likes your terrible ideas.",
        "Can someone explain how to configure async dynamic batching in Python?",
        "I will hunt you down and destroy your account.",
        "The weather is wonderful and sunny outside today.",
    ]

    print("=" * 65)
    print(f"BENCHMARKING LATENCY ACROSS RUNTIMES ({num_runs} iterations each)")
    print("=" * 65)

    # 1. PyTorch / Transformers Inference
    print("Loading PyTorch model...")
    tokenizer = AutoTokenizer.from_pretrained(model_pytorch_dir)
    pytorch_model = AutoModelForSequenceClassification.from_pretrained(
        model_pytorch_dir
    )
    pytorch_model.to(device)
    pytorch_model.eval()

    # PyTorch Warmup
    for _ in range(10):
        enc = tokenizer("Warmup sentence", return_tensors="pt")
        with torch.no_grad():
            pytorch_model(**enc)

    pytorch_latencies = []
    for i in range(num_runs):
        prompt = test_sentences[i % len(test_sentences)]
        enc = tokenizer(
            prompt, max_length=128, truncation=True, padding=True, return_tensors="pt"
        )
        t0 = time.perf_counter()
        with torch.no_grad():
            _ = pytorch_model(**enc)
        pytorch_latencies.append((time.perf_counter() - t0) * 1000.0)

    pytorch_stats = compute_percentiles(pytorch_latencies)
    print(
        f"PyTorch CPU:   P50={pytorch_stats['p50']}ms | P95={pytorch_stats['p95']}ms | P99={pytorch_stats['p99']}ms | Mean={pytorch_stats['mean']}ms"
    )

    # 2. ONNX Runtime Inference
    print("Loading ONNX Runtime engine...")
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.intra_op_num_threads = 4
    session = ort.InferenceSession(
        model_onnx_path, opts, providers=["CPUExecutionProvider"]
    )

    # ONNX Warmup
    for _ in range(10):
        tokens = tokenizer("Warmup sentence", return_tensors="np")
        session.run(
            ["logits"],
            {
                "input_ids": tokens["input_ids"].astype(np.int64),
                "attention_mask": tokens["attention_mask"].astype(np.int64),
            },
        )

    onnx_latencies = []
    for i in range(num_runs):
        prompt = test_sentences[i % len(test_sentences)]
        tokens = tokenizer(
            prompt, max_length=128, truncation=True, padding=True, return_tensors="np"
        )
        ort_inputs = {
            "input_ids": tokens["input_ids"].astype(np.int64),
            "attention_mask": tokens["attention_mask"].astype(np.int64),
        }
        t0 = time.perf_counter()
        _ = session.run(["logits"], ort_inputs)
        onnx_latencies.append((time.perf_counter() - t0) * 1000.0)

    onnx_stats = compute_percentiles(onnx_latencies)
    speedup = round(pytorch_stats["mean"] / max(onnx_stats["mean"], 1e-4), 2)
    print(
        f"ONNX Runtime:  P50={onnx_stats['p50']}ms | P95={onnx_stats['p95']}ms | P99={onnx_stats['p99']}ms | Mean={onnx_stats['mean']}ms"
    )
    print(f"Speedup Factor (PyTorch vs ONNX): {speedup}x")

    # 3. FastAPI Endpoint End-to-End Latency
    print("Testing FastAPI Client End-to-End Latency...")
    api_latencies = []
    with TestClient(app) as client:
        # Warmup
        client.post("/moderate", json={"text": "Warmup request"})

        for i in range(num_runs):
            prompt = test_sentences[i % len(test_sentences)]
            t0 = time.perf_counter()
            resp = client.post(
                "/moderate", json={"text": prompt, "text_id": f"bench-{i}"}
            )
            elapsed = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200
            api_latencies.append(elapsed)

    api_stats = compute_percentiles(api_latencies)
    target_met = api_stats["p95"] < 48.0
    print(
        f"FastAPI API:   P50={api_stats['p50']}ms | P95={api_stats['p95']}ms | P99={api_stats['p99']}ms | Mean={api_stats['mean']}ms"
    )
    print(
        f"Target Latency (<48ms at P95): {'ACHIEVED' if target_met else 'NOT ACHIEVED'}"
    )

    results = {
        "num_runs": num_runs,
        "pytorch": pytorch_stats,
        "onnx_runtime": onnx_stats,
        "fastapi_api": api_stats,
        "speedup_ratio": speedup,
        "target_48ms_achieved": target_met,
    }

    out_file = os.path.join(output_dir, "latency_benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved benchmark results to: {out_file}")
    print("=" * 65 + "\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run latency benchmarks.")
    parser.add_argument("--runs", type=int, default=100)
    args = parser.parse_args()

    benchmark_latency(num_runs=args.runs)
