#!/usr/bin/env bash
# Comprehensive benchmark suite runner
set -euo pipefail

source .venv/bin/activate 2>/dev/null || true

echo "=========================================================="
echo "RUNNING FULL CONTENT MODERATION ENGINE BENCHMARK SUITE"
echo "=========================================================="

echo "==> 1. Running Latency Benchmarks (PyTorch vs ONNX vs API)..."
python benchmarks/benchmark_latency.py --runs 100

echo "==> 2. Running Throughput & Concurrency Benchmarks..."
python benchmarks/benchmark_throughput.py

echo "=========================================================="
echo "All benchmarks completed successfully! Results in benchmarks/"
echo "=========================================================="
