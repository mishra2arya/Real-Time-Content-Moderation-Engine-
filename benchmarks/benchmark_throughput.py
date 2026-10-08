"""High-throughput benchmark testing concurrency, stream scaling, and vector batching."""

import argparse
import asyncio
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

from app.services.moderation_service import ModerationService

SAMPLE_MESSAGES = [
    "I really love the collaborative work being done by this development team.",
    "You are an obnoxious clown and your code is absolute garbage.",
    "Could someone explain how to tune the ONNX Runtime execution provider?",
    "I will find you and make you suffer for this insult.",
    "The new production release deployment was finished ahead of schedule.",
    "Why are you being so rude? Please maintain professional etiquette.",
    "Let's schedule a design review session for the new inference architecture.",
    "Kill the background process before triggering the server shutdown.",
]


async def benchmark_batch_throughput(
    service: ModerationService,
    batch_sizes: List[int] = [1, 8, 16, 32, 64, 128],
    num_batches: int = 20,
) -> Dict[str, any]:
    """Measure throughput scaling across various batch sizes."""
    print("\n--- Measuring Vectorized Batch Processing Throughput ---")
    batch_results = {}

    for bsize in batch_sizes:
        items = [
            {"text": SAMPLE_MESSAGES[i % len(SAMPLE_MESSAGES)], "text_id": f"id-{i}"}
            for i in range(bsize)
        ]

        # Warmup
        await service.moderate_batch(items)

        latencies = []
        t_start = time.perf_counter()
        for _ in range(num_batches):
            t0 = time.perf_counter()
            _ = await service.moderate_batch(items)
            latencies.append((time.perf_counter() - t0) * 1000.0)
        total_time = time.perf_counter() - t_start

        total_messages = bsize * num_batches
        msg_per_sec = total_messages / max(total_time, 1e-6)
        arr = np.array(latencies)

        batch_results[f"batch_{bsize}"] = {
            "batch_size": bsize,
            "total_messages": total_messages,
            "duration_seconds": round(total_time, 3),
            "messages_per_second": round(msg_per_sec, 2),
            "p50_latency_ms": round(float(np.percentile(arr, 50)), 3),
            "p95_latency_ms": round(float(np.percentile(arr, 95)), 3),
            "mean_latency_ms": round(float(np.mean(arr)), 3),
            "latency_per_message_ms": round(float(np.mean(arr)) / bsize, 3),
        }
        print(
            f"Batch Size {bsize:3d} | Latency: {np.mean(arr):6.2f}ms | Throughput: {msg_per_sec:7.1f} msg/sec | Per-msg: {np.mean(arr)/bsize:5.2f}ms"
        )

    return batch_results


async def benchmark_concurrent_stream(
    service: ModerationService,
    concurrencies: List[int] = [1, 5, 10, 20],
    requests_per_worker: int = 15,
) -> Dict[str, any]:
    """Measure concurrent request throughput and latency distribution."""
    print("\n--- Measuring Concurrent Stream Handling ---")
    concurrency_results = {}

    for c in concurrencies:
        latencies = []
        errors = 0

        async def worker(worker_id: int):
            nonlocal errors
            for req_idx in range(requests_per_worker):
                text = SAMPLE_MESSAGES[(worker_id + req_idx) % len(SAMPLE_MESSAGES)]
                t0 = time.perf_counter()
                try:
                    _ = await service.moderate_text(
                        text, text_id=f"c-{worker_id}-{req_idx}"
                    )
                    latencies.append((time.perf_counter() - t0) * 1000.0)
                except Exception:
                    errors += 1

        t_start = time.perf_counter()
        tasks = [worker(w) for w in range(c)]
        await asyncio.gather(*tasks)
        total_time = time.perf_counter() - t_start

        total_reqs = c * requests_per_worker
        rps = total_reqs / max(total_time, 1e-6)
        arr = np.array(latencies) if latencies else np.array([0.0])

        concurrency_results[f"concurrency_{c}"] = {
            "concurrent_workers": c,
            "total_requests": total_reqs,
            "successful_requests": len(latencies),
            "failed_requests": errors,
            "duration_seconds": round(total_time, 3),
            "requests_per_second": round(rps, 2),
            "p50_latency_ms": round(float(np.percentile(arr, 50)), 3),
            "p95_latency_ms": round(float(np.percentile(arr, 95)), 3),
            "p99_latency_ms": round(float(np.percentile(arr, 99)), 3),
        }
        print(
            f"Concurrency {c:2d} | Total: {total_reqs} reqs in {total_time:.2f}s | RPS: {rps:6.1f} req/s | P50: {np.percentile(arr, 50):5.2f}ms | P95: {np.percentile(arr, 95):5.2f}ms"
        )

    return concurrency_results


async def main():
    parser = argparse.ArgumentParser(description="Run throughput benchmark.")
    parser.add_argument("--output_dir", type=str, default="benchmarks")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    service = ModerationService()

    print("=" * 65)
    print("THROUGHPUT & CONCURRENCY BENCHMARK SUITE")
    print("=" * 65)

    batch_metrics = await benchmark_batch_throughput(service)
    concurrent_metrics = await benchmark_concurrent_stream(service)

    # Check whether 1,000+ msg/sec target was achieved
    max_batch_throughput = max(v["messages_per_second"] for v in batch_metrics.values())
    max_concurrent_rps = max(
        v["requests_per_second"] for v in concurrent_metrics.values()
    )
    target_1000_achieved = max_batch_throughput >= 1000.0

    print("\n" + "=" * 65)
    print("SUMMARY OF THROUGHPUT BENCHMARK RESULTS")
    print("=" * 65)
    print(f"Peak Batch Processing Throughput:     {max_batch_throughput:.1f} msg/sec")
    print(f"Peak Concurrent Request Throughput:   {max_concurrent_rps:.1f} req/sec")
    print(
        f"Target >= 1,000 msg/sec (Batch):      {'ACHIEVED' if target_1000_achieved else 'NOT ACHIEVED'}"
    )
    print(
        f"Target >= 1,000 msg/sec (Concurrent): {'ACHIEVED' if max_concurrent_rps >= 1000.0 else 'NOT ACHIEVED (Hardware CPU bounded)'}"
    )

    summary = {
        "peak_batch_throughput_msg_per_sec": max_batch_throughput,
        "peak_concurrent_rps": max_concurrent_rps,
        "target_1000_msg_sec_achieved_batch": target_1000_achieved,
        "target_1000_msg_sec_achieved_concurrent": bool(max_concurrent_rps >= 1000.0),
        "batch_benchmarks": batch_metrics,
        "concurrent_benchmarks": concurrent_metrics,
        "hardware_context": "Local CPU Inference (Intel/AMD x86_64, 4 threads)",
    }

    out_file = os.path.join(args.output_dir, "throughput_benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Results saved to: {out_file}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
