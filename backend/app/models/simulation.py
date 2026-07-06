"""
Scenario simulation data models for PRISM.

These models represent the output of the Scenario Simulation Engine —
scored, ranked, and compared outcomes for each intervention strategy.

The simulation engine evaluates every strategy across 5 dimensions
and produces a composite PRISM Score that enables direct comparison.

Scoring dimensions:
  health_impact          — How much does this reduce health burden?
  cost_efficiency        — How much impact per resource spent?
  implementation_speed   — How quickly can this be deployed?
  community_acceptance   — How likely is community/political support?
  sustainability         — How durable is the improvement?
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """Multi-dimensional score for a single intervention strategy."""

    health_impact: float = Field(ge=0.0, le=100.0)
    cost_efficiency: float = Field(ge=0.0, le=100.0)
    implementation_speed: float = Field(ge=0.0, le=100.0)
    community_acceptance: float = Field(ge=0.0, le=100.0)
    sustainability: float = Field(ge=0.0, le=100.0)
    composite_prism_score: float = Field(ge=0.0, le=100.0)


class ProjectedMetrics(BaseModel):
    """Projected community health metrics at a point in time."""

    aqi_reduction_percent: float | None = None
    respiratory_cases_reduction_percent: float | None = None
    pm25_reduction_percent: float | None = None
    construction_dust_reduction_percent: float | None = None
    population_protected: str | None = None
    narrative: str = ""


class TradeOffItem(BaseModel):
    """A single trade-off associated with an intervention."""

    benefit: str
    cost: str
    affected_group: str
    severity: str = Field(
        description="low|medium|high — how significant is this trade-off"
    )


class SimulationResult(BaseModel):
    """
    Complete simulation result for one intervention strategy.

    Contains scores, 30-day projections, trade-offs,
    and the composite PRISM Score used for ranking.
    """

    id: str | None = None
    intervention_id: str
    intervention_title: str
    analysis_id: str
    simulated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    simulation_horizon_days: int = 30

    # Scoring
    scores: ScoreBreakdown

    # Projections at key intervals
    projection_day_7: ProjectedMetrics | None = None
    projection_day_14: ProjectedMetrics | None = None
    projection_day_30: ProjectedMetrics | None = None

    # Trade-offs
    trade_offs: list[TradeOffItem] = Field(default_factory=list)

    # Ranking
    rank_among_strategies: int | None = None
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.7)

    # Gemini reasoning
    gemini_simulation_text: str = ""

    # Recommendation flag
    is_recommended: bool = False
    recommendation_reason: str = ""

    def to_firestore_dict(self) -> dict[str, Any]:
        """Serialize to Firestore-compatible dictionary."""
        return self.model_dump(mode="json", exclude_none=False)


class RunSimulationRequest(BaseModel):
    """Request to run scenario simulation."""

    analysis_id: str = Field(description="The situation analysis ID")
    intervention_ids: list[str] = Field(
        default_factory=list,
        description="Specific intervention IDs to simulate. Empty = simulate all for analysis.",
    )


class SimulationListResponse(BaseModel):
    """API response for simulation results."""

    results: list[SimulationResult]
    analysis_id: str
    total: int
    recommended_intervention_id: str | None = None