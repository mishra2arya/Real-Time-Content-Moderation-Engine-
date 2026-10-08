"""FastAPI application entrypoint with lifespan events, Prometheus metrics, and middleware."""

import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import ModerationEngineException
from app.core.logging import logger
from app.inference.batching import get_batching_engine
from app.inference.model_manager import get_model_manager
from app.observability.metrics import (
    REQUEST_LATENCY_HISTOGRAM,
    REQUESTS_TOTAL,
    get_metrics_content_type,
    get_metrics_latest,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup priming and graceful shutdown."""
    settings = get_settings()
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} ({settings.app_env})..."
    )

    # 1. Initialize and warm up ONNX inference engine
    model_mgr = get_model_manager()
    model_mgr.initialize()

    # 2. Start asynchronous batching worker
    batch_engine = get_batching_engine()
    await batch_engine.start()

    logger.info(
        "Application startup and model pre-warming complete. Accepting traffic."
    )
    yield

    # Graceful shutdown
    logger.info("Shutting down application...")
    await batch_engine.stop()
    logger.info("Cleanup completed successfully.")


def create_app() -> FastAPI:
    """Application factory for FastAPI service."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="High-throughput real-time content moderation engine powered by DistilBERT and ONNX Runtime.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and Metrics Middleware
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = req_id

        endpoint = request.url.path
        method = request.method
        t0 = time.perf_counter()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            REQUESTS_TOTAL.labels(
                endpoint=endpoint, method=method, status=status_code
            ).inc()
            raise exc

        latency = time.perf_counter() - t0

        # Exclude telemetry probes from application latency distribution metrics
        if endpoint not in ("/metrics", "/health", "/ready", "/version"):
            REQUESTS_TOTAL.labels(
                endpoint=endpoint, method=method, status=status_code
            ).inc()
            REQUEST_LATENCY_HISTOGRAM.labels(endpoint=endpoint).observe(latency)

        response.headers["X-Request-ID"] = req_id
        return response

    # Prometheus Metrics Exposition Endpoint
    @app.get("/metrics", tags=["Telemetry"], summary="Expose Prometheus metrics")
    def metrics():
        return Response(get_metrics_latest(), media_type=get_metrics_content_type())

    # Include API Routers
    app.include_router(router)

    # Custom Domain Exception Handler
    @app.exception_handler(ModerationEngineException)
    async def domain_exception_handler(
        request: Request, exc: ModerationEngineException
    ):
        logger.warning(f"Domain exception on {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "detail": exc.message,
                "status_code": exc.status_code,
            },
        )

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while processing the request.",
                "status_code": 500,
            },
        )

    # Serve static frontend dashboard if built
    frontend_dist = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist"
    )
    if os.path.isdir(frontend_dist):
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app


app = create_app()
