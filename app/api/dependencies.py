"""FastAPI dependency injection providers."""

from typing import Optional

from app.services.health_service import HealthService, get_health_service
from app.services.moderation_service import ModerationService

_moderation_service: Optional[ModerationService] = None


def get_moderation_service() -> ModerationService:
    """Provide singleton ModerationService instance."""
    global _moderation_service
    if _moderation_service is None:
        _moderation_service = ModerationService()
    return _moderation_service


def get_health_service_dep() -> HealthService:
    """Provide HealthService instance."""
    return get_health_service()
