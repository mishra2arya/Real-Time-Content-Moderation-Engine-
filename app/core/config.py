"""Application configuration management with environment variable overrides."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings definition for the Real-Time Content Moderation Engine."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Meta
    app_name: str = Field(
        default="Real-Time Content Moderation Engine", alias="APP_NAME"
    )
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_env: str = Field(default="production", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Model & Inference
    model_name: str = Field(default="distilbert-base-uncased", alias="MODEL_NAME")
    model_onnx_path: str = Field(
        default="models/onnx/model.onnx", alias="MODEL_ONNX_PATH"
    )
    model_pytorch_path: str = Field(
        default="models/pytorch", alias="MODEL_PYTORCH_PATH"
    )
    max_sequence_length: int = Field(default=128, alias="MAX_SEQUENCE_LENGTH")
    inference_engine: str = Field(
        default="onnx", alias="INFERENCE_ENGINE"
    )  # onnx or pytorch
    execution_provider: str = Field(
        default="CPUExecutionProvider", alias="EXECUTION_PROVIDER"
    )
    num_threads: int = Field(default=4, alias="NUM_THREADS")

    # Policy & Thresholds
    default_toxicity_threshold: float = Field(
        default=0.50, alias="DEFAULT_TOXICITY_THRESHOLD"
    )
    strict_toxicity_threshold: float = Field(
        default=0.35, alias="STRICT_TOXICITY_THRESHOLD"
    )
    flag_review_threshold: float = Field(default=0.40, alias="FLAG_REVIEW_THRESHOLD")

    # Batching & Concurrency
    batch_max_size: int = Field(default=64, alias="BATCH_MAX_SIZE")
    batch_timeout_ms: int = Field(default=5, alias="BATCH_TIMEOUT_MS")
    max_concurrent_requests: int = Field(default=100, alias="MAX_CONCURRENT_REQUESTS")
    max_payload_chars: int = Field(default=10000, alias="MAX_PAYLOAD_CHARS")

    # Security
    api_key: Optional[str] = Field(default=None, alias="API_KEY")
    require_api_key: bool = Field(default=False, alias="REQUIRE_API_KEY")


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
