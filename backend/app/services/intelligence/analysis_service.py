"""
Analysis service for PRISM Decision Intelligence Engine.

Orchestrates the complete analysis pipeline:
1. Assemble context from Firestore events
2. Detect patterns
3. Run Gemini reasoning
4. Store result in Firestore
5. Return complete SituationAnalysis

This service is the entry point for all analysis operations.
"""

from datetime import datetime, timezone

from app.integrations.firestore import get_firestore_client
from app.models.analysis import (
    AnalysisListResponse,
    AnalysisRequest,
    AnalysisStatus,
    SituationAnalysis,
)
from app.services.intelligence.context_assembler import assemble_context
from app.services.intelligence.pattern_detector import detect_patterns
from app.services.intelligence.reasoning_engine import run_analysis
from app.utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_ANALYSES = "situation_analyses"


async def create_analysis(request: AnalysisRequest) -> SituationAnalysis:
    """
    Run the complete Decision Intelligence pipeline.

    Creates a pending analysis record, runs the full pipeline,
    updates the record with results, and returns the complete analysis.

    Args:
        request: AnalysisRequest with location and time window

    Returns:
        Complete SituationAnalysis with Gemini reasoning
    """
    client = get_firestore_client()

    # Create initial pending record
    doc_ref = client.collection(COLLECTION_ANALYSES).document()
    analysis_id = doc_ref.id

    pending_analysis = SituationAnalysis(
        id=analysis_id,
        status=AnalysisStatus.ANALYZING,
        location=request.location,
        latitude=request.latitude,
        longitude=request.longitude,
        time_window_hours=request.time_window_hours,
    )

    doc_ref.set(pending_analysis.to_firestore_dict())
    logger.info("Created pending analysis: %s", analysis_id)

    try:
        # Step 1: Assemble context
        logger.info("Step 1: Assembling context...")
        context = await assemble_context(
            latitude=request.latitude,
            longitude=request.longitude,
            location=request.location,
            time_window_hours=request.time_window_hours,
        )

        # Step 2: Detect patterns
        logger.info("Step 2: Detecting patterns...")
        patterns = detect_patterns(context)

        # Step 3: Gemini reasoning
        logger.info("Step 3: Running Gemini reasoning...")
        analysis = await run_analysis(context, patterns)

        # Attach metadata
        analysis.id = analysis_id
        analysis.status = AnalysisStatus.COMPLETE
        analysis.location = request.location
        analysis.latitude = request.latitude
        analysis.longitude = request.longitude
        analysis.time_window_hours = request.time_window_hours
        analysis.trigger_event_ids = context.get("event_ids", [])[:20]
        analysis.created_at = datetime.now(timezone.utc)

        # Store complete analysis
        doc_ref.set(analysis.to_firestore_dict())
        logger.info(
            "Analysis %s complete: severity=%s urgency=%s",
            analysis_id,
            analysis.severity_level,
            analysis.urgency,
        )

        return analysis

    except Exception as exc:
        logger.error("Analysis pipeline failed: %s", exc, exc_info=True)

        failed_analysis = SituationAnalysis(
            id=analysis_id,
            status=AnalysisStatus.FAILED,
            location=request.location,
            latitude=request.latitude,
            longitude=request.longitude,
            time_window_hours=request.time_window_hours,
            error_message=str(exc),
            headline="Analysis failed",
            summary=f"The analysis pipeline encountered an error: {str(exc)}",
        )

        doc_ref.set(failed_analysis.to_firestore_dict())
        return failed_analysis


async def get_analysis(analysis_id: str) -> SituationAnalysis | None:
    """
    Retrieve a single analysis by ID from Firestore.

    Args:
        analysis_id: Firestore document ID

    Returns:
        SituationAnalysis if found, None otherwise
    """
    client = get_firestore_client()
    doc = client.collection(COLLECTION_ANALYSES).document(analysis_id).get()

    if not doc.exists:
        return None

    data = doc.to_dict()
    if not data:
        return None

    data["id"] = doc.id
    return SituationAnalysis(**data)


async def list_analyses(limit: int = 20) -> AnalysisListResponse:
    """
    Retrieve recent analyses from Firestore.

    Args:
        limit: Maximum number of analyses to return

    Returns:
        AnalysisListResponse with list of analyses
    """
    client = get_firestore_client()

    query = (
        client.collection(COLLECTION_ANALYSES)
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
    )

    docs = list(query.stream())
    analyses = []

    for doc in docs:
        data = doc.to_dict()
        if data:
            data["id"] = doc.id
            try:
                analyses.append(SituationAnalysis(**data))
            except Exception as exc:
                logger.warning(
                    "Failed to parse analysis %s: %s", doc.id, exc
                )

    return AnalysisListResponse(analyses=analyses, total=len(analyses))