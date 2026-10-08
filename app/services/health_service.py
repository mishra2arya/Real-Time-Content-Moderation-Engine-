"""Health, readiness, and system telemetry service."""

import os
from typing import Any, Dict

import psutil

from app.core.config import get_settings
from app.inference.model_manager import get_model_manager


class HealthService:
    """Provides system health, memory, and model readiness status."""

    def __init__(self):
        self.settings = get_settings()
        self.model_manager = get_model_manager()

    def get_health(self) -> Dict[str, Any]:
        """Liveness check verifying the application process is alive."""
        return {
            "status": "healthy",
            "app_name": self.settings.app_name,
            "version": self.settings.app_version,
            "environment": self.settings.app_env,
        }

    def get_readiness(self) -> Dict[str, Any]:
        """Readiness check verifying model loading and system resources."""
        is_ready = self.model_manager.is_ready()
        model_info = self.model_manager.get_info()

        # Telemetry
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        return {
            "status": "ready" if is_ready else "not_ready",
            "model_ready": is_ready,
            "model_info": model_info,
            "system": {
                "memory_rss_mb": round(mem_info.rss / (1024 * 1024), 2),
                "cpu_percent": process.cpu_percent(interval=None),
                "num_threads": process.num_threads(),
            },
        }


_health_service = None


def get_health_service() -> HealthService:
    global _health_service
    if _health_service is None:
        _health_service = HealthService()
    return _health_service
