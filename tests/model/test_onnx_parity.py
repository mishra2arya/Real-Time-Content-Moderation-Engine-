"""Model and ONNX Runtime unit tests."""

import os

import numpy as np
import pytest
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.inference.onnx_engine import ONNXInferenceEngine
from app.moderation.tokenizer import ModerationTokenizer


def test_tokenizer_output_shapes():
    """Tokenizer produces numpy arrays with correct dimensions and int64 dtype."""
    tokenizer = ModerationTokenizer(max_length=64)
    res = tokenizer.tokenize(
        ["First text sample", "Second sample"], padding="max_length"
    )

    assert "input_ids" in res
    assert "attention_mask" in res
    assert res["input_ids"].shape == (2, 64)
    assert res["attention_mask"].shape == (2, 64)
    assert res["input_ids"].dtype == np.int64
    assert res["attention_mask"].dtype == np.int64


def test_onnx_engine_predict(onnx_engine: ONNXInferenceEngine):
    """ONNX engine should return valid logits and positive latency."""
    logits, latency_ms = onnx_engine.predict(["Test sentence for inference."])
    assert logits.shape == (1, 2)
    assert latency_ms > 0.0
    assert not np.isnan(logits).any()


def test_pytorch_onnx_numerical_parity(onnx_engine: ONNXInferenceEngine):
    """Verify PyTorch and ONNX Runtime predictions agree within numerical tolerance."""
    pytorch_dir = "models/pytorch"
    has_weights = os.path.isdir(pytorch_dir) and any(
        os.path.exists(os.path.join(pytorch_dir, fname))
        for fname in ("model.safetensors", "pytorch_model.bin")
    )
    if not has_weights:
        pytest.skip("PyTorch model weights not found in models/pytorch.")

    pt_model = AutoModelForSequenceClassification.from_pretrained(pytorch_dir)
    pt_tokenizer = AutoTokenizer.from_pretrained(pytorch_dir)
    pt_model.eval()

    test_inputs = [
        "A pleasant morning to everyone.",
        "You are a terrible person and an idiot.",
        "Terminating worker process on node 4.",
    ]

    for text in test_inputs:
        # PyTorch pass
        enc = pt_tokenizer(
            text,
            max_length=128,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        with torch.no_grad():
            pt_logits = pt_model(**enc).logits.cpu().numpy()

        # ONNX pass
        ort_logits, _ = onnx_engine.predict([text])

        # Assert parity
        np.testing.assert_allclose(pt_logits, ort_logits, rtol=1e-3, atol=1e-4)
