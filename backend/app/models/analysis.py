"""
Situation analysis data models for PRISM.

These models represent the output of the Decision Intelligence Engine —
the structured reasoning produced by Gemini 2.5 Flash about community
health and environmental conditions.

Every analysis is stored in Firestore and becomes the basis for
intervention generation and scenario simulation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnalysisStatus(str, Enum):
    """Lifecycle status of a situation analysis."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    FAILED = "failed"


class UrgencyLevel(str, Enum):
    """Urgency classification for community response."""

    ROUTINE = "routine"
    ELEVATED = "elevated"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class SeverityLevel(str, Enum):
    """Overall severity of the detected situation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RootCause(BaseModel):
    """A single identified root cause with supporting evidence."""

    cause: str = Field(description="Clear description of the root cause")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score 0.0 to 1.0",
    )
    category: str = Field(
        description="Category: environmental | behavioral | infrastructure | meteorological"
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Specific data points supporting this cause",
    )
    affected_population: str | None = Field(
        default=None,
        description="Who is most affected by this root cause",
    )


class DetectedPattern(BaseModel):
    """A pattern identified in the community data."""

    pattern: str = Field(description="Description of the pattern")
    strength: float = Field(
        ge=0.0,
        le=1.0,
        description="Pattern strength 0.0 (weak) to 1.0 (strong)",
    )
    pattern_type: str = Field(
        description="Type: temporal | spatial | correlation | anomaly"
    )
    data_sources: list[str] = Field(
        default_factory=list,
        description="Which data sources reveal this pattern",
    )


class DataSummary(BaseModel):
    """Summary of the data context used in the analysis."""

    total_events: int
    air_quality_events: int
    weather_events: int
    health_events: int
    construction_events: int
    time_window_hours: int
    location: str
    avg_aqi: float | None = None
    max_respiratory_cases: int | None = None
    dominant_severity: str | None = None


class SituationAnalysis(BaseModel):
    """
    Complete situation analysis produced by the Decision Intelligence Engine.

    This is the primary output of PRISM's AI reasoning — a structured,
    evidence-based assessment of community health and environmental conditions,
    including root causes, detected patterns, severity, and urgency.
    """

    id: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: AnalysisStatus = AnalysisStatus.PENDING
    domain: str = "health_environment"

    # Scope
    time_window_hours: int = 24
    location: str = ""
    latitude: float = 0.0
    longitude: float = 0.0

    # Data context
    data_summary: DataSummary | None = None
    trigger_event_ids: list[str] = Field(default_factory=list)

    # AI reasoning output
    severity_level: SeverityLevel = SeverityLevel.LOW
    urgency: UrgencyLevel = UrgencyLevel.ROUTINE
    headline: str = ""
    summary: str = ""
    root_causes: list[RootCause] = Field(default_factory=list)
    patterns_detected: list[DetectedPattern] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    population_at_risk: str = ""
    recommended_action_timeframe: str = ""
    gemini_reasoning: str = ""
    confidence_overall: float = 0.0

    # Error tracking
    error_message: str | None = None

    def to_firestore_dict(self) -> dict[str, Any]:
        """Serialize to Firestore-compatible dictionary."""
        return self.model_dump(mode="json", exclude_none=False)


class AnalysisRequest(BaseModel):
    """Request to run a new situation analysis."""

    city_id: str = Field(
        default="hyderabad",
        description="City identifier. Supported: hyderabad, delhi, bangalore, mumbai",
    )
    location: str = Field(default="")
    latitude: float = Field(default=0.0, ge=-90, le=90)
    longitude: float = Field(default=0.0, ge=-180, le=180)
    time_window_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="How many hours of historical data to analyze",
    )

    def model_post_init(self, __context: Any) -> None:
        """Resolve city config if city_id provided and lat/lon are defaults."""
        from app.config_cities import get_city_config
        config = get_city_config(self.city_id)
        if self.latitude == 0.0 and self.longitude == 0.0:
            self.latitude = config.latitude
            self.longitude = config.longitude
        if not self.location:
            self.location = f"{config.display_name}, {config.state}"


class AnalysisListResponse(BaseModel):
    """API response for a list of analyses."""

    analyses: list[SituationAnalysis]
    total: int


class AnalysisResponse(BaseModel):
    """API response for a single analysis."""

    analysis: SituationAnalysis