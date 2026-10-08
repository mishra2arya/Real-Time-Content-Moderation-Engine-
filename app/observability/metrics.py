"""Prometheus metrics definitions and exposition helpers."""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# Operational request counters
REQUESTS_TOTAL = Counter(
    "moderation_requests_total",
    "Total incoming moderation API requests",
    ["endpoint", "method", "status"],
)

# Policy decision counters
DECISIONS_TOTAL = Counter(
    "moderation_decisions_total",
    "Total policy decisions rendered",
    ["decision", "label"],
)

# End-to-end API latency histogram (in seconds)
REQUEST_LATENCY_HISTOGRAM = Histogram(
    "moderation_latency_seconds",
    "End-to-end request latency in seconds",
    ["endpoint"],
    buckets=[0.005, 0.010, 0.020, 0.035, 0.048, 0.075, 0.100, 0.250, 0.500, 1.0],
)

# Dedicated ONNX Runtime forward-pass latency histogram (in seconds)
INFERENCE_LATENCY_HISTOGRAM = Histogram(
    "moderation_inference_latency_seconds",
    "ONNX Runtime model inference latency in seconds",
    buckets=[0.002, 0.005, 0.010, 0.020, 0.035, 0.048, 0.075, 0.100],
)

# Vector batch size histogram
BATCH_SIZE_HISTOGRAM = Histogram(
    "moderation_batch_size",
    "Distribution of batch sizes processed",
    buckets=[1, 2, 4, 8, 16, 32, 64, 128],
)


def get_metrics_latest() -> bytes:
    """Export all registered Prometheus metrics in text exposition format."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Return standard Prometheus media type."""
    return CONTENT_TYPE_LATEST
