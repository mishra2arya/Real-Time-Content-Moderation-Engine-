"""Pytest test configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.inference.onnx_engine import ONNXInferenceEngine, get_onnx_engine
from app.main import app
from app.moderation.postprocessing import PolicyEngine
from app.services.moderation_service import ModerationService


@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI TestClient session fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def onnx_engine() -> ONNXInferenceEngine:
    """Initialized ONNX inference engine fixture."""
    return get_onnx_engine()


@pytest.fixture(scope="session")
def policy_engine() -> PolicyEngine:
    """Configured PolicyEngine fixture."""
    settings = get_settings()
    return PolicyEngine(
        block_threshold=settings.default_toxicity_threshold,
        flag_threshold=settings.flag_review_threshold,
        strict_threshold=settings.strict_toxicity_threshold,
    )


@pytest.fixture(scope="session")
def moderation_service() -> ModerationService:
    """ModerationService fixture."""
    return ModerationService()
