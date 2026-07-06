"""
Simulation router for PRISM.

Exposes endpoints for running and retrieving scenario simulations.
Simulation requires interventions to have been generated first.
"""

from fastapi import APIRouter, HTTPException, status

from app.models.simulation import RunSimulationRequest, SimulationListResponse
from app.services.simulation.simulation_service import (
    get_simulation_results,
    run_simulation,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post(
    "/run",
    response_model=SimulationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Run scenario simulation",
    description=(
        "Simulates 30-day outcomes for all intervention strategies "
        "associated with an analysis. Scores each strategy across "
        "5 dimensions and computes composite PRISM Scores for ranking."
    ),
)
async def run_scenario_simulation(
    request: RunSimulationRequest,
) -> SimulationListResponse:
    """
    Run scenario simulation for all interventions in an analysis.

    Requires:
    - A completed situation analysis (status=complete)
    - At least one generated intervention strategy

    Returns ranked simulation results with PRISM Scores.
    Takes 20-45 seconds due to Gemini API latency.
    """
    logger.info(
        "Simulation requested: analysis_id=%s intervention_ids=%s",
        request.analysis_id,
        request.intervention_ids,
    )

    try:
        result = await run_simulation(request)
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Simulation endpoint failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(exc)}",
        )


@router.get(
    "/{analysis_id}",
    response_model=SimulationListResponse,
    summary="Get simulation results",
    description="Retrieve stored simulation results for an analysis.",
)
async def get_simulation(analysis_id: str) -> SimulationListResponse:
    """Retrieve simulation results for an analysis."""
    try:
        return await get_simulation_results(analysis_id)
    except Exception as exc:
        logger.error(
            "Failed to retrieve simulation for %s: %s", analysis_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve simulation: {str(exc)}",
        )