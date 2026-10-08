"""Pydantic v2 schemas for API requests, responses, versioning, and telemetry."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ModerationRequest(BaseModel):
    """Payload for single text moderation."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text content to be evaluated for policy compliance.",
        examples=["Have a wonderful day!"],
    )
    text_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Optional client-provided correlation or tracking identifier.",
        examples=["msg-12345"],
    )
    strict: bool = Field(
        default=False,
        description="Whether to evaluate using strict, lowered toxicity thresholds.",
    )


class ModerationResponse(BaseModel):
    """Structured policy evaluation outcome for a single text."""

    text_id: Optional[str] = Field(
        default=None, description="Request or message identifier."
    )
    request_id: Optional[str] = Field(
        default=None, description="Distributed tracing identifier."
    )
    decision: str = Field(
        ...,
        description="Actionable business decision: 'allow', 'block', or 'flag_review'.",
    )
    label: str = Field(
        ..., description="Classification category: 'non_toxic' or 'toxic'."
    )
    confidence: float = Field(
        ..., description="Model classification probability score."
    )
    policy_category: Optional[str] = Field(
        default=None,
        description="Primary violation category if policy breached (e.g. 'threat', 'insult', 'toxicity').",
    )
    policy_categories: List[str] = Field(
        default_factory=list,
        description="Granular violation categories detected.",
    )
    model_version: str = Field(
        ..., description="Version identifier of the deployed model."
    )
    inference_ms: float = Field(
        ..., description="Model forward-pass latency in milliseconds."
    )
    total_latency_ms: float = Field(
        ..., description="End-to-end request processing latency in milliseconds."
    )


class BatchItem(BaseModel):
    """Individual item inside a batch request."""

    text: str = Field(..., min_length=1, max_length=10000)
    text_id: Optional[str] = Field(default=None, max_length=128)


class BatchModerationRequest(BaseModel):
    """Payload for high-throughput multi-item batch moderation."""

    items: List[BatchItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of text items to evaluate concurrently (maximum 100 per request).",
    )
    strict: bool = Field(
        default=False,
        description="Whether to apply strict policy thresholds across the batch.",
    )


class BatchModerationResponse(BaseModel):
    """Outcome for batched moderation requests."""

    results: List[ModerationResponse] = Field(
        ..., description="List of moderation decisions."
    )
    batch_size: int = Field(..., description="Total items processed.")
    total_latency_ms: float = Field(
        ..., description="Total processing time for the batch in milliseconds."
    )


class HealthResponse(BaseModel):
    """Liveness probe status."""

    status: str
    app_name: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness probe status."""

    status: str
    model_ready: bool
    model_info: Dict[str, Any]
    system: Dict[str, Any]


class VersionResponse(BaseModel):
    """Service version and build metadata."""

    app_name: str
    app_version: str
    model_version: str
    inference_engine: str
    python_version: str
    status: str


class ErrorResponse(BaseModel):
    """Structured error payload."""

    error: str
    detail: Optional[str] = None
    status_code: int
