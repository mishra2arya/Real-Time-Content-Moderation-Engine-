"""Unit tests for configuration and Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas import BatchModerationRequest, ModerationRequest
from app.core.config import Settings


def test_settings_defaults():
    """Verify standard default configuration values."""
    s = Settings()
    assert s.app_name == "Real-Time Content Moderation Engine"
    assert s.port == 8000
    assert s.default_toxicity_threshold == 0.50
    assert s.max_sequence_length == 128


def test_moderation_request_schema_valid():
    """Valid request schema should parse properly."""
    req = ModerationRequest(text="Hello world", text_id="req-1", strict=False)
    assert req.text == "Hello world"
    assert req.text_id == "req-1"
    assert req.strict is False


def test_moderation_request_schema_empty():
    """Empty text string should trigger validation error."""
    with pytest.raises(ValidationError):
        ModerationRequest(text="")


def test_batch_request_schema_limit():
    """Batch cannot exceed 100 items."""
    items = [{"text": f"message {i}"} for i in range(101)]
    with pytest.raises(ValidationError):
        BatchModerationRequest(items=items)
