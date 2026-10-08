#!/usr/bin/env bash
# ==============================================================================
# Production Startup Script for Real-Time Content Moderation Engine
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

echo "======================================================================"
echo " Starting Real-Time Content Moderation Engine"
echo " Working Directory: ${ROOT_DIR}"
echo "======================================================================"

# 1. Validate and activate virtual environment
if [ -f "${ROOT_DIR}/.venv/bin/activate" ]; then
    echo "[1/4] Activating virtual environment (.venv)..."
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.venv/bin/activate"
elif command -v python3 &>/dev/null; then
    echo "[1/4] Using active python environment: $(which python3)"
else
    echo "ERROR: No suitable Python environment found. Please run python3 -m venv .venv && source .venv/bin/activate"
    exit 1
fi

# 2. Validate dependencies
echo "[2/4] Validating core dependencies..."
python3 -c "
import fastapi, uvicorn, onnxruntime, transformers, torch, pydantic
print(f'   -> FastAPI: {fastapi.__version__}')
print(f'   -> ONNX Runtime: {onnxruntime.__version__}')
print(f'   -> PyTorch: {torch.__version__}')
print(f'   -> Transformers: {transformers.__version__}')
" || {
    echo "ERROR: Missing required dependencies. Please run: pip install -r requirements.txt"
    exit 1
}

# 3. Validate ONNX model artifacts
MODEL_FILE="${ROOT_DIR}/models/onnx/model.onnx"
TOKENIZER_FILE="${ROOT_DIR}/models/onnx/tokenizer.json"
echo "[3/4] Verifying model artifacts..."
if [ ! -f "${MODEL_FILE}" ]; then
    echo "ERROR: Model file not found at: ${MODEL_FILE}"
    echo "Please generate the model using: python training/train.py && python training/export_onnx.py"
    exit 1
fi
if [ ! -f "${TOKENIZER_FILE}" ]; then
    echo "ERROR: Tokenizer file not found at: ${TOKENIZER_FILE}"
    exit 1
fi
echo "   -> ONNX Model: $(du -h "${MODEL_FILE}" | cut -f1) (${MODEL_FILE})"
echo "   -> Tokenizer:  $(du -h "${TOKENIZER_FILE}" | cut -f1) (${TOKENIZER_FILE})"

# 4. Configure environment and start server
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"
LOG_LEVEL="${LOG_LEVEL:-info}"

export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

echo "[4/4] Launching Uvicorn service on http://${HOST}:${PORT} (workers: ${WORKERS})..."
echo "======================================================================"
exec python3 -m uvicorn app.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --log-level "${LOG_LEVEL}"
