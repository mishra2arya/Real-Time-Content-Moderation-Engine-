# System Architecture — Real-Time Content Moderation Engine

## 1. High-Level Architecture Overview

The Content Moderation Engine is organized into decoupled, modular layers designed for high-throughput stream moderation with predictable low latency:

```text
[ Client Streaming Requests / Edge API Gateways ]
                        │
                        ▼
          ┌───────────────────────────┐
          │     FastAPI ASGI Server   │
          │  - Request ID Tracing     │
          │  - CORS / Auth Guards     │
          │  - Prometheus Metrics     │
          └─────────────┬─────────────┘
                        │
                        ▼
          ┌───────────────────────────┐
          │   Moderation Coordinator  │
          └──────┬─────────────┬──────┘
                 │             │
        (Single Stream)   (Batched Stream)
                 │             │
                 ▼             ▼
       ┌────────────────┐  ┌─────────────────────────┐
       │ Text Cleaning  │  │ Dynamic Micro-Batcher   │
       │ Normalization  │  │ Bounded Concurrency     │
       └────────┬───────┘  └───────────┬─────────────┘
                │                      │
                └──────────┬───────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  ONNX Runtime Accelerator (C++)   │
          │  - Graph Optimization (Level All) │
          │  - Threading & Memory Allocation  │
          │  - DistilBERT Sequence Classifier │
          └────────────────┬──────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │    Decoupled Policy Engine        │
          │  - Thresholds (ALLOW/REVIEW/BLOCK)│
          │  - Violation Tagging              │
          └────────────────┬──────────────────┘
                           │
                           ▼
            [ Structured JSON Response ]
```

---

## 2. Component Design Details

### 2.1 Preprocessing (`app/moderation/preprocessing.py`)
- **Unicode NFKD Normalization**: Decomposes ligature variants and accented characters.
- **Invisible Character Removal**: Strips zero-width spaces (`\u200B` to `\u200D`), zero-width non-breaking spaces (`\uFEFF`), and directional marks.
- **HTML Sanitization**: Strips HTML tags (`<p>`, `<div>`) first, then unescapes entities (`&amp;` $\to$ `&`, `&lt;` $\to$ `<`).
- **Repetition Reduction**: Normalizes elongated text (e.g. `haaaate` $\to$ `haate`), suppressing evasion strategies.
- **Length Caps**: Discards characters beyond 10,000 to prevent denial-of-service memory exhaustion.

### 2.2 Inference Engine (`app/inference/onnx_engine.py`)
- **Singleton Lifecycle**: Created once at startup during FastAPI lifespan initialization.
- **Thread Tuning**: Configured with 4 intra-op CPU threads for optimal multi-core parallelism.
- **Pre-warming**: Primes the execution graph and C++ tensor memory buffers during startup to eliminate cold-start spikes.

### 2.3 Dynamic Micro-Batching (`app/inference/batching.py`)
- **Asynchronous Queue**: Incoming requests are queued in an asyncio queue with bounded backpressure.
- **Time-Bounded Aggregation**: Flushes batches when reaching either `batch_max_size` (64 items) or `batch_timeout_ms` (5ms).
- **Executor Offloading**: Runs vector forward-passes in a separate thread pool to keep the ASGI event loop unblocked.

### 2.4 Policy Decoupling (`app/moderation/postprocessing.py`)
- Isolates mathematical neural network probabilities from business logic rules.
- Supports variable safety sensitivity:
  - Standard Mode: `block_threshold = 0.50`, `flag_threshold = 0.40`.
  - Strict Mode: `strict_threshold = 0.35` for elevated safety environments.
- Granular subcategory detection: `threat`, `severe_toxicity`, `insult`, `identity_attack`, `sexual_explicit`.

### 2.5 Observability & Probes (`app/observability/`)
- **Metrics**: Standard Prometheus exposition via `/metrics` (`moderation_requests_total`, `moderation_request_duration_seconds`, `moderation_inference_duration_seconds`, `moderation_decisions_total`).
- **Health Probes**: Liveness probe on `/health` and Kubernetes/Knative readiness probe on `/ready`.

### 2.6 Frontend Dashboard Architecture (`frontend/`)
- **Stack**: React 18, TypeScript 5, Vite 6, Tailwind CSS 3.
- **Design System**: High-contrast cybersecurity operations aesthetic adhering to strict **NO BLUE** and **NO PURE BLACK** constraints (charcoal/graphite surfaces, violet/magenta accents, emerald positive, amber warning, rose danger).
- **Component Architecture**:
  - `Sidebar` & `Header`: Navigation, live status pill, real-time sync.
  - `DashboardPage`: Top KPI cards, live inference sandbox, engine summary, and activity table.
  - `LiveModerationPage`: Single-item real-time analysis and multi-line vectorized batch processing with confidence gauges.
  - `StreamMonitorPage`: Real-time audit log with search, filtering by outcome, and modal event inspection.
  - `AnalyticsPage`: Decision ratios, policy category distribution, and empirical latency percentiles.
  - `ModelPage`: Transformer parameter specs, ONNX runtime configuration, and confusion matrix display.
  - `ApiPage`: Interactive REST documentation and query runner.
  - `SystemPage`: Live process memory (RSS), CPU %, thread count, and Knative autoscaling specifications.
- **Serving Model**: Built with `npm run build` into `frontend/dist/` and served directly by FastAPI via `StaticFiles(directory="frontend/dist", html=True)`. Also supports standalone Vite development server with API proxying.
