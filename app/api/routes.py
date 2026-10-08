"""API route definitions for content moderation, batching, version, and health checks."""

import sys
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import get_health_service_dep, get_moderation_service
from app.api.schemas import (
    BatchModerationRequest,
    BatchModerationResponse,
    HealthResponse,
    ModerationRequest,
    ModerationResponse,
    ReadinessResponse,
    VersionResponse,
)
from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import verify_api_key
from app.services.health_service import HealthService
from app.services.moderation_service import ModerationService

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Telemetry"],
    summary="Service liveness probe",
)
async def health_check(
    health_service: HealthService = Depends(get_health_service_dep),
) -> HealthResponse:
    """Check whether the service process is alive."""
    return HealthResponse(**health_service.get_health())


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    tags=["Telemetry"],
    summary="Service readiness probe",
)
async def readiness_check(
    health_service: HealthService = Depends(get_health_service_dep),
) -> ReadinessResponse:
    """Check whether model sessions and required resources are loaded."""
    ready_data = health_service.get_readiness()
    if not ready_data.get("model_ready", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready to receive traffic",
        )
    return ReadinessResponse(**ready_data)


@router.get(
    "/version",
    response_model=VersionResponse,
    tags=["Telemetry"],
    summary="Service version and build metadata",
)
async def version_info(
    health_service: HealthService = Depends(get_health_service_dep),
) -> VersionResponse:
    """Return application version, model version, and runtime platform."""
    settings = get_settings()
    model_info = health_service.model_manager.get_info()
    return VersionResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        model_version=model_info.get("model_version", "unknown"),
        inference_engine=model_info.get("engine", "ONNX Runtime"),
        python_version=sys.version.split()[0],
        status="active",
    )


@router.post(
    "/moderate",
    response_model=ModerationResponse,
    tags=["Moderation"],
    summary="Evaluate single text for policy violations",
)
async def moderate(
    payload: ModerationRequest,
    request: Request,
    moderation_service: ModerationService = Depends(get_moderation_service),
    _: Optional[str] = Depends(verify_api_key),
) -> ModerationResponse:
    """Perform real-time moderation on an incoming text message."""
    req_id = getattr(request.state, "request_id", None)
    try:
        result = await moderation_service.moderate_text(
            text=payload.text,
            text_id=payload.text_id,
            strict=payload.strict,
            use_batch_queue=False,
        )

        primary_category = (
            result.policy_categories[0] if result.policy_categories else None
        )

        logger.info(
            "Moderation completed",
            extra={
                "request_id": req_id or payload.text_id,
                "endpoint": "/moderate",
                "method": "POST",
                "status_code": 200,
                "decision": result.decision.value,
                "label": result.label,
                "confidence": result.confidence,
                "inference_ms": result.inference_ms,
                "total_latency_ms": result.total_latency_ms,
                "model_version": result.model_version,
            },
        )

        return ModerationResponse(
            text_id=result.text_id,
            request_id=req_id,
            decision=result.decision.value,
            label=result.label,
            confidence=result.confidence,
            policy_category=primary_category,
            policy_categories=result.policy_categories,
            model_version=result.model_version,
            inference_ms=result.inference_ms,
            total_latency_ms=result.total_latency_ms,
        )
    except Exception as e:
        logger.error(f"Failed to moderate request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}",
        ) from e


@router.post(
    "/moderate/batch",
    response_model=BatchModerationResponse,
    tags=["Moderation"],
    summary="Evaluate batch of texts for high-throughput stream processing",
)
async def moderate_batch(
    payload: BatchModerationRequest,
    request: Request,
    moderation_service: ModerationService = Depends(get_moderation_service),
    _: Optional[str] = Depends(verify_api_key),
) -> BatchModerationResponse:
    """Perform high-throughput batched moderation on multiple text messages."""
    req_id = getattr(request.state, "request_id", None)
    t_start = time.perf_counter()
    try:
        items = [{"text": it.text, "text_id": it.text_id} for it in payload.items]
        results = await moderation_service.moderate_batch(
            items=items,
            strict=payload.strict,
        )

        responses = [
            ModerationResponse(
                text_id=r.text_id,
                request_id=req_id,
                decision=r.decision.value,
                label=r.label,
                confidence=r.confidence,
                policy_category=r.policy_categories[0] if r.policy_categories else None,
                policy_categories=r.policy_categories,
                model_version=r.model_version,
                inference_ms=r.inference_ms,
                total_latency_ms=r.total_latency_ms,
            )
            for r in results
        ]

        batch_latency_ms = round((time.perf_counter() - t_start) * 1000.0, 3)

        logger.info(
            "Batch moderation completed",
            extra={
                "request_id": req_id,
                "endpoint": "/moderate/batch",
                "method": "POST",
                "status_code": 200,
                "batch_size": len(responses),
                "total_latency_ms": batch_latency_ms,
            },
        )

        return BatchModerationResponse(
            results=responses,
            batch_size=len(responses),
            total_latency_ms=batch_latency_ms,
        )
    except Exception as e:
        logger.error(f"Failed to process batch moderation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch inference error: {str(e)}",
        ) from e
