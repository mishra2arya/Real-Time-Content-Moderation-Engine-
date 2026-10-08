# Real-Time Content Moderation Engine — Operating Manual

This is the definitive guide to running, testing, benchmarking, and deploying the **Real-Time Content Moderation Engine** from a fresh terminal.

All commands below are derived directly from the verified repository implementation.

---

## QUICK START

To start the production service immediately with all pre-trained weights and configurations:

```bash
# 1. Navigate to repository root
cd "/home/uday/Downloads/Real-Time Content Moderation Engine"

# 2. Activate Python virtual environment
source .venv/bin/activate

# 3. Launch service using the one-command start script
./scripts/start.sh
```

The service is now running on `http://0.0.0.0:8000`.

Open your browser to:
- **Web Dashboard**: `http://localhost:8000/` (Integrated React SPA)
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

In another terminal, verify service health:

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Send a real-time moderation request:

```bash
curl -s -X POST http://127.0.0.1:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"text": "Antigravity builds reliable real-time ML systems.", "text_id": "req-001"}' | python3 -m json.tool
```

---

## FRONTEND DASHBOARD (REACT + TYPESCRIPT + VITE)

The frontend is an enterprise dark-mode cybersecurity / AI operations dashboard with zero blue and zero pure black styling.

### 1. Unified Production Serving (One Command)
When you start the backend via `./scripts/start.sh`, FastAPI automatically mounts and serves the compiled frontend at the root URL:
```bash
# Terminal 1: Starts both backend API and React dashboard
./scripts/start.sh

# Open in browser:
http://localhost:8000/
```

### 2. Frontend Development with Hot Module Replacement (HMR)
For rapid frontend UI development with live reload:
```bash
# Terminal 1: Backend API
./scripts/start.sh

# Terminal 2: Vite Dev Server (proxies /api to localhost:8000)
source .venv/bin/activate
cd frontend
npm run dev

# Open in browser:
http://localhost:5173/
```

### 3. Frontend Quality & Test Suite
```bash
cd frontend

# Run frontend unit tests (Vitest)
npm run test

# Run TypeScript strict type verification
npm run typecheck

# Build optimized production bundle to frontend/dist/
npm run build
```

---

## FULL DEVELOPMENT WORKFLOW

### 1. Environment & Setup

```bash
# Python requirement: Python 3.11, 3.12, or 3.13 (Python 3.13.12 tested)
python3 --version

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install pinned runtime dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install development & testing tooling
pip install -r requirements-dev.txt

# Configure environment variables (optional overrides)
cp .env.example .env
```

### 2. Dataset Pipeline

The dataset engine can ingest external CSV/JSONL records or synthesize a curated 2,480-record moderation corpus with adversarial benign computing phrases (e.g. `kill -9`, `execute process`):

```bash
# Prepare dataset splits (train, val, test) and compute dataset statistics
python training/prepare_dataset.py --output_dir data/processed --seed 42

# Inspect generated dataset statistics
cat data/processed/dataset_stats.json | python3 -m json.tool
```

Output files:
- `data/processed/train.csv` (1,574 clean examples)
- `data/processed/val.csv` (338 clean examples)
- `data/processed/test.csv` (338 clean held-out examples)
- `data/processed/dataset_stats.json`

### 3. Model Fine-Tuning

Fine-tune `distilbert-base-uncased` with AdamW, class-weighted cross-entropy loss, and validation checkpointing:

```bash
# Train PyTorch model
python training/train.py --config configs/training_config.yaml
```

Output artifacts:
- Checkpoints saved to `models/pytorch/model.safetensors`
- Tokenizer configurations in `models/pytorch/tokenizer.json`
- Training metadata in `models/pytorch/training_metadata.json`

### 4. Scientific Evaluation

Evaluate the fine-tuned model against the held-out test split:

```bash
# Run scientific evaluation
python training/evaluate.py \
  --model_dir models/pytorch \
  --test_csv data/processed/test.csv \
  --output_dir artifacts

# View empirical classification report and confusion matrix
cat artifacts/classification_report.txt
cat artifacts/confusion_matrix.csv
cat artifacts/metrics.json | python3 -m json.tool
```

### 5. ONNX Export & Parity Validation

Export the fine-tuned PyTorch checkpoint to ONNX opset 17 with dynamic sequence length and batch sizing:

```bash
# Export PyTorch model to ONNX
python training/export_onnx.py \
  --model_dir models/pytorch \
  --output models/onnx/model.onnx \
  --opset 17

# Validate numerical parity between PyTorch and ONNX Runtime
pytest tests/model/test_onnx_parity.py -v
```

Output artifacts:
- `models/onnx/model.onnx` (255.5 MB graph)
- `models/onnx/tokenizer.json`
- `models/onnx/metadata.json`

---

## API TESTING

Start the API server in your main terminal:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run these commands in a separate terminal:

### 1. Liveness Probe (`GET /health`)
```bash
curl -s -i http://127.0.0.1:8000/health
```
- **Expected Status**: `HTTP/1.1 200 OK`
- **Expected Response**:
```json
{
    "status": "healthy",
    "app_name": "Real-Time Content Moderation Engine",
    "version": "1.0.0",
    "environment": "production"
}
```

### 2. Readiness Probe (`GET /ready`)
```bash
curl -s -i http://127.0.0.1:8000/ready
```
- **Expected Status**: `HTTP/1.1 200 OK`
- **Expected Response**:
```json
{
    "status": "ready",
    "model_ready": true,
    "model_info": {
        "model_version": "distilbert-moderation-v1",
        "engine": "ONNX Runtime",
        "execution_provider": "CPUExecutionProvider",
        "max_sequence_length": 128,
        "threads": 4,
        "ready": true
    },
    "system": {
        "memory_rss_mb": 918.75,
        "cpu_percent": 0.0,
        "num_threads": 64
    }
}
```

### 3. Service Version Metadata (`GET /version`)
```bash
curl -s -i http://127.0.0.1:8000/version
```
- **Expected Status**: `HTTP/1.1 200 OK`
- **Expected Response**:
```json
{
    "app_name": "Real-Time Content Moderation Engine",
    "app_version": "1.0.0",
    "model_version": "distilbert-moderation-v1",
    "inference_engine": "ONNX Runtime",
    "python_version": "3.13.12",
    "status": "active"
}
```

### 4. Single Moderation: Benign Content (`POST /moderate`)
```bash
curl -s -i -X POST http://127.0.0.1:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"text": "We are having a pleasant discussion about software engineering.", "text_id": "item-101"}'
```
- **Expected Status**: `HTTP/1.1 200 OK`
- **Expected Response**:
```json
{
    "text_id": "item-101",
    "request_id": "72ab5e6e-9524-4c10-90f6-93393814ba8b",
    "decision": "allow",
    "label": "non_toxic",
    "confidence": 0.9924,
    "policy_category": null,
    "policy_categories": [],
    "model_version": "distilbert-moderation-v1",
    "inference_ms": 9.021,
    "total_latency_ms": 9.166
}
```

### 5. Single Moderation: Toxic / Threat Content (`POST /moderate`)
```bash
curl -s -i -X POST http://127.0.0.1:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"text": "I will hunt you down and kill you.", "text_id": "item-102"}'
```
- **Expected Status**: `HTTP/1.1 200 OK`
- **Expected Response**:
```json
{
    "text_id": "item-102",
    "request_id": "6b634050-c85d-4232-b6be-c65b635e0fd7",
    "decision": "block",
    "label": "toxic",
    "confidence": 0.9932,
    "policy_category": "threat",
    "policy_categories": ["threat"],
    "model_version": "distilbert-moderation-v1",
    "inference_ms": 13.205,
    "total_latency_ms": 13.537
}
```

### 6. Batch Moderation (`POST /moderate/batch`)
```bash
curl -s -i -X POST http://127.0.0.1:8000/moderate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"text": "Have a wonderful weekend ahead!"},
      {"text": "You are an idiot and completely worthless."}
    ]
  }'
```
- **Expected Status**: `HTTP/1.1 200 OK`
- **Expected Response**:
```json
{
    "results": [
        {
            "text_id": null,
            "request_id": "401b64c0-ee18-4d6b-bcaa-427184f56338",
            "decision": "allow",
            "label": "non_toxic",
            "confidence": 0.985,
            "policy_category": null,
            "policy_categories": [],
            "model_version": "distilbert-moderation-v1",
            "inference_ms": 11.998,
            "total_latency_ms": 12.164
        },
        {
            "text_id": null,
            "request_id": "401b64c0-ee18-4d6b-bcaa-427184f56338",
            "decision": "block",
            "label": "toxic",
            "confidence": 0.9932,
            "policy_category": "insult",
            "policy_categories": ["insult"],
            "model_version": "distilbert-moderation-v1",
            "inference_ms": 11.998,
            "total_latency_ms": 12.188
        }
    ],
    "batch_size": 2,
    "total_latency_ms": 12.239
}
```

### 7. Prometheus Metrics (`GET /metrics`)
```bash
curl -s http://127.0.0.1:8000/metrics | grep moderation_
```
- **Expected Status**: `HTTP/1.1 200 OK`
- **Sample Output**:
```text
# HELP moderation_requests_total Total incoming moderation API requests
# TYPE moderation_requests_total counter
moderation_requests_total{endpoint="/moderate",method="POST",status="200"} 2.0
moderation_requests_total{endpoint="/moderate/batch",method="POST",status="200"} 1.0
# HELP moderation_decisions_total Moderation decisions by outcome and category
# TYPE moderation_decisions_total counter
moderation_decisions_total{decision="allow",label="non_toxic",policy_category="none"} 1.0
moderation_decisions_total{decision="block",label="toxic",policy_category="threat"} 1.0
```

---

## DOCKER

> **Note**: If running on a host where the Docker engine daemon is installed, use these verified container commands:

### 1. Build Production Image
```bash
docker build -t content-moderation-engine:latest .
```

### 2. Run Container
```bash
docker run --rm -d \
  --name moderation-engine \
  -p 8000:8000 \
  --memory="2g" \
  --cpus="2.0" \
  content-moderation-engine:latest
```

### 3. Verify Containerized Endpoint
```bash
# Verify container health probe
curl -s http://127.0.0.1:8000/health | python3 -m json.tool

# Verify container inference
curl -s -X POST http://127.0.0.1:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"text": "Containerized DistilBERT ONNX inference is operational."}' | python3 -m json.tool
```

### 4. Stop Container
```bash
docker stop moderation-engine
```

### 5. Multi-Container Orchestration with Prometheus
```bash
# Launch API service and Prometheus monitoring bundle
docker compose up -d --build

# Prometheus dashboard will be available at: http://localhost:9090
# API will be available at: http://localhost:8000

# Tear down containers
docker compose down
```

---

## TESTING

Run all automated quality, security, and functional tests:

```bash
# 1. Run full test suite with coverage report
pytest -v --cov=app --cov-report=term-missing

# 2. Run only unit tests
pytest tests/unit/ -v

# 3. Run API integration tests
pytest tests/api/ -v

# 4. Run PyTorch vs ONNX numerical parity tests
pytest tests/model/test_onnx_parity.py -v

# 5. Run adversarial robustness & edge-case tests
pytest tests/performance/test_robustness_adversarial.py -v

# 6. Static style and lint checks
ruff check .

# 7. Code formatting verification
black --check --target-version py313 .

# 8. Static type safety checks
mypy app/

# 9. AST security vulnerability scanner
bandit -c pyproject.toml -r app training

# 10. Dependency CVE audit
pip-audit
```

---

## PERFORMANCE BENCHMARKING

### 1. Latency Benchmark
Measures end-to-end API latency distribution (P50, P90, P95, P99) across 100 requests.
```bash
python benchmarks/benchmark_latency.py --runs 100
```
- **What it measures**: Client HTTP request to FastAPI + ONNX Runtime forward pass + Policy evaluation.
- **Where results are stored**: `benchmarks/latency_benchmark_results.json` and `artifacts/performance.json`.
- **Warmup**: 15 pre-warm iterations.
- **Expected Output**:
  ```text
  FastAPI API:   P50=14.244ms | P95=17.858ms | P99=19.982ms | Mean=14.724ms
  Target Latency (<48ms at P95): ACHIEVED
  ```

### 2. Throughput Benchmark
Evaluates message processing rates across multiple batch sizes and concurrency worker levels.
```bash
python benchmarks/benchmark_throughput.py
```
- **What it measures**: Peak batch processing rate (batch sizes 1, 8, 16, 32, 64, 128) and concurrent async requests (1, 5, 10, 20 workers).
- **Where results are stored**: `benchmarks/throughput_benchmark_results.json` and `artifacts/performance.json`.
- **Expected Output**:
  ```text
  Peak Batch Processing Throughput:   168.2 msg/sec (Batch size 8)
  Peak Concurrent Request Throughput: 90.2 req/sec (Concurrency 10)
  ```

### 3. Locust Load Testing
Simulates realistic user traffic with mixed payload patterns:
```bash
locust -f benchmarks/locustfile.py \
  --headless \
  -u 20 \
  -r 5 \
  --run-time 30s \
  --host http://127.0.0.1:8000
```
- **What it measures**: Sustained requests/sec, failure rates, and latency under multi-user concurrency.
- **Target**: Local test infrastructure only (`http://127.0.0.1:8000`).

---

## GCP DEPLOYMENT

### Safe Local Files
The repository includes production-ready Google Cloud Run deployment definitions:
- Knative Cloud Run manifest: `deployment/gcp/service.yaml`
- Cloud Build configuration: `deployment/gcp/cloudbuild.yaml`
- Automated deployer: `deployment/gcp/deploy.sh`

> **Note**: Deployment commands prepared but not verified against a live GCP project. No external billable resources are provisioned automatically.

### External Cloud Run Deployment Commands
When deploying to an active Google Cloud Platform project with authenticated `gcloud`:

```bash
# 1. Set target GCP Project and Region
export PROJECT_ID="<YOUR_GCP_PROJECT_ID>"
export REGION="us-central1"
export SERVICE_NAME="content-moderation-engine"
export IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/moderation/engine:latest"

# 2. Build and submit container image to Artifact Registry
gcloud builds submit --tag "${IMAGE}" .

# 3. Deploy to Cloud Run with autoscaling (min 1, max 20 instances)
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE}" \
    --region "${REGION}" \
    --platform managed \
    --cpu 2 \
    --memory 2Gi \
    --concurrency 80 \
    --min-instances 1 \
    --max-instances 20 \
    --no-cpu-throttling \
    --allow-unauthenticated \
    --set-env-vars="APP_ENV=production,LOG_LEVEL=INFO,NUM_THREADS=4,DEFAULT_TOXICITY_THRESHOLD=0.50,STRICT_TOXICITY_THRESHOLD=0.35,FLAG_REVIEW_THRESHOLD=0.40,BATCH_MAX_SIZE=64,BATCH_TIMEOUT_MS=5,MAX_CONCURRENT_REQUESTS=100"

# 4. Alternatively, use the automated deploy script:
./deployment/gcp/deploy.sh
```

---

## ONE-COMMAND START OPTION

We provide `scripts/start.sh` which executes environment validation, dependency verification, model artifact confirmation, and starts Uvicorn with clean error diagnostics:

```bash
./scripts/start.sh
```

### What `scripts/start.sh` does:
1. Validates and activates `.venv`.
2. Validates core imports (`fastapi`, `onnxruntime`, `torch`, `transformers`, `pydantic`).
3. Confirms existence and file sizes of `models/onnx/model.onnx` and `models/onnx/tokenizer.json`.
4. Sets `PYTHONPATH` to the repository root.
5. Launches `uvicorn app.main:app` with graceful termination handling.

---

## TROUBLESHOOTING

### 1. Check Python & Environment
```bash
python3 --version
which python3
```
*Expected: Python 3.11.x, 3.12.x, or 3.13.x inside `.venv/bin/python3`.*

### 2. Check Dependencies
```bash
python -c "import fastapi, onnxruntime, torch, transformers; print('Dependencies OK')"
```

### 3. Check ONNX Model Assets
```bash
ls -lh models/onnx/model.onnx models/onnx/tokenizer.json
```
*Expected: `model.onnx` is ~256MB and `tokenizer.json` is ~696KB.*

### 4. Check If Port 8000 Is In Use
```bash
lsof -i :8000 || netstat -tuln | grep 8000 || echo "Port 8000 is free"
```

### 5. Check Running API Process
```bash
pgrep -fl uvicorn || echo "No uvicorn process running"
```

### 6. Kill Any Stray Uvicorn Processes
```bash
pkill -f "uvicorn app.main:app" || true
```

### 7. Check ONNX Runtime Execution Provider
```bash
python -c "import onnxruntime as ort; print('Available Providers:', ort.get_available_providers())"
```
*Expected: `['CPUExecutionProvider']`.*

### 8. Check Active Configuration Safely (No Secrets)
```bash
python -c "
from app.core.config import get_settings
s = get_settings()
print('App Name:     ', s.app_name)
print('Version:      ', s.app_version)
print('Environment:  ', s.app_env)
print('Model Path:   ', s.model_onnx_path)
print('CPU Threads:  ', s.num_threads)
print('Toxicity Thresh:', s.default_toxicity_threshold)
"
```

---

## FROM ZERO TO RUNNING

Follow these exact steps from a clean machine where this repository is cloned:

```bash
# Step 1: Navigate into repository root
cd "/home/uday/Downloads/Real-Time Content Moderation Engine"

# Step 2: Create Python 3 virtual environment
python3 -m venv .venv

# Step 3: Activate virtual environment
source .venv/bin/activate

# Step 4: Upgrade pip and install runtime dependencies
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

# Step 5: (Optional) Prepare configuration file
cp .env.example .env

# Step 6: Verify pre-built model or generate from scratch
# (Pre-trained ONNX model is already supplied in models/onnx/model.onnx)
# To regenerate:
# python training/prepare_dataset.py
# python training/train.py
# python training/export_onnx.py

# Step 7: Launch API service
./scripts/start.sh

# Step 8: (In second terminal) Verify health
curl -s http://127.0.0.1:8000/health | python3 -m json.tool

# Step 9: Send real test request
curl -s -X POST http://127.0.0.1:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"text": "Antigravity powers production-ready ML engineering."}' | python3 -m json.tool

# Step 10: Run full test suite
pytest -q
```

---

## COPY-PASTE QUICK START

Copy and paste this single block into your terminal:

```bash
cd "/home/uday/Downloads/Real-Time Content Moderation Engine" && \
source .venv/bin/activate && \
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
