"""
Decision memory data models for PRISM.

Decision memory is the learning layer of PRISM. Every time a decision
maker selects an intervention strategy, that decision is recorded here.
When actual outcomes are later observed, they are recorded against the
original decision — creating a feedback loop for continuous improvement.

This collection answers: "What did we decide, and did it work?"
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DecisionStatus(str, Enum):
    """Lifecycle status of a recorded decision."""

    SELECTED = "selected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ActualOutcome(BaseModel):
    """
    Actual observed outcomes recorded after an intervention was implemented.

    These are filled in by decision makers after the intervention
    has been running long enough to observe results.
    """

    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    aqi_change_percent: float | None = Field(
        default=None,
        description="Actual % change in AQI (negative = improvement)",
    )
    respiratory_cases_change_percent: float | None = Field(
        default=None,
        description="Actual % change in respiratory cases",
    )
    implementation_success: bool | None = None
    obstacles_encountered: list[str] = Field(default_factory=list)
    actual_cost_level: str | None = None
    community_response: str | None = None
    notes: str = ""


class DecisionMemoryRecord(BaseModel):
    """
    A complete record of a decision made using PRISM.

    Captures the full decision context — what situation was detected,
    what options were available, what was chosen, why, and what happened.
    This is the primary artifact for organizational learning.
    """

    id: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Decision context
    analysis_id: str
    analysis_headline: str
    analysis_severity: str
    analysis_urgency: str
    location: str

    # What was chosen
    selected_strategy_id: str
    selected_strategy_title: str
    selected_strategy_type: str
    prism_score_at_selection: float | None = None
    rank_at_selection: int | None = None

    # Who decided and why
    selected_by_uid: str
    selected_by_name: str
    selection_reason: str

    # Status tracking
    status: DecisionStatus = DecisionStatus.SELECTED

    # Actual outcomes (filled in later)
    actual_outcome: ActualOutcome | None = None
    lessons_learned: str = ""

    # Domain for future filtering
    domain: str = "health_environment"

    def to_firestore_dict(self) -> dict[str, Any]:
        """Serialize to Firestore-compatible dictionary."""
        return self.model_dump(mode="json", exclude_none=False)


class RecordDecisionRequest(BaseModel):
    """Request to record a decision in memory."""

    analysis_id: str
    selected_strategy_id: str
    selection_reason: str = Field(
        min_length=10,
        description="Why this strategy was selected (min 10 characters)",
    )


class RecordOutcomeRequest(BaseModel):
    """Request to record actual outcomes for a decision."""

    status: DecisionStatus
    actual_outcome: ActualOutcome
    lessons_learned: str = ""


class DecisionMemoryListResponse(BaseModel):
    """API response for a list of decision memory records."""

    records: list[DecisionMemoryRecord]
    total: int


class DecisionMemoryResponse(BaseModel):
    """API response for a single decision memory record."""

    record: DecisionMemoryRecord