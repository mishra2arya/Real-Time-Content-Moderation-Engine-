#!/usr/bin/env bash
# Automated deployment script for Google Cloud Run
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="content-moderation-engine"
IMAGE_TAG="us-central1-docker.pkg.dev/${PROJECT_ID}/moderation/engine:latest"

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: PROJECT_ID is not set. Please export PROJECT_ID=<your-gcp-project-id> or log in with gcloud."
    exit 1
fi

echo "========================================================="
echo "Deploying ${SERVICE_NAME} to GCP Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region:  ${REGION}"
echo "Image:   ${IMAGE_TAG}"
echo "========================================================="

# 1. Build and Submit Container Image
echo "Building and pushing container image to Artifact Registry..."
gcloud builds submit --tag "${IMAGE_TAG}" .

# 2. Deploy to Cloud Run
echo "Deploying service to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_TAG}" \
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

echo "========================================================="
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --format 'value(status.url)')
echo "Deployment successful! Service URL: ${SERVICE_URL}"
echo "Testing health probe: curl ${SERVICE_URL}/health"
echo "========================================================="
