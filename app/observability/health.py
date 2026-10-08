"""Health, readiness, and system telemetry probes."""

import os
from typing import Any, Dict

import psutil

from app.core.config import get_settings
from app.inference.model_manager import get_model_manager


class HealthChecker:
    """Provides system health, memory, and model readiness status."""

    def __init__(self):
        self.settings = get_settings()
        self.model_manager = get_model_manager()

    def check_liveness(self) -> Dict[str, Any]:
        """Liveness check verifying the application process is alive."""
        return {
            "status": "healthy",
            "app_name": self.settings.app_name,
            "version": self.settings.app_version,
            "environment": self.settings.app_env,
        }

    def check_readiness(self) -> Dict[str, Any]:
        """Readiness check verifying model loading and memory status."""
        is_ready = self.model_manager.is_ready()
        model_info = self.model_manager.get_info()

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


_health_checker = None


def get_health_checker() -> HealthChecker:
    """Retrieve singleton HealthChecker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
