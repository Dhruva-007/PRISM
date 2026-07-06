"""
Data ingestion router for PRISM.

Exposes endpoints for:
- Triggering data ingestion from external sources
- Querying stored community events

These endpoints are the entry point for all community data
that flows into the PRISM decision intelligence pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.integrations.firestore import get_firestore_client
from app.models.community import (
    CommunityEventListResponse,
    DataSource,
    EventType,
    IngestTriggerRequest,
    IngestTriggerResponse,
)
from app.services.ingestion.ingestion_service import (
    get_recent_events,
    run_ingestion,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingestion"])

ALL_SOURCES = [
    DataSource.OPENAQ,
    DataSource.OPEN_METEO,
    DataSource.HEALTH,
    DataSource.CONSTRUCTION,
]


@router.post(
    "/trigger",
    response_model=IngestTriggerResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger data ingestion",
    description=(
        "Triggers data ingestion from all or specified external sources. "
        "Runs adapters concurrently and stores normalized events in Firestore."
    ),
)
async def trigger_ingestion(
    request: IngestTriggerRequest | None = None,
) -> IngestTriggerResponse:
    """
    Trigger the data ingestion pipeline.

    If no request body is provided, ingests from all sources
    using the default Metro Area location.
    """
    if request is None:
        request = IngestTriggerRequest(sources=ALL_SOURCES)

    if not request.sources:
        request.sources = ALL_SOURCES

    try:
        result = await run_ingestion(request)
        return result
    except Exception as exc:
        logger.error("Ingestion trigger failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(exc)}",
        )


@router.get(
    "/events",
    response_model=CommunityEventListResponse,
    summary="List community events",
    description="Retrieve recent community events from Firestore with optional filtering.",
)
async def list_events(
    source: str | None = Query(default=None, description="Filter by data source"),
    event_type: str | None = Query(default=None, description="Filter by event type"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum events to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> CommunityEventListResponse:
    """
    Retrieve recent community events.

    Events are ordered by ingestion time, most recent first.
    """
    if source and source not in [s.value for s in DataSource]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source. Valid values: {[s.value for s in DataSource]}",
        )

    if event_type and event_type not in [e.value for e in EventType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event_type. Valid values: {[e.value for e in EventType]}",
        )

    try:
        firestore_client = get_firestore_client()
        events_data = await get_recent_events(
            firestore_client=firestore_client,
            limit=limit + offset,
            source=source,
            event_type=event_type,
        )

        paginated = events_data[offset : offset + limit]

        return CommunityEventListResponse(
            events=paginated,
            total=len(events_data),
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        logger.error("Failed to retrieve events: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve events: {str(exc)}",
        )