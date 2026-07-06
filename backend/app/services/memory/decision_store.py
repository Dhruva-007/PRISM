"""
Decision memory store for PRISM.

Handles storing, retrieving, and updating decision memory records.

The memory store is the organizational learning layer — it connects
past decisions to their actual outcomes so future analyses can
benefit from real-world feedback.
"""

from datetime import datetime, timezone

from google.cloud.firestore_v1.base_query import FieldFilter

from app.integrations.firestore import get_firestore_client
from app.models.memory import (
    DecisionMemoryListResponse,
    DecisionMemoryRecord,
    DecisionMemoryResponse,
    DecisionStatus,
    RecordDecisionRequest,
    RecordOutcomeRequest,
)
from app.services.intelligence.analysis_service import get_analysis
from app.services.intervention.intervention_service import COLLECTION_INTERVENTIONS
from app.utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_MEMORY = "decision_memory"


async def record_decision(
    request: RecordDecisionRequest,
    user_uid: str,
    user_name: str,
) -> DecisionMemoryResponse:
    """
    Record a decision made by a decision maker.

    Fetches the analysis and intervention details to create
    a complete, self-contained memory record.

    Args:
        request: RecordDecisionRequest with analysis and strategy IDs
        user_uid: Firebase UID of the decision maker
        user_name: Display name of the decision maker

    Returns:
        DecisionMemoryResponse with the created record

    Raises:
        ValueError: If analysis or strategy not found
    """
    client = get_firestore_client()

    analysis = await get_analysis(request.analysis_id)
    if analysis is None:
        raise ValueError(f"Analysis {request.analysis_id} not found")

    strategy_doc = (
        client.collection(COLLECTION_INTERVENTIONS)
        .document(request.selected_strategy_id)
        .get()
    )
    if not strategy_doc.exists:
        raise ValueError(
            f"Strategy {request.selected_strategy_id} not found"
        )

    strategy_data = strategy_doc.to_dict() or {}

    doc_ref = client.collection(COLLECTION_MEMORY).document()

    record = DecisionMemoryRecord(
        id=doc_ref.id,
        analysis_id=request.analysis_id,
        analysis_headline=analysis.headline,
        analysis_severity=analysis.severity_level.value,
        analysis_urgency=analysis.urgency.value,
        location=analysis.location,
        selected_strategy_id=request.selected_strategy_id,
        selected_strategy_title=strategy_data.get("title", "Unknown Strategy"),
        selected_strategy_type=strategy_data.get("strategy_type", "immediate"),
        prism_score_at_selection=strategy_data.get("prism_score"),
        rank_at_selection=strategy_data.get("rank"),
        selected_by_uid=user_uid,
        selected_by_name=user_name,
        selection_reason=request.selection_reason,
        status=DecisionStatus.SELECTED,
    )

    doc_ref.set(record.to_firestore_dict())

    logger.info(
        "Decision recorded: analysis=%s strategy=%s by=%s",
        request.analysis_id,
        request.selected_strategy_id,
        user_name,
    )

    return DecisionMemoryResponse(record=record)


async def update_outcome(
    memory_id: str,
    request: RecordOutcomeRequest,
    user_uid: str,
) -> DecisionMemoryResponse:
    """
    Record actual outcomes for a decision.

    Only the original decision maker can update outcomes.

    Args:
        memory_id: The decision memory document ID
        request: RecordOutcomeRequest with actual outcomes
        user_uid: Firebase UID of the requesting user

    Returns:
        Updated DecisionMemoryResponse

    Raises:
        ValueError: If record not found or user not authorized
    """
    client = get_firestore_client()

    doc_ref = client.collection(COLLECTION_MEMORY).document(memory_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Decision memory record {memory_id} not found")

    data = doc.to_dict() or {}

    if data.get("selected_by_uid") != user_uid:
        raise PermissionError(
            "Only the original decision maker can update outcomes"
        )

    update_data = {
        "status": request.status.value,
        "actual_outcome": request.actual_outcome.model_dump(mode="json"),
        "lessons_learned": request.lessons_learned,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    doc_ref.update(update_data)

    data.update(update_data)
    data["id"] = memory_id

    record = DecisionMemoryRecord(**data)

    logger.info(
        "Outcome recorded for decision %s: status=%s",
        memory_id,
        request.status,
    )

    return DecisionMemoryResponse(record=record)


async def get_memory_record(memory_id: str) -> DecisionMemoryRecord | None:
    """Retrieve a single decision memory record by ID."""
    client = get_firestore_client()
    doc = client.collection(COLLECTION_MEMORY).document(memory_id).get()

    if not doc.exists:
        return None

    data = doc.to_dict()
    if not data:
        return None

    data["id"] = doc.id
    return DecisionMemoryRecord(**data)


async def list_memory_records(
    domain: str | None = None,
    limit: int = 20,
) -> DecisionMemoryListResponse:
    """
    Retrieve recent decision memory records.

    Args:
        domain: Optional filter by domain
        limit: Maximum number of records to return

    Returns:
        DecisionMemoryListResponse ordered by creation time
    """
    client = get_firestore_client()

    query = client.collection(COLLECTION_MEMORY)

    if domain:
        query = query.where(filter=FieldFilter("domain", "==", domain))

    query = query.order_by("created_at", direction="DESCENDING").limit(limit)

    docs = list(query.stream())
    records = []

    for doc in docs:
        data = doc.to_dict()
        if data:
            data["id"] = doc.id
            try:
                records.append(DecisionMemoryRecord(**data))
            except Exception as exc:
                logger.warning(
                    "Failed to parse memory record %s: %s", doc.id, exc
                )

    return DecisionMemoryListResponse(records=records, total=len(records))