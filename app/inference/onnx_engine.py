"""Optimized ONNX Runtime inference engine with session caching and warmup."""

import json
import os
import time
from typing import List, Optional, Tuple, Union

import numpy as np
import onnxruntime as ort

from app.core.config import get_settings
from app.core.logging import logger
from app.moderation.tokenizer import ModerationTokenizer


class ONNXInferenceEngine:
    """High-performance ONNX Runtime inference engine for DistilBERT."""

    _instance: Optional["ONNXInferenceEngine"] = None

    def __init__(
        self,
        model_path: Optional[str] = None,
        tokenizer_path: Optional[str] = None,
        execution_provider: Optional[str] = None,
        num_threads: Optional[int] = None,
        max_length: Optional[int] = None,
    ):
        settings = get_settings()
        self.model_path = model_path or settings.model_onnx_path
        self.tokenizer_path = tokenizer_path or os.path.dirname(self.model_path)
        self.execution_provider = execution_provider or settings.execution_provider
        self.num_threads = num_threads or settings.num_threads
        self.max_length = max_length or settings.max_sequence_length

        self.model_version = "distilbert-moderation-v1"
        self._load_metadata()

        # Initialize session
        self.session, self.tokenizer = self._initialize_session()

        # Warmup session
        self.warmup()

    def _load_metadata(self) -> None:
        """Load model metadata if present."""
        meta_path = os.path.join(os.path.dirname(self.model_path), "metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    self.model_version = meta.get("model_version", self.model_version)
            except Exception as e:
                logger.warning(f"Could not parse model metadata: {e}")

    def _initialize_session(self) -> Tuple[ort.InferenceSession, ModerationTokenizer]:
        """Configure and create ONNX Runtime InferenceSession and Tokenizer."""
        if not os.path.exists(self.model_path):
            parts_dir = os.path.join(os.path.dirname(self.model_path), "parts")
            if os.path.isdir(parts_dir):
                part_files = sorted(
                    [
                        os.path.join(parts_dir, f)
                        for f in os.listdir(parts_dir)
                        if f.startswith(os.path.basename(self.model_path) + ".part_")
                    ]
                )
                if part_files:
                    logger.info(
                        f"Reconstructing {self.model_path} from {len(part_files)} chunks..."
                    )
                    with open(self.model_path, "wb") as f_out:
                        for p in part_files:
                            with open(p, "rb") as f_in:
                                f_out.write(f_in.read())

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"ONNX model file not found at: {self.model_path}")

        logger.info(f"Loading ONNX model from: {self.model_path}")
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.intra_op_num_threads = self.num_threads
        opts.inter_op_num_threads = 1

        available_providers = ort.get_available_providers()
        providers = [self.execution_provider]
        if self.execution_provider not in available_providers:
            logger.warning(
                f"Requested provider '{self.execution_provider}' not in {available_providers}. Falling back to CPU."
            )
            providers = ["CPUExecutionProvider"]

        session = ort.InferenceSession(self.model_path, opts, providers=providers)

        # Initialize tokenizer
        tokenizer = ModerationTokenizer(
            model_name_or_path=(
                self.tokenizer_path
                if os.path.exists(self.tokenizer_path)
                else "distilbert-base-uncased"
            ),
            max_length=self.max_length,
        )

        return session, tokenizer

    def warmup(self, num_iterations: int = 3) -> None:
        """Execute warmup iterations to prime graph caches and kernels."""
        logger.info(f"Warming up ONNX engine ({num_iterations} iterations)...")
        dummy_text = "System warmup message for neural network inference cache."
        for _ in range(num_iterations):
            self.predict([dummy_text])
        logger.info("ONNX engine warmup complete.")

    def predict(
        self,
        texts: Union[str, List[str]],
    ) -> Tuple[np.ndarray, float]:
        """Run batch inference on one or more texts.

        Args:
            texts: Single text or list of texts.

        Returns:
            Tuple of (logits ndarray [batch_size, 2], inference_time_ms float).
        """
        if isinstance(texts, str):
            texts = [texts]

        t0 = time.perf_counter()

        tokens = self.tokenizer.tokenize(
            texts,
            padding=True,
            truncation=True,
        )

        ort_inputs = {
            "input_ids": tokens["input_ids"],
            "attention_mask": tokens["attention_mask"],
        }

        ort_outputs = self.session.run(["logits"], ort_inputs)
        logits = ort_outputs[0]

        inference_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return logits, inference_ms


def get_onnx_engine() -> ONNXInferenceEngine:
    """Retrieve or initialize singleton ONNX inference engine."""
    if ONNXInferenceEngine._instance is None:
        ONNXInferenceEngine._instance = ONNXInferenceEngine()
    return ONNXInferenceEngine._instance
