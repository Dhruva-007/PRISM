"""
Shared pytest fixtures for PRISM backend tests.

Provides:
- Mock Firestore client
- Mock Gemini model
- Sample community events
- Sample analysis objects
- Sample intervention strategies
- FastAPI test client
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.models.community import (
    AirQualityMetrics,
    CommunityEvent,
    DataSource,
    EventType,
    GeoLocation,
    HealthMetrics,
    SeverityLevel,
    WeatherMetrics,
    ConstructionMetrics,
)
from app.models.analysis import (
    AnalysisStatus,
    DataSummary,
    DetectedPattern,
    RootCause,
    SeverityLevel as AnalysisSeverity,
    SituationAnalysis,
    UrgencyLevel,
)
from app.models.intervention import (
    CostLevel,
    ExpectedOutcome,
    InterventionAction,
    InterventionStrategy,
    StrategyType,
)
from app.models.simulation import ScoreBreakdown, SimulationResult


# ── Sample Data Fixtures ────────────────────────────────────────────


@pytest.fixture
def sample_air_quality_event() -> CommunityEvent:
    """A realistic air quality event for Hyderabad."""
    return CommunityEvent(
        id="test-aq-001",
        source=DataSource.OPENAQ,
        event_type=EventType.AIR_QUALITY,
        location=GeoLocation(
            latitude=17.385,
            longitude=78.4867,
            district="Secunderabad",
            city="Hyderabad, Telangana",
        ),
        timestamp=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        severity=SeverityLevel.HIGH,
        metrics=AirQualityMetrics(
            aqi=142.0,
            pm25=38.5,
            pm10=72.3,
            no2=45.2,
            o3=88.1,
            dominant_pollutant="PM2.5",
        ),
        raw_source_id="openaq-station-12345",
        metadata={"station_name": "Secunderabad Station"},
    )


@pytest.fixture
def sample_weather_event() -> CommunityEvent:
    """A realistic weather event for Hyderabad."""
    return CommunityEvent(
        id="test-weather-001",
        source=DataSource.OPEN_METEO,
        event_type=EventType.WEATHER,
        location=GeoLocation(
            latitude=17.385,
            longitude=78.4867,
            district="Meteorological Station",
            city="Hyderabad, Telangana",
        ),
        timestamp=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        severity=SeverityLevel.MEDIUM,
        metrics=WeatherMetrics(
            temperature_celsius=34.5,
            humidity_percent=44.0,
            wind_speed_ms=1.2,
            wind_direction_degrees=270.0,
            precipitation_mm=0.0,
            pressure_hpa=1008.0,
            visibility_km=8.0,
            weather_condition="Clear sky",
        ),
        raw_source_id="open_meteo_17.385_78.4867",
        metadata={"weather_code": 0},
    )


@pytest.fixture
def sample_health_event() -> CommunityEvent:
    """A realistic health report event."""
    return CommunityEvent(
        id="test-health-001",
        source=DataSource.HEALTH,
        event_type=EventType.HEALTH_REPORT,
        location=GeoLocation(
            latitude=17.365,
            longitude=78.4967,
            district="Old City - Charminar",
            city="Hyderabad, Telangana",
        ),
        timestamp=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        severity=SeverityLevel.CRITICAL,
        metrics=HealthMetrics(
            respiratory_cases=183,
            er_visits=27,
            clinic_visits=100,
            hospitalization_rate=0.115,
            affected_age_group="65+ years",
            condition="Asthma exacerbation",
        ),
        raw_source_id="health_old_city_20260705",
        metadata={"report_type": "daily_aggregate"},
    )


@pytest.fixture
def sample_construction_event() -> CommunityEvent:
    """A realistic construction event."""
    return CommunityEvent(
        id="test-construction-001",
        source=DataSource.CONSTRUCTION,
        event_type=EventType.CONSTRUCTION,
        location=GeoLocation(
            latitude=17.403,
            longitude=78.4647,
            district="Kukatpally",
            city="Hyderabad, Telangana",
        ),
        timestamp=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        severity=SeverityLevel.HIGH,
        metrics=ConstructionMetrics(
            activity_type="Tunnel boring and elevated corridor construction",
            dust_risk=SeverityLevel.HIGH,
            proximity_to_schools_m=280.0,
            proximity_to_hospitals_m=950.0,
            estimated_duration_days=540,
            affected_radius_m=800.0,
        ),
        raw_source_id="construction_metro_phase2",
        metadata={"site_name": "Hyderabad Metro Rail Phase 2"},
    )


@pytest.fixture
def sample_events(
    sample_air_quality_event,
    sample_weather_event,
    sample_health_event,
    sample_construction_event,
) -> list[CommunityEvent]:
    """A complete set of community events for testing."""
    return [
        sample_air_quality_event,
        sample_weather_event,
        sample_health_event,
        sample_construction_event,
    ]


@pytest.fixture
def sample_analysis() -> SituationAnalysis:
    """A complete situation analysis for testing."""
    return SituationAnalysis(
        id="test-analysis-001",
        status=AnalysisStatus.COMPLETE,
        location="Hyderabad, Telangana",
        latitude=17.385,
        longitude=78.4867,
        time_window_hours=24,
        severity_level=AnalysisSeverity.HIGH,
        urgency=UrgencyLevel.URGENT,
        headline="Elevated respiratory risk from construction dust and heat stress",
        summary=(
            "Hyderabad is experiencing elevated respiratory health burden "
            "driven by active construction near Kukatpally Metro site and "
            "high temperatures reducing pollutant dispersal."
        ),
        root_causes=[
            RootCause(
                cause="Active Metro Phase 2 construction generating PM10 dust",
                confidence=0.87,
                category="infrastructure",
                supporting_evidence=["PM2.5 at 38.5 µg/m³", "Construction site 280m from school"],
                affected_population="Children and elderly in Kukatpally",
            )
        ],
        patterns_detected=[
            DetectedPattern(
                pattern="Low wind speed reducing pollutant dispersal",
                strength=0.82,
                pattern_type="meteorological",
                data_sources=["open_meteo"],
            )
        ],
        key_findings=[
            "PM2.5 exceeds WHO guideline by 2.5x",
            "Wind speed below dispersal threshold at 1.2 m/s",
            "183 respiratory cases in Old City alone",
        ],
        population_at_risk="Children under 14 and adults over 65 near construction zones",
        recommended_action_timeframe="Immediate action required within 24-48 hours",
        gemini_reasoning="Analysis based on converging air quality, weather, and health data.",
        confidence_overall=0.78,
        data_summary=DataSummary(
            total_events=12,
            air_quality_events=3,
            weather_events=1,
            health_events=7,
            construction_events=4,
            time_window_hours=24,
            location="Hyderabad, Telangana",
            avg_aqi=142.0,
            max_respiratory_cases=183,
            dominant_severity="high",
        ),
    )


@pytest.fixture
def sample_intervention(sample_analysis) -> InterventionStrategy:
    """A complete intervention strategy for testing."""
    return InterventionStrategy(
        id="test-strategy-001",
        analysis_id=sample_analysis.id,
        title="Emergency Construction Dust Suppression",
        description="Immediate dust suppression at Metro construction sites near schools.",
        strategy_type=StrategyType.IMMEDIATE,
        target_root_causes=["Metro Phase 2 construction dust"],
        actions=[
            InterventionAction(
                action_id="A1",
                title="Deploy water suppression at Metro sites",
                description="Install water sprinkler systems at all active Metro construction sites.",
                responsible_party="HMDA Construction Oversight Division",
                timeline_days=1,
                estimated_cost=CostLevel.LOW,
                dependencies=[],
                success_metric="PM10 reduction of 30% within 48 hours",
            ),
            InterventionAction(
                action_id="A2",
                title="Temporary school closure advisory",
                description="Issue advisory for schools within 500m of active sites.",
                responsible_party="Telangana Education Department",
                timeline_days=2,
                estimated_cost=CostLevel.LOW,
                dependencies=["A1"],
                success_metric="100% of at-risk schools notified",
            ),
        ],
        total_estimated_cost=CostLevel.LOW,
        implementation_complexity="Low",
        required_authorities=["HMDA", "GHMC", "Telangana Education Department"],
        prerequisites=[],
        expected_outcomes=[
            ExpectedOutcome(
                metric="PM2.5 concentration",
                baseline_value="38.5 µg/m³",
                expected_value="< 25 µg/m³",
                timeframe="Within 48 hours",
                confidence=0.75,
            )
        ],
        primary_beneficiaries="Children in Kukatpally schools",
        estimated_population_impacted="12,000 residents near Metro construction",
        risks=["Construction delays", "Contractor resistance"],
        trade_offs=["Short-term relief without long-term structural change"],
        gemini_rationale="Fastest deployable intervention with direct impact on source.",
    )


@pytest.fixture
def sample_simulation_result(sample_intervention) -> SimulationResult:
    """A complete simulation result for testing."""
    return SimulationResult(
        id="test-sim-001",
        intervention_id=sample_intervention.id,
        intervention_title=sample_intervention.title,
        analysis_id="test-analysis-001",
        simulation_horizon_days=30,
        scores=ScoreBreakdown(
            health_impact=88.0,
            cost_efficiency=91.0,
            implementation_speed=95.0,
            community_acceptance=72.0,
            sustainability=45.0,
            composite_prism_score=79.2,
        ),
        confidence_level=0.78,
        gemini_simulation_text="High speed and low cost make this the top-ranked strategy.",
        is_recommended=True,
        recommendation_reason="Highest PRISM Score with best health impact.",
        rank_among_strategies=1,
    )


# ── Mock Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def mock_firestore_client():
    """Mock Firestore client for tests that should not hit real Firestore."""
    with patch("app.integrations.firestore.get_firestore_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_gemini_model():
    """Mock Gemini model for tests that should not hit Vertex AI."""
    with patch("app.integrations.vertex_ai.get_gemini_model") as mock:
        model = MagicMock()
        mock.return_value = model
        yield model


@pytest.fixture
def test_client():
    """FastAPI test client that does not hit external services."""
    with patch("app.integrations.firestore.get_firestore_client") as mock_fs:
        with patch("app.integrations.vertex_ai.get_gemini_model") as mock_ai:
            mock_fs.return_value = MagicMock()
            mock_ai.return_value = MagicMock()
            from app.main import app
            with TestClient(app, raise_server_exceptions=False) as client:
                yield client