#!/usr/bin/env bash
# Environment setup and asset generation script
set -euo pipefail

echo "==> 1. Setting up Python 3.13 Virtual Environment..."
python3.13 -m venv .venv
source .venv/bin/activate

echo "==> 2. Installing Dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

echo "==> 3. Preparing Dataset..."
python training/prepare_dataset.py

echo "==> 4. Verifying Model and ONNX Artifacts..."
if [ ! -f "models/onnx/model.onnx" ] && [ -d "models/onnx/parts" ]; then
    echo "Reconstructing ONNX model from chunks..."
    cat models/onnx/parts/model.onnx.part_* > models/onnx/model.onnx
fi
if [ ! -f "models/onnx/model.onnx" ]; then
    echo "Exporting ONNX model..."
    python training/export_onnx.py
fi

echo "==> 5. Running Test Suite..."
pytest -v tests/

echo "==> Setup completed successfully!"
