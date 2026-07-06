"""
Analysis router for PRISM Decision Intelligence Engine.

Exposes endpoints for running and retrieving situation analyses.
Analysis is computationally expensive (Gemini API call) so it is
triggered on-demand rather than continuously.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.models.analysis import (
    AnalysisListResponse,
    AnalysisRequest,
    AnalysisResponse,
)
from app.services.intelligence.analysis_service import (
    create_analysis,
    get_analysis,
    list_analyses,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post(
    "/run",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run situation analysis",
    description=(
        "Triggers the complete Decision Intelligence pipeline: "
        "context assembly → pattern detection → Gemini 2.5 reasoning → "
        "structured analysis stored in Firestore."
    ),
)
async def run_analysis(
    request: AnalysisRequest | None = None,
) -> AnalysisResponse:
    """
    Run a new situation analysis using Gemini 2.5 Flash.

    This endpoint:
    1. Gathers all recent community events from Firestore
    2. Detects statistical patterns
    3. Sends structured context to Gemini 2.5 Flash
    4. Returns a complete structured analysis

    Note: This call takes 10-30 seconds due to Gemini API latency.
    """
    if request is None:
        request = AnalysisRequest()

    logger.info(
        "Analysis requested: location=%s time_window=%dh",
        request.location,
        request.time_window_hours,
    )

    try:
        analysis = await create_analysis(request)
        return AnalysisResponse(analysis=analysis)
    except Exception as exc:
        logger.error("Analysis endpoint failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(exc)}",
        )


@router.get(
    "",
    response_model=AnalysisListResponse,
    summary="List analyses",
    description="Retrieve recent situation analyses ordered by creation time.",
)
async def get_analyses(
    limit: int = Query(default=20, ge=1, le=100),
) -> AnalysisListResponse:
    """Retrieve recent situation analyses."""
    try:
        return await list_analyses(limit=limit)
    except Exception as exc:
        logger.error("Failed to list analyses: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analyses: {str(exc)}",
        )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Get analysis by ID",
    description="Retrieve a single situation analysis by its Firestore document ID.",
)
async def get_analysis_by_id(analysis_id: str) -> AnalysisResponse:
    """Retrieve a single analysis by ID."""
    try:
        analysis = await get_analysis(analysis_id)
        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found",
            )
        return AnalysisResponse(analysis=analysis)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to retrieve analysis %s: %s", analysis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis: {str(exc)}",
        )