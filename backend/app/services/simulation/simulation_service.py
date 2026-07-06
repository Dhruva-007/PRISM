"""
Simulation service for PRISM.

Orchestrates scenario simulation:
1. Fetch analysis and interventions from Firestore
2. Run Gemini simulation
3. Store results and update intervention PRISM scores
4. Return ranked results
"""

from app.integrations.firestore import get_firestore_client
from app.models.intervention import InterventionStrategy
from app.models.simulation import (
    RunSimulationRequest,
    SimulationListResponse,
    SimulationResult,
)
from app.services.intelligence.analysis_service import get_analysis
from app.services.simulation.scenario_engine import simulate_strategies
from app.utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_SIMULATIONS = "simulation_results"
COLLECTION_INTERVENTIONS = "intervention_strategies"


async def run_simulation(
    request: RunSimulationRequest,
) -> SimulationListResponse:
    """
    Run scenario simulation for all interventions in an analysis.

    Args:
        request: RunSimulationRequest with analysis_id

    Returns:
        SimulationListResponse with ranked results

    Raises:
        ValueError: If analysis not found or has no interventions
    """
    analysis = await get_analysis(request.analysis_id)
    if analysis is None:
        raise ValueError(f"Analysis {request.analysis_id} not found")

    client = get_firestore_client()

    if request.intervention_ids:
        strategies = []
        for iid in request.intervention_ids:
            doc = client.collection(COLLECTION_INTERVENTIONS).document(iid).get()
            if doc.exists:
                data = doc.to_dict()
                if data:
                    data["id"] = doc.id
                    try:
                        strategies.append(InterventionStrategy(**data))
                    except Exception as exc:
                        logger.warning("Failed to parse intervention %s: %s", iid, exc)
    else:
        query = (
            client.collection(COLLECTION_INTERVENTIONS)
            .where("analysis_id", "==", request.analysis_id)
            .order_by("rank")
        )
        docs = list(query.stream())
        strategies = []
        for doc in docs:
            data = doc.to_dict()
            if data:
                data["id"] = doc.id
                try:
                    strategies.append(InterventionStrategy(**data))
                except Exception as exc:
                    logger.warning("Failed to parse intervention %s: %s", doc.id, exc)

    if not strategies:
        raise ValueError(
            f"No interventions found for analysis {request.analysis_id}. "
            "Generate interventions first."
        )

    logger.info(
        "Running simulation for %d strategies | analysis=%s",
        len(strategies),
        request.analysis_id,
    )

    results = await simulate_strategies(analysis, strategies)

    if not results:
        raise ValueError("Simulation produced no results — Gemini may have failed")

    stored_results = []
    recommended_id = None

    for result in results:
        doc_ref = client.collection(COLLECTION_SIMULATIONS).document()
        result.id = doc_ref.id
        doc_ref.set(result.to_firestore_dict())

        if result.is_recommended:
            recommended_id = result.intervention_id

        intervention_ref = client.collection(COLLECTION_INTERVENTIONS).document(
            result.intervention_id
        )
        intervention_ref.update({
            "prism_score": result.scores.composite_prism_score,
            "rank": result.rank_among_strategies,
        })

        stored_results.append(result)
        logger.info(
            "Stored simulation: %s | PRISM Score: %.1f | Rank: %d",
            result.intervention_title,
            result.scores.composite_prism_score,
            result.rank_among_strategies or 0,
        )

    return SimulationListResponse(
        results=stored_results,
        analysis_id=request.analysis_id,
        total=len(stored_results),
        recommended_intervention_id=recommended_id,
    )


async def get_simulation_results(
    analysis_id: str,
) -> SimulationListResponse:
    """
    Retrieve stored simulation results for an analysis.

    Args:
        analysis_id: The situation analysis ID

    Returns:
        SimulationListResponse with stored results ordered by rank
    """
    client = get_firestore_client()

    from google.cloud.firestore_v1.base_query import FieldFilter
    query = (
        client.collection(COLLECTION_SIMULATIONS)
        .where(filter=FieldFilter("analysis_id", "==", analysis_id))
    )

    docs = list(query.stream())
    results = []
    recommended_id = None

    for doc in docs:
        data = doc.to_dict()
        if data:
            data["id"] = doc.id
            try:
                result = SimulationResult(**data)
                results.append(result)
                if result.is_recommended:
                    recommended_id = result.intervention_id
            except Exception as exc:
                logger.warning(
                    "Failed to parse simulation %s: %s", doc.id, exc
                )

    results.sort(key=lambda r: r.rank_among_strategies or 999)

    return SimulationListResponse(
        results=results,
        analysis_id=analysis_id,
        total=len(results),
        recommended_intervention_id=recommended_id,
    )