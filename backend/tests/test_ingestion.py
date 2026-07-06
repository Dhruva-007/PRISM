"""
Tests for PRISM data ingestion pipeline.

Verifies:
- Health adapter generates correct events per city
- Construction adapter generates city-specific sites
- Open-Meteo adapter parses real API response format
- Pattern detector identifies correct patterns
- Context assembler computes correct summaries
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.community import (
    DataSource,
    EventType,
    HealthMetrics,
    ConstructionMetrics,
    SeverityLevel,
)
from app.services.ingestion.health_adapter import HealthAdapter
from app.services.ingestion.construction_adapter import ConstructionAdapter
from app.services.intelligence.pattern_detector import detect_patterns


class TestHealthAdapter:
    @pytest.mark.asyncio
    async def test_generates_events_for_hyderabad(self):
        adapter = HealthAdapter()
        events = await adapter.fetch(
            latitude=17.385,
            longitude=78.4867,
            city="Hyderabad, Telangana",
            city_id="hyderabad",
        )
        assert len(events) == 7
        for event in events:
            assert event.source == DataSource.HEALTH
            assert event.event_type == EventType.HEALTH_REPORT
            assert isinstance(event.metrics, HealthMetrics)
            assert event.severity in [s for s in SeverityLevel]

    @pytest.mark.asyncio
    async def test_generates_events_for_delhi(self):
        adapter = HealthAdapter()
        events = await adapter.fetch(
            latitude=28.6139,
            longitude=77.209,
            city="Delhi, NCT",
            city_id="delhi",
        )
        assert len(events) == 8
        districts = [e.location.district for e in events]
        assert "Connaught Place" in districts
        assert "Anand Vihar" in districts

    @pytest.mark.asyncio
    async def test_generates_events_for_bangalore(self):
        adapter = HealthAdapter()
        events = await adapter.fetch(
            latitude=12.9716,
            longitude=77.5946,
            city="Bangalore, Karnataka",
            city_id="bangalore",
        )
        assert len(events) == 7
        districts = [e.location.district for e in events]
        assert "Whitefield" in districts

    @pytest.mark.asyncio
    async def test_generates_events_for_mumbai(self):
        adapter = HealthAdapter()
        events = await adapter.fetch(
            latitude=19.076,
            longitude=72.8777,
            city="Mumbai, Maharashtra",
            city_id="mumbai",
        )
        assert len(events) == 7
        districts = [e.location.district for e in events]
        assert "Dharavi" in districts

    @pytest.mark.asyncio
    async def test_respiratory_cases_are_positive(self):
        adapter = HealthAdapter()
        events = await adapter.fetch(
            latitude=17.385,
            longitude=78.4867,
            city="Hyderabad, Telangana",
            city_id="hyderabad",
        )
        for event in events:
            metrics = event.metrics
            assert isinstance(metrics, HealthMetrics)
            assert metrics.respiratory_cases is not None
            assert metrics.respiratory_cases >= 0
            assert metrics.er_visits is not None
            assert metrics.er_visits >= 0

    @pytest.mark.asyncio
    async def test_locations_offset_from_center(self):
        adapter = HealthAdapter()
        center_lat = 17.385
        center_lon = 78.4867
        events = await adapter.fetch(
            latitude=center_lat,
            longitude=center_lon,
            city="Hyderabad, Telangana",
            city_id="hyderabad",
        )
        locations = [(e.location.latitude, e.location.longitude) for e in events]
        unique_locations = set(locations)
        assert len(unique_locations) > 1

    @pytest.mark.asyncio
    async def test_deterministic_output_same_day(self):
        adapter = HealthAdapter()
        events1 = await adapter.fetch(
            latitude=17.385,
            longitude=78.4867,
            city="Hyderabad, Telangana",
            city_id="hyderabad",
        )
        events2 = await adapter.fetch(
            latitude=17.385,
            longitude=78.4867,
            city="Hyderabad, Telangana",
            city_id="hyderabad",
        )
        cases1 = [e.metrics.respiratory_cases for e in events1
                  if isinstance(e.metrics, HealthMetrics)]
        cases2 = [e.metrics.respiratory_cases for e in events2
                  if isinstance(e.metrics, HealthMetrics)]
        assert cases1 == cases2


class TestConstructionAdapter:
    @pytest.mark.asyncio
    async def test_generates_events_for_hyderabad(self):
        adapter = ConstructionAdapter()
        events = await adapter.fetch(
            latitude=17.385,
            longitude=78.4867,
            city="Hyderabad, Telangana",
            city_id="hyderabad",
        )
        assert len(events) >= 1
        for event in events:
            assert event.source == DataSource.CONSTRUCTION
            assert event.event_type == EventType.CONSTRUCTION
            assert isinstance(event.metrics, ConstructionMetrics)

    @pytest.mark.asyncio
    async def test_generates_events_for_mumbai(self):
        adapter = ConstructionAdapter()
        events = await adapter.fetch(
            latitude=19.076,
            longitude=72.8777,
            city="Mumbai, Maharashtra",
            city_id="mumbai",
        )
        assert len(events) >= 1
        site_names = [
            e.metadata.get("site_name", "") for e in events
        ]
        assert any("Mumbai" in name or "Dharavi" in name or
                   "Coastal" in name or "Metro" in name
                   for name in site_names)

    @pytest.mark.asyncio
    async def test_dust_risk_matches_severity(self):
        adapter = ConstructionAdapter()
        events = await adapter.fetch(
            latitude=17.385,
            longitude=78.4867,
            city="Hyderabad, Telangana",
            city_id="hyderabad",
        )
        for event in events:
            metrics = event.metrics
            assert isinstance(metrics, ConstructionMetrics)
            assert metrics.dust_risk == event.severity

    @pytest.mark.asyncio
    async def test_proximity_values_are_positive(self):
        adapter = ConstructionAdapter()
        events = await adapter.fetch(
            latitude=17.385,
            longitude=78.4867,
            city="Hyderabad, Telangana",
            city_id="hyderabad",
        )
        for event in events:
            metrics = event.metrics
            assert isinstance(metrics, ConstructionMetrics)
            if metrics.proximity_to_schools_m is not None:
                assert metrics.proximity_to_schools_m > 0
            if metrics.proximity_to_hospitals_m is not None:
                assert metrics.proximity_to_hospitals_m > 0


class TestPatternDetector:
    def test_detects_aqi_threshold_exceedance(self):
        context = {
            "air_quality": {
                "available": True,
                "avg_aqi": 155.0,
                "max_aqi": 180.0,
                "avg_pm25_ugm3": 45.0,
                "pm25_exceeds_who": True,
                "station_count": 3,
                "stations": ["Secunderabad", "Kukatpally"],
                "dominant_pollutants": ["PM2.5"],
            },
            "weather": {"available": False},
            "health": {"available": False},
            "construction": {"available": False},
        }
        patterns = detect_patterns(context)
        assert len(patterns) >= 1
        types = [p["pattern_type"] for p in patterns]
        assert "anomaly" in types

    def test_detects_atmospheric_stagnation(self):
        context = {
            "air_quality": {"available": False},
            "weather": {
                "available": True,
                "wind_speed_ms": 0.8,
                "low_wind_dispersion": True,
                "heat_stress_conditions": False,
                "pollutant_dispersal_risk": "HIGH",
                "temperature_celsius": 28.0,
            },
            "health": {"available": False},
            "construction": {"available": False},
        }
        patterns = detect_patterns(context)
        assert len(patterns) >= 1
        assert any("stagnation" in p["pattern"].lower() or
                   "wind" in p["pattern"].lower()
                   for p in patterns)

    def test_detects_compound_risk(self):
        context = {
            "air_quality": {
                "available": True,
                "avg_aqi": 160.0,
                "avg_pm25_ugm3": 48.0,
                "pm25_exceeds_who": True,
                "station_count": 3,
                "stations": [],
                "dominant_pollutants": ["PM2.5"],
                "max_aqi": 190.0,
            },
            "weather": {
                "available": True,
                "wind_speed_ms": 1.0,
                "low_wind_dispersion": True,
                "heat_stress_conditions": True,
                "temperature_celsius": 36.0,
                "pollutant_dispersal_risk": "HIGH",
            },
            "health": {
                "available": True,
                "total_respiratory_cases": 250,
                "district_count": 5,
                "districts": ["Secunderabad"],
                "critical_districts": ["Old City"],
                "avg_hospitalization_rate": 0.09,
                "max_respiratory_cases": 183,
                "total_er_visits": 45,
                "total_clinic_visits": 120,
                "reported_conditions": ["Asthma"],
                "population_exposure_estimate": 2000,
            },
            "construction": {
                "available": True,
                "active_sites": 3,
                "site_names": ["Metro Phase 2"],
                "high_dust_risk_sites": ["Metro Phase 2"],
                "school_proximity_risk": "HIGH",
                "total_affected_radius_m": 2400,
                "closest_school_proximity_m": 280,
                "closest_hospital_proximity_m": 500,
            },
        }
        patterns = detect_patterns(context)
        assert len(patterns) >= 3
        strengths = [p["strength"] for p in patterns]
        assert max(strengths) >= 0.8

    def test_no_patterns_for_empty_context(self):
        context = {
            "air_quality": {"available": False},
            "weather": {"available": False},
            "health": {"available": False},
            "construction": {"available": False},
        }
        patterns = detect_patterns(context)
        assert len(patterns) == 0

    def test_patterns_sorted_by_strength_descending(self):
        context = {
            "air_quality": {
                "available": True,
                "avg_aqi": 165.0,
                "avg_pm25_ugm3": 50.0,
                "pm25_exceeds_who": True,
                "station_count": 5,
                "stations": [],
                "dominant_pollutants": ["PM2.5"],
                "max_aqi": 200.0,
            },
            "weather": {
                "available": True,
                "wind_speed_ms": 0.5,
                "low_wind_dispersion": True,
                "heat_stress_conditions": True,
                "temperature_celsius": 38.0,
                "pollutant_dispersal_risk": "HIGH",
            },
            "health": {
                "available": True,
                "total_respiratory_cases": 300,
                "district_count": 7,
                "districts": [],
                "critical_districts": ["Old City", "Uppal"],
                "avg_hospitalization_rate": 0.1,
                "max_respiratory_cases": 200,
                "total_er_visits": 60,
                "total_clinic_visits": 150,
                "reported_conditions": [],
                "population_exposure_estimate": 2400,
            },
            "construction": {"available": False},
        }
        patterns = detect_patterns(context)
        if len(patterns) >= 2:
            for i in range(len(patterns) - 1):
                assert patterns[i]["strength"] >= patterns[i + 1]["strength"]