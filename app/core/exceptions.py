"""Centralized application exceptions and error definitions."""

from fastapi import status


class ModerationEngineException(Exception):
    """Base exception for all domain errors within the moderation engine."""

    def __init__(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ModelNotReadyException(ModerationEngineException):
    """Raised when an inference request is received before the model has finished loading."""

    def __init__(
        self,
        message: str = "Model engine is warming up or not ready to receive traffic",
    ):
        super().__init__(
            message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class InvalidPayloadException(ModerationEngineException):
    """Raised when an input payload fails domain-specific validation constraints."""

    def __init__(self, message: str):
        super().__init__(
            message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class QueueCapacityExceededException(ModerationEngineException):
    """Raised when dynamic micro-batching queue capacity is exceeded (backpressure)."""

    def __init__(
        self, message: str = "Moderation request rejected due to queue overload"
    ):
        super().__init__(message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class InferenceTimeoutException(ModerationEngineException):
    """Raised when inference forward-pass exceeds configured time boundary."""

    def __init__(self, message: str = "Inference execution timed out"):
        super().__init__(message=message, status_code=status.HTTP_504_GATEWAY_TIMEOUT)
