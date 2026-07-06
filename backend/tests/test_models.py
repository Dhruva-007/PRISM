"""
Tests for PRISM Pydantic data models.

Verifies:
- Valid model construction
- Field validation
- Metric type enforcement
- Serialization to Firestore dict
- City configuration
"""

import pytest
from datetime import datetime, timezone

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
    IngestTriggerRequest,
)
from app.models.analysis import (
    AnalysisRequest,
    AnalysisStatus,
    RootCause,
    DetectedPattern,
    SituationAnalysis,
    UrgencyLevel,
    SeverityLevel as AnalysisSeverity,
)
from app.models.intervention import (
    CostLevel,
    InterventionStrategy,
    StrategyType,
)
from app.models.simulation import ScoreBreakdown, SimulationResult
from app.config_cities import get_city_config, SUPPORTED_CITY_IDS


class TestGeoLocation:
    def test_valid_location(self):
        loc = GeoLocation(
            latitude=17.385,
            longitude=78.4867,
            district="Secunderabad",
            city="Hyderabad",
        )
        assert loc.latitude == 17.385
        assert loc.longitude == 78.4867

    def test_coordinates_rounded_to_6_decimals(self):
        loc = GeoLocation(
            latitude=17.38500012345678,
            longitude=78.48670098765432,
            district="Test",
            city="Test",
        )
        assert len(str(loc.latitude).split(".")[-1]) <= 6
        assert len(str(loc.longitude).split(".")[-1]) <= 6

    def test_invalid_latitude_raises(self):
        with pytest.raises(Exception):
            GeoLocation(latitude=91.0, longitude=0.0, district="X", city="X")

    def test_invalid_longitude_raises(self):
        with pytest.raises(Exception):
            GeoLocation(latitude=0.0, longitude=181.0, district="X", city="X")


class TestCommunityEvent:
    def test_valid_air_quality_event(self, sample_air_quality_event):
        event = sample_air_quality_event
        assert event.source == DataSource.OPENAQ
        assert event.event_type == EventType.AIR_QUALITY
        assert isinstance(event.metrics, AirQualityMetrics)

    def test_valid_weather_event(self, sample_weather_event):
        assert sample_weather_event.event_type == EventType.WEATHER
        assert isinstance(sample_weather_event.metrics, WeatherMetrics)

    def test_valid_health_event(self, sample_health_event):
        assert sample_health_event.event_type == EventType.HEALTH_REPORT
        assert isinstance(sample_health_event.metrics, HealthMetrics)

    def test_mismatched_metrics_raises_validation_error(self):
        """Air quality event cannot have WeatherMetrics."""
        with pytest.raises(Exception):
            CommunityEvent(
                source=DataSource.OPENAQ,
                event_type=EventType.AIR_QUALITY,
                location=GeoLocation(
                    latitude=17.385,
                    longitude=78.4867,
                    district="Test",
                    city="Test",
                ),
                timestamp=datetime.now(timezone.utc),
                severity=SeverityLevel.LOW,
                metrics=WeatherMetrics(temperature_celsius=30.0),
            )

    def test_to_firestore_dict_is_json_serializable(self, sample_air_quality_event):
        data = sample_air_quality_event.to_firestore_dict()
        assert isinstance(data, dict)
        assert data["source"] == "openaq"
        assert data["event_type"] == "air_quality"
        assert "metrics" in data
        assert "location" in data

    def test_severity_levels_are_valid(self):
        for level in ["low", "medium", "high", "critical"]:
            assert SeverityLevel(level) is not None


class TestIngestTriggerRequest:
    def test_default_resolves_hyderabad(self):
        req = IngestTriggerRequest()
        assert req.city_id == "hyderabad"
        assert abs(req.latitude - 17.385) < 0.01
        assert abs(req.longitude - 78.4867) < 0.01
        assert "Hyderabad" in req.city

    def test_delhi_resolves_correctly(self):
        req = IngestTriggerRequest(city_id="delhi")
        assert abs(req.latitude - 28.6139) < 0.01
        assert abs(req.longitude - 77.209) < 0.01
        assert "Delhi" in req.city

    def test_bangalore_resolves_correctly(self):
        req = IngestTriggerRequest(city_id="bangalore")
        assert abs(req.latitude - 12.9716) < 0.01
        assert "Bangalore" in req.city

    def test_mumbai_resolves_correctly(self):
        req = IngestTriggerRequest(city_id="mumbai")
        assert abs(req.latitude - 19.076) < 0.01
        assert "Mumbai" in req.city

    def test_explicit_coordinates_not_overridden(self):
        req = IngestTriggerRequest(
            city_id="hyderabad",
            latitude=17.0,
            longitude=78.0,
        )
        assert req.latitude == 17.0
        assert req.longitude == 78.0


class TestAnalysisRequest:
    def test_default_resolves_hyderabad(self):
        req = AnalysisRequest()
        assert "Hyderabad" in req.location
        assert abs(req.latitude - 17.385) < 0.01

    def test_city_id_delhi_resolves(self):
        req = AnalysisRequest(city_id="delhi")
        assert "Delhi" in req.location


class TestSituationAnalysis:
    def test_valid_analysis_construction(self, sample_analysis):
        assert sample_analysis.status == AnalysisStatus.COMPLETE
        assert sample_analysis.confidence_overall == 0.78
        assert len(sample_analysis.root_causes) == 1
        assert len(sample_analysis.patterns_detected) == 1

    def test_to_firestore_dict(self, sample_analysis):
        data = sample_analysis.to_firestore_dict()
        assert isinstance(data, dict)
        assert data["status"] == "complete"
        assert data["severity_level"] == "high"

    def test_root_cause_confidence_bounds(self):
        with pytest.raises(Exception):
            RootCause(
                cause="Test",
                confidence=1.5,
                category="environmental",
                supporting_evidence=[],
            )

    def test_pattern_strength_bounds(self):
        with pytest.raises(Exception):
            DetectedPattern(
                pattern="Test",
                strength=1.5,
                pattern_type="anomaly",
                data_sources=[],
            )


class TestInterventionStrategy:
    def test_valid_strategy(self, sample_intervention):
        assert sample_intervention.strategy_type == StrategyType.IMMEDIATE
        assert sample_intervention.total_estimated_cost == CostLevel.LOW
        assert len(sample_intervention.actions) == 2

    def test_to_firestore_dict(self, sample_intervention):
        data = sample_intervention.to_firestore_dict()
        assert data["strategy_type"] == "immediate"
        assert data["total_estimated_cost"] == "low"


class TestScoreBreakdown:
    def test_valid_scores(self):
        scores = ScoreBreakdown(
            health_impact=88.0,
            cost_efficiency=91.0,
            implementation_speed=95.0,
            community_acceptance=72.0,
            sustainability=45.0,
            composite_prism_score=79.2,
        )
        assert scores.composite_prism_score == 79.2

    def test_score_out_of_range_raises(self):
        with pytest.raises(Exception):
            ScoreBreakdown(
                health_impact=101.0,
                cost_efficiency=50.0,
                implementation_speed=50.0,
                community_acceptance=50.0,
                sustainability=50.0,
                composite_prism_score=50.0,
            )


class TestCityConfig:
    def test_all_four_cities_exist(self):
        for city_id in ["hyderabad", "delhi", "bangalore", "mumbai"]:
            assert city_id in SUPPORTED_CITY_IDS

    def test_hyderabad_config(self):
        config = get_city_config("hyderabad")
        assert config.display_name == "Hyderabad"
        assert config.state == "Telangana"
        assert len(config.districts) >= 5
        assert len(config.construction_sites) >= 3
        assert len(config.health_conditions) >= 5

    def test_delhi_config(self):
        config = get_city_config("delhi")
        assert config.display_name == "Delhi"
        assert config.latitude == 28.6139

    def test_unknown_city_returns_default(self):
        config = get_city_config("unknown_city_xyz")
        assert config.city_id == "hyderabad"

    def test_all_cities_have_districts_and_sites(self):
        for city_id in SUPPORTED_CITY_IDS:
            config = get_city_config(city_id)
            assert len(config.districts) > 0
            assert len(config.construction_sites) > 0
            assert len(config.health_conditions) > 0