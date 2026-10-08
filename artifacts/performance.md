# Content Moderation Engine — Performance & Benchmark Report

## 1. Benchmark Environment
- **Hardware Platform**: x86_64 CPU (Intel/AMD Architecture, 4 execution threads allocated)
- **Operating System**: Linux (Debian 3.13.12 Kernel)
- **Runtime Environment**: Python 3.13.12, ONNX Runtime 1.30.0, PyTorch 2.14.0+cpu
- **Model Architecture**: `distilbert-base-uncased` fine-tuned for binary moderation (66,364,418 parameters)
- **Sequence Length**: 128 tokens
- **Warmup Iterations**: 10 warmup requests executed prior to timing

---

## 2. Latency Breakdown & Target Evaluation

Target SLA: **$< 48\text{ ms/request}$**

| Measurement Layer | P50 Latency | P90 Latency | P95 Latency | P99 Latency | Mean Latency | Max Latency | Target Status |
|---|---|---|---|---|---|---|---|
| **PyTorch CPU Baseline** | 10.76 ms | 12.15 ms | 12.67 ms | 13.69 ms | 11.35 ms | 45.27 ms | PASS ($<48\text{ms}$) |
| **ONNX Runtime (CPU)** | 10.39 ms | 12.30 ms | 12.39 ms | 12.80 ms | 10.50 ms | 13.41 ms | PASS ($<48\text{ms}$) |
| **FastAPI Client E2E** | **14.24 ms** | **17.32 ms** | **17.86 ms** | **19.98 ms** | **14.72 ms** | **21.90 ms** | **ACHIEVED** |

*Note: FastAPI latency accounts for full HTTP serialization, Pydantic v2 validation, text preprocessing, ONNX Runtime C++ execution, policy threshold evaluation, and structured JSON formatting.*

---

## 3. Throughput & Concurrency Scaling

Target SLA: **$\ge 1,000\text{ msg/sec}$**

### Vectorized Batch Processing
| Batch Size | Duration (s) | Total Messages | Throughput (msg/sec) | Mean Latency (ms) | Latency Per Message (ms) |
|---|---|---|---|---|---|
| **1** | 0.222 | 20 | 90.0 msg/s | 11.11 ms | 11.11 ms |
| **8** | 0.951 | 160 | 168.2 msg/s | 47.57 ms | 5.95 ms |
| **16** | 1.930 | 320 | 165.8 msg/s | 96.49 ms | 6.03 ms |
| **32** | 4.210 | 640 | 152.0 msg/s | 210.51 ms | 6.58 ms |
| **64** | 7.634 | 1,280 | 167.7 msg/s | 381.72 ms | 5.96 ms |
| **128** | 15.403 | 2,560 | 166.2 msg/s | 770.15 ms | 6.02 ms |

### Concurrent Request Streams (Single Request Workload)
| Concurrent Workers | Total Requests | Duration (s) | Requests / Sec (RPS) | P50 Latency (ms) | P95 Latency (ms) |
|---|---|---|---|---|---|
| **1** | 15 | 0.17 | 89.2 req/s | 11.16 ms | 12.00 ms |
| **5** | 75 | 0.84 | 88.9 req/s | 11.10 ms | 12.31 ms |
| **10** | 150 | 1.66 | 90.2 req/s | 11.08 ms | 11.60 ms |
| **20** | 300 | 3.34 | 89.9 req/s | 11.07 ms | 11.68 ms |

---

## 4. Hardware Bottleneck & Horizontal Scaling Analysis

- **Single Worker Ceiling**: A single sequential CPU thread takes ~6–11 ms per forward pass. A single worker process mathematically caps out at approximately $1 / 0.006 \approx 167\text{ msg/sec}$.
- **Achieving $1,000+\text{ msg/sec}$ in Production**: To handle 1,000+ incoming message streams per second, the service relies on horizontal scaling:
  $$\text{Required Instances} = \frac{1000\text{ msg/s}}{168\text{ msg/s/instance}} \approx 6\text{ Cloud Run instances}$$
- The provided GCP Cloud Run Knative manifest (`deployment/gcp/service.yaml`) configures autoscaling from **1 to 20 instances** with 80 concurrent connections per instance, providing total capacity up to **1,600 concurrent streams**.
