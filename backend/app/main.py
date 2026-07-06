"""
PRISM Backend — FastAPI Application Entry Point.

This module creates and configures the FastAPI application.
It is the entry point for Uvicorn:
    uvicorn app.main:app --reload --port 8000

Responsibilities:
- Create FastAPI application instance
- Configure CORS for frontend communication
- Register all API routers
- Manage application lifecycle (startup/shutdown)
- Provide OpenAPI documentation
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.integrations.firestore import get_firestore_client
from app.integrations.vertex_ai import get_gemini_model
from app.routers import health, ingest, analysis, interventions, simulation, memory
from app.utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Runs startup logic before the application begins accepting requests,
    and shutdown logic when the application is stopping.

    Startup:
    - Initialize Firestore connection
    - Initialize Vertex AI / Gemini model
    - Log configuration summary

    Shutdown:
    - Log shutdown message
    """
    settings = get_settings()
    logger.info(
        "Starting PRISM backend | env=%s | version=%s",
        settings.app_env,
        settings.app_version,
    )

    # Initialize connections at startup so first request is not slow
    try:
        get_firestore_client()
        logger.info("Firestore client initialized at startup")
    except Exception as exc:
        logger.error("Failed to initialize Firestore at startup: %s", exc)
        raise

    try:
        get_gemini_model()
        logger.info("Vertex AI model initialized at startup")
    except Exception as exc:
        logger.error("Failed to initialize Vertex AI at startup: %s", exc)
        raise

    logger.info("PRISM backend is ready to accept requests")

    yield

    logger.info("PRISM backend shutting down")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    application = FastAPI(
        title="PRISM — Decision Intelligence API",
        description=(
            "AI-powered Decision Intelligence System for community health "
            "and environmental intervention. Transforms multimodal community "
            "data into explainable, simulated, and optimized decisions."
        ),
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    # Register routers
    application.include_router(health.router, prefix="/api/v1")
    application.include_router(ingest.router, prefix="/api/v1")
    application.include_router(analysis.router, prefix="/api/v1")
    application.include_router(interventions.router, prefix="/api/v1")
    application.include_router(simulation.router, prefix="/api/v1")
    application.include_router(memory.router, prefix="/api/v1")

    logger.info(
        "PRISM application configured | CORS origins=%s",
        settings.allowed_origins_list,
    )

    return application


app = create_application()