"""Model lifecycle management, status inspection, and reloading."""

from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.core.logging import logger
from app.inference.onnx_engine import ONNXInferenceEngine, get_onnx_engine


class ModelManager:
    """Manages model lifecycle, health, metadata, and memory status."""

    _instance: Optional["ModelManager"] = None

    def __init__(self):
        self.settings = get_settings()
        self._engine: Optional[ONNXInferenceEngine] = None

    def initialize(self) -> None:
        """Initialize the model engine and verify ready state."""
        logger.info("Initializing ModelManager...")
        self._engine = get_onnx_engine()
        logger.info(f"ModelManager ready with model: {self._engine.model_version}")

    @property
    def engine(self) -> ONNXInferenceEngine:
        if self._engine is None:
            self.initialize()
        if self._engine is None:
            raise RuntimeError("Failed to initialize ONNX inference engine")
        return self._engine

    def is_ready(self) -> bool:
        """Check whether the model is loaded and ready for inference."""
        return self._engine is not None and self._engine.session is not None

    def get_info(self) -> Dict[str, Any]:
        """Return runtime metadata about the loaded model."""
        eng = self.engine
        return {
            "model_version": eng.model_version,
            "engine": "ONNX Runtime",
            "execution_provider": eng.execution_provider,
            "max_sequence_length": eng.max_length,
            "threads": eng.num_threads,
            "ready": self.is_ready(),
        }


def get_model_manager() -> ModelManager:
    """Retrieve or initialize singleton ModelManager."""
    if ModelManager._instance is None:
        ModelManager._instance = ModelManager()
    return ModelManager._instance
