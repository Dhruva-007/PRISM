"""
Decision memory router for PRISM.

Exposes endpoints for recording decisions and their outcomes.
This is the learning layer — connecting decisions to real-world results.

Authentication note: In this phase we extract user identity from
the Firebase ID token passed in the Authorization header.
For the hackathon, we verify the token and extract UID and name.
"""

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.models.memory import (
    DecisionMemoryListResponse,
    DecisionMemoryResponse,
    RecordDecisionRequest,
    RecordOutcomeRequest,
)
from app.services.memory.decision_store import (
    get_memory_record,
    list_memory_records,
    record_decision,
    update_outcome,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/memory", tags=["memory"])


def _extract_user_from_request(request: Request) -> tuple[str, str]:
    """
    Extract user UID and display name from request state.

    In production this would use a proper auth dependency.
    For the hackathon, we extract from request headers directly
    since full Firebase token verification middleware is not yet wired.

    Returns:
        Tuple of (uid, display_name)
    """
    uid = request.headers.get("X-User-UID", "anonymous")
    name = request.headers.get("X-User-Name", "Decision Maker")
    return uid, name


@router.post(
    "/record",
    response_model=DecisionMemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a decision",
    description=(
        "Records a decision maker's selection of an intervention strategy. "
        "Creates a permanent memory record linking the analysis, "
        "the chosen strategy, and the decision rationale."
    ),
)
async def record_memory(
    request_body: RecordDecisionRequest,
    http_request: Request,
) -> DecisionMemoryResponse:
    """Record a decision in PRISM memory."""
    uid, name = _extract_user_from_request(http_request)

    logger.info(
        "Recording decision: analysis=%s strategy=%s user=%s",
        request_body.analysis_id,
        request_body.selected_strategy_id,
        name,
    )

    try:
        return await record_decision(request_body, uid, name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Failed to record decision: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record decision: {str(exc)}",
        )


@router.patch(
    "/{memory_id}/outcome",
    response_model=DecisionMemoryResponse,
    summary="Record actual outcome",
    description=(
        "Records the actual observed outcomes of an implemented intervention. "
        "This is how PRISM learns from real-world results."
    ),
)
async def record_outcome(
    memory_id: str,
    request_body: RecordOutcomeRequest,
    http_request: Request,
) -> DecisionMemoryResponse:
    """Record actual outcomes for a decision."""
    uid, _ = _extract_user_from_request(http_request)

    try:
        return await update_outcome(memory_id, request_body, uid)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Failed to record outcome: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record outcome: {str(exc)}",
        )


@router.get(
    "",
    response_model=DecisionMemoryListResponse,
    summary="List decision memory records",
    description="Retrieve recent decision memory records ordered by creation time.",
)
async def list_memory(
    domain: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> DecisionMemoryListResponse:
    """Retrieve decision memory records."""
    try:
        return await list_memory_records(domain=domain, limit=limit)
    except Exception as exc:
        logger.error("Failed to list memory records: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve memory records: {str(exc)}",
        )


@router.get(
    "/{memory_id}",
    response_model=DecisionMemoryResponse,
    summary="Get memory record by ID",
)
async def get_memory(memory_id: str) -> DecisionMemoryResponse:
    """Retrieve a single decision memory record."""
    try:
        record = await get_memory_record(memory_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory record {memory_id} not found",
            )
        return DecisionMemoryResponse(record=record)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to retrieve memory record %s: %s", memory_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve record: {str(exc)}",
        )