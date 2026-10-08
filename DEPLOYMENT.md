# Production Deployment Guide

## 1. Containerization (Docker)

### Build the Production Image
The Dockerfile uses a multi-stage build that compiles dependencies in a builder stage and creates a lightweight runtime container running under an unprivileged non-root user (`appuser`).

```bash
docker build -t content-moderation-engine:latest .
```

### Run Locally with Docker
```bash
docker run --rm \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e LOG_LEVEL=INFO \
  -e NUM_THREADS=4 \
  content-moderation-engine:latest
```

### Test Container Health Probe
```bash
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/ready | jq .
```

### Run with Docker Compose (Engine + Prometheus)
```bash
docker compose up --build
```
- API Server: `http://localhost:8000`
- Prometheus Metrics Dashboard: `http://localhost:9090`

---

## 2. Google Cloud Platform (Cloud Run)

The service is engineered for serverless horizontal autoscaling on Google Cloud Run.

### Architecture Parameters
- **Memory**: 2 GiB
- **CPU**: 2 vCPU
- **Concurrency**: 80 concurrent connections per container instance
- **Autoscaling**: Minimum 1 instance (eliminates cold starts), Maximum 20 instances
- **Scaling Bandwidth**: $20 \times 80 = 1,600$ concurrent stream capacity

### Automated Deployment via Script
```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

./deployment/gcp/deploy.sh
```

### Declarative Deployment via Knative Manifest
```bash
gcloud run services replace deployment/gcp/service.yaml --region us-central1
```

### Cloud Build Pipeline
The repository includes `deployment/gcp/cloudbuild.yaml` which automatically runs the test suite, builds the container image, publishes to Google Artifact Registry, and deploys to Cloud Run.
```bash
gcloud builds submit --config deployment/gcp/cloudbuild.yaml .
```

---

## 3. Production Readiness Checklist

- [x] Multi-stage container build with dependency caching
- [x] Unprivileged runtime user (`appuser:appgroup` with UID 10001)
- [x] Liveness probe configured on `/health`
- [x] Readiness probe configured on `/ready`
- [x] Prometheus `/metrics` endpoint exposed
- [x] Graceful shutdown handling on `SIGTERM`
- [x] Sensitive user content excluded from structured logs
- [x] Autoscaling parameters tuned to handle 1,000+ incoming message streams
