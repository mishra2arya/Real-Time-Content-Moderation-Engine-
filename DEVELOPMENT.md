# Development Guide — Real-Time Content Moderation Engine

## 1. Environment Setup

Ensure you have Python 3.11+ installed. Python 3.13 is recommended.

```bash
# Clone the repository
git clone https://github.com/example/real-time-content-moderation-engine.git
cd "Real-Time Content Moderation Engine"

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install all development dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt
```

---

## 2. Dataset Preparation & Retraining

To generate the processed dataset and calculate statistics:
```bash
python training/prepare_dataset.py
```
To ingest an external CSV (e.g. 200K+ records from Jigsaw/Civil Comments):
```bash
python training/prepare_dataset.py --input /path/to/raw_dataset.csv --text-col text --label-col label
```

To fine-tune the DistilBERT model:
```bash
python training/train.py --config configs/training_config.yaml
```

To evaluate the model on the held-out test split:
```bash
python training/evaluate.py
```

To export the trained PyTorch checkpoint to an optimized ONNX graph:
```bash
python training/export_onnx.py
```

---

## 3. Running Tests & Static Quality Checks

### Run Automated Tests with Coverage
```bash
pytest -v --cov=app --cov-report=term-missing
```

### Run Ruff Linter
```bash
ruff check .
```

### Run Black Code Formatter Check
```bash
black --check .
```

### Run MyPy Static Type Checker
```bash
mypy app/
```

### Run Bandit Security Audit
```bash
bandit -r app training -c pyproject.toml
```

### Run Pip-Audit Dependency Vulnerability Scan
```bash
pip-audit
```

---

## 4. Local Development Server

Run the development server with live reload:
```bash
./scripts/run_local.sh
```
Or directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation: `http://localhost:8000/docs`
