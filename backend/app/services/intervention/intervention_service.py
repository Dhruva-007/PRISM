"""
Intervention service for PRISM.

Orchestrates intervention generation:
1. Fetch the situation analysis from Firestore
2. Call the generator (Gemini)
3. Store generated strategies in Firestore
4. Return structured response

Also handles retrieval of stored interventions.
"""

from app.integrations.firestore import get_firestore_client
from app.models.intervention import (
    GenerateInterventionsRequest,
    InterventionListResponse,
    InterventionStrategy,
)
from app.services.intelligence.analysis_service import get_analysis
from app.services.intervention.generator import generate_interventions
from app.utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_INTERVENTIONS = "intervention_strategies"


async def create_interventions(
    request: GenerateInterventionsRequest,
) -> InterventionListResponse:
    """
    Generate and store intervention strategies for an analysis.

    Args:
        request: GenerateInterventionsRequest with analysis_id

    Returns:
        InterventionListResponse with generated strategies

    Raises:
        ValueError: If analysis not found or incomplete
    """
    analysis = await get_analysis(request.analysis_id)

    if analysis is None:
        raise ValueError(f"Analysis {request.analysis_id} not found")

    if analysis.status.value != "complete":
        raise ValueError(
            f"Analysis {request.analysis_id} is not complete "
            f"(status: {analysis.status}). Run analysis first."
        )

    strategies = await generate_interventions(
        analysis=analysis,
        num_strategies=request.num_strategies,
    )

    if not strategies:
        raise ValueError(
            "Intervention generation failed — Gemini returned no strategies"
        )

    client = get_firestore_client()
    stored_strategies = []

    for i, strategy in enumerate(strategies):
        strategy.rank = i + 1

        doc_ref = client.collection(COLLECTION_INTERVENTIONS).document()
        strategy.id = doc_ref.id
        doc_ref.set(strategy.to_firestore_dict())
        stored_strategies.append(strategy)

        logger.info(
            "Stored strategy %d/%d: %s (id=%s)",
            i + 1,
            len(strategies),
            strategy.title,
            strategy.id,
        )

    logger.info(
        "Stored %d intervention strategies for analysis %s",
        len(stored_strategies),
        request.analysis_id,
    )

    return InterventionListResponse(
        strategies=stored_strategies,
        analysis_id=request.analysis_id,
        total=len(stored_strategies),
    )


async def get_interventions_for_analysis(
    analysis_id: str,
) -> InterventionListResponse:
    """
    Retrieve stored intervention strategies for an analysis.

    Args:
        analysis_id: The situation analysis ID

    Returns:
        InterventionListResponse with stored strategies
    """
    client = get_firestore_client()

    from google.cloud.firestore_v1.base_query import FieldFilter
    query = (
        client.collection(COLLECTION_INTERVENTIONS)
        .where(filter=FieldFilter("analysis_id", "==", analysis_id))
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
                logger.warning(
                    "Failed to parse intervention %s: %s", doc.id, exc
                )

    return InterventionListResponse(
        strategies=strategies,
        analysis_id=analysis_id,
        total=len(strategies),
    )


async def list_all_interventions(limit: int = 20) -> InterventionListResponse:
    """
    Retrieve the most recently created intervention strategies.

    Args:
        limit: Maximum number of strategies to return

    Returns:
        InterventionListResponse
    """
    client = get_firestore_client()

    query = (
        client.collection(COLLECTION_INTERVENTIONS)
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
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
                logger.warning(
                    "Failed to parse intervention %s: %s", doc.id, exc
                )

    return InterventionListResponse(
        strategies=strategies,
        analysis_id="",
        total=len(strategies),
    )