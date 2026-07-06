"""
Health check router for PRISM backend.

Provides endpoints that:
1. Confirm the service is running (liveness check)
2. Confirm all dependencies are reachable (readiness check)

Cloud Run uses the /health endpoint to determine container health.
The frontend and monitoring systems use this to verify service status.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.integrations.firestore import get_firestore_client
from app.integrations.vertex_ai import get_gemini_model
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


class ServiceStatus(BaseModel):
    """Status of an individual dependency."""

    name: str
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Complete health check response."""

    status: str
    version: str
    environment: str
    timestamp: str
    services: list[ServiceStatus]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check endpoint.

    Checks:
    - Application is running
    - Firestore is reachable
    - Vertex AI model is initialized

    Returns 200 if all services are healthy.
    Returns 503 if any critical service is unreachable.
    """
    settings = get_settings()
    services: list[ServiceStatus] = []
    overall_healthy = True

    # Check Firestore connectivity
    try:
        client = get_firestore_client()
        # Perform a lightweight read to verify connectivity
        client.collection("_health_check").limit(1).get()
        services.append(
            ServiceStatus(
                name="firestore",
                status="healthy",
                detail="Connection verified",
            )
        )
        logger.debug("Firestore health check passed")
    except Exception as exc:
        overall_healthy = False
        services.append(
            ServiceStatus(
                name="firestore",
                status="unhealthy",
                detail=str(exc),
            )
        )
        logger.error("Firestore health check failed: %s", exc)

    # Check Vertex AI initialization
    try:
        model = get_gemini_model()
        services.append(
            ServiceStatus(
                name="vertex_ai",
                status="healthy",
                detail=f"Model {settings.vertex_ai_model_id} initialized",
            )
        )
        logger.debug("Vertex AI health check passed")
    except Exception as exc:
        overall_healthy = False
        services.append(
            ServiceStatus(
                name="vertex_ai",
                status="unhealthy",
                detail=str(exc),
            )
        )
        logger.error("Vertex AI health check failed: %s", exc)

    response = HealthResponse(
        status="healthy" if overall_healthy else "degraded",
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
    )

    if not overall_healthy:
        raise HTTPException(status_code=503, detail=response.model_dump())

    return response


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """
    Minimal liveness check.

    Returns immediately without checking dependencies.
    Used by Cloud Run to determine if the container should be restarted.
    """
    return {"status": "alive"}

@router.get("/cities")
async def list_cities() -> dict:
    """
    Return the list of supported cities.

    Used by the frontend to populate the city selector dropdown.
    """
    from app.config_cities import get_all_city_summaries
    return {"cities": get_all_city_summaries()}