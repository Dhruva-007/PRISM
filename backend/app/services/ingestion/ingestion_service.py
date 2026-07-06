"""
Ingestion service for PRISM.

Orchestrates all data source adapters, running them concurrently
for efficiency, then normalizes and stores results in Firestore.

This service is the entry point for all data ingestion operations.
The decision intelligence engine consumes data stored by this service.
"""

import asyncio
from datetime import datetime, timezone

from google.cloud.firestore import Client

from app.integrations.firestore import get_firestore_client
from app.models.community import (
    CommunityEvent,
    DataSource,
    IngestTriggerRequest,
    IngestTriggerResponse,
)
from app.services.ingestion.construction_adapter import ConstructionAdapter
from app.services.ingestion.health_adapter import HealthAdapter
from app.services.ingestion.openaq_adapter import OpenAQAdapter
from app.services.ingestion.openmeteo_adapter import OpenMeteoAdapter
from app.utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_EVENTS = "community_events"

ADAPTER_MAP = {
    DataSource.OPENAQ: OpenAQAdapter,
    DataSource.OPEN_METEO: OpenMeteoAdapter,
    DataSource.HEALTH: HealthAdapter,
    DataSource.CONSTRUCTION: ConstructionAdapter,
}


async def _run_adapter(
    source: DataSource,
    latitude: float,
    longitude: float,
    city: str,
    city_id: str = "hyderabad",
) -> tuple[DataSource, list[CommunityEvent], Exception | None]:
    """
    Run a single adapter and return results with source identifier.

    Always returns a tuple — never raises. Errors are captured and returned
    so the orchestrator can continue with other adapters.
    """
    adapter_class = ADAPTER_MAP.get(source)
    if adapter_class is None:
        return source, [], ValueError(f"No adapter for source: {source}")

    try:
        adapter = adapter_class()
        events = await adapter.fetch(latitude=latitude, longitude=longitude, city=city, city_id=city_id)
        return source, events, None
    except Exception as exc:
        logger.error("Adapter %s failed: %s", source, exc)
        return source, [], exc


def _store_events_in_firestore(
    client: Client,
    events: list[CommunityEvent],
) -> int:
    """
    Store normalized events in Firestore using batch writes.

    Returns the number of events successfully stored.
    Firestore batch limit is 500 operations per batch.
    """
    if not events:
        return 0

    stored_count = 0
    batch_size = 400

    for i in range(0, len(events), batch_size):
        batch = client.batch()
        batch_events = events[i : i + batch_size]

        for event in batch_events:
            doc_ref = client.collection(COLLECTION_EVENTS).document()
            event_data = event.to_firestore_dict()
            event_data["id"] = doc_ref.id
            batch.set(doc_ref, event_data)
            stored_count += 1

        batch.commit()
        logger.debug("Committed batch of %d events to Firestore", len(batch_events))

    return stored_count


async def run_ingestion(request: IngestTriggerRequest) -> IngestTriggerResponse:
    """
    Run the full ingestion pipeline for the specified sources.

    Concurrently fetches from all requested data sources,
    then stores all normalized events in Firestore.

    Args:
        request: IngestTriggerRequest with sources and location

    Returns:
        IngestTriggerResponse with ingestion results summary
    """
    logger.info(
        "Starting ingestion | sources=%s | location=(%s, %s)",
        [s.value for s in request.sources],
        request.latitude,
        request.longitude,
    )

    tasks = [
        _run_adapter(
            source=source,
            latitude=request.latitude,
            longitude=request.longitude,
            city=request.city,
            city_id=request.city_id,
        )
        for source in request.sources
    ]

    results = await asyncio.gather(*tasks)

    all_events: list[CommunityEvent] = []
    sources_succeeded: list[str] = []
    sources_failed: list[str] = []

    for source, events, error in results:
        if error is not None:
            sources_failed.append(source.value)
            logger.warning("Source %s failed: %s", source.value, error)
        else:
            sources_succeeded.append(source.value)
            all_events.extend(events)
            logger.info(
                "Source %s succeeded: %d events", source.value, len(events)
            )

    firestore_client = get_firestore_client()
    stored_count = _store_events_in_firestore(firestore_client, all_events)

    logger.info(
        "Ingestion complete | stored=%d | succeeded=%s | failed=%s",
        stored_count,
        sources_succeeded,
        sources_failed,
    )

    return IngestTriggerResponse(
        status="complete",
        events_ingested=stored_count,
        sources_attempted=[s.value for s in request.sources],
        sources_succeeded=sources_succeeded,
        sources_failed=sources_failed,
        message=f"Ingested {stored_count} events from {len(sources_succeeded)} sources.",
    )


async def get_recent_events(
    firestore_client: Client,
    limit: int = 50,
    source: str | None = None,
    event_type: str | None = None,
) -> list[dict]:
    """
    Retrieve recent community events from Firestore.

    Args:
        firestore_client: Firestore client
        limit: Maximum number of events to return
        source: Optional filter by data source
        event_type: Optional filter by event type

    Returns:
        List of event dictionaries ordered by ingested_at descending
    """
    query = firestore_client.collection(COLLECTION_EVENTS)

    from google.cloud.firestore_v1.base_query import FieldFilter
    if source:
        query = query.where(filter=FieldFilter("source", "==", source))

    if event_type:
        query = query.where(filter=FieldFilter("event_type", "==", event_type))

    query = query.order_by("ingested_at", direction="DESCENDING").limit(limit)

    docs = query.stream()
    events = []

    for doc in docs:
        data = doc.to_dict()
        if data:
            data["id"] = doc.id
            events.append(data)

    return events