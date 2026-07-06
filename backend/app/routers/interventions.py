"""
Interventions router for PRISM.

Exposes endpoints for generating and retrieving intervention strategies.
Intervention generation requires a completed situation analysis.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.models.intervention import (
    GenerateInterventionsRequest,
    InterventionListResponse,
)
from app.services.intervention.intervention_service import (
    create_interventions,
    get_interventions_for_analysis,
    list_all_interventions,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/interventions", tags=["interventions"])


@router.post(
    "/generate",
    response_model=InterventionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate intervention strategies",
    description=(
        "Generates multiple distinct intervention strategies for a completed "
        "situation analysis using Gemini 2.5 Flash. "
        "Requires the analysis to have status=complete."
    ),
)
async def generate_interventions(
    request: GenerateInterventionsRequest,
) -> InterventionListResponse:
    """
    Generate intervention strategies for a situation analysis.

    This endpoint:
    1. Fetches the analysis from Firestore
    2. Sends it to Gemini with a structured intervention prompt
    3. Parses and validates the response
    4. Stores all strategies in Firestore
    5. Returns the complete list

    Note: Takes 15-40 seconds due to Gemini API latency.
    """
    logger.info(
        "Intervention generation requested: analysis_id=%s num_strategies=%d",
        request.analysis_id,
        request.num_strategies,
    )

    try:
        result = await create_interventions(request)
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Intervention generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intervention generation failed: {str(exc)}",
        )


@router.get(
    "",
    response_model=InterventionListResponse,
    summary="List recent intervention strategies",
    description="Retrieve the most recently generated intervention strategies.",
)
async def list_interventions(
    analysis_id: str | None = Query(
        default=None,
        description="Filter by analysis ID",
    ),
    limit: int = Query(default=20, ge=1, le=100),
) -> InterventionListResponse:
    """Retrieve intervention strategies."""
    try:
        if analysis_id:
            return await get_interventions_for_analysis(analysis_id)
        return await list_all_interventions(limit=limit)
    except Exception as exc:
        logger.error("Failed to list interventions: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interventions: {str(exc)}",
        )