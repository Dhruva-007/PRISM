"""
Community event data models for PRISM.

Every piece of external data that enters PRISM — air quality readings,
weather observations, health reports, traffic events, construction notices —
is normalized into a CommunityEvent before being stored in Firestore.

This is the canonical data schema for the ingestion pipeline.
All adapters must produce CommunityEvent instances.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class DataSource(str, Enum):
    """Supported external data sources."""

    OPENAQ = "openaq"
    NOAA = "noaa"
    OPEN_METEO = "open_meteo"
    OSM = "osm"
    HEALTH = "health"
    CONSTRUCTION = "construction"


class EventType(str, Enum):
    """Types of community events PRISM tracks."""

    AIR_QUALITY = "air_quality"
    WEATHER = "weather"
    TRAFFIC = "traffic"
    HEALTH_REPORT = "health_report"
    CONSTRUCTION = "construction"


class SeverityLevel(str, Enum):
    """Severity levels used consistently across PRISM."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GeoLocation(BaseModel):
    """Geographic location of a community event."""

    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    district: str = Field(default="Unknown District")
    city: str = Field(default="Metro Area")

    @field_validator("latitude", "longitude")
    @classmethod
    def round_coordinates(cls, v: float) -> float:
        """Round coordinates to 6 decimal places (sub-meter precision)."""
        return round(v, 6)


class AirQualityMetrics(BaseModel):
    """Metrics specific to air quality events."""

    aqi: float | None = Field(default=None, ge=0, le=500)
    pm25: float | None = Field(default=None, ge=0, description="PM2.5 µg/m³")
    pm10: float | None = Field(default=None, ge=0, description="PM10 µg/m³")
    no2: float | None = Field(default=None, ge=0, description="NO2 µg/m³")
    o3: float | None = Field(default=None, ge=0, description="Ozone µg/m³")
    co: float | None = Field(default=None, ge=0, description="CO mg/m³")
    so2: float | None = Field(default=None, ge=0, description="SO2 µg/m³")
    dominant_pollutant: str | None = None


class WeatherMetrics(BaseModel):
    """Metrics specific to weather events."""

    temperature_celsius: float | None = None
    humidity_percent: float | None = Field(default=None, ge=0, le=100)
    wind_speed_ms: float | None = Field(default=None, ge=0)
    wind_direction_degrees: float | None = Field(default=None, ge=0, le=360)
    precipitation_mm: float | None = Field(default=None, ge=0)
    pressure_hpa: float | None = None
    visibility_km: float | None = Field(default=None, ge=0)
    weather_condition: str | None = None


class HealthMetrics(BaseModel):
    """Metrics specific to health report events."""

    respiratory_cases: int | None = Field(default=None, ge=0)
    er_visits: int | None = Field(default=None, ge=0)
    clinic_visits: int | None = Field(default=None, ge=0)
    hospitalization_rate: float | None = Field(default=None, ge=0)
    affected_age_group: str | None = None
    condition: str | None = None


class TrafficMetrics(BaseModel):
    """Metrics specific to traffic events."""

    congestion_level: float | None = Field(default=None, ge=0, le=100)
    heavy_vehicle_count: int | None = Field(default=None, ge=0)
    affected_roads: list[str] = Field(default_factory=list)
    incident_type: str | None = None


class ConstructionMetrics(BaseModel):
    """Metrics specific to construction events."""

    activity_type: str | None = None
    dust_risk: SeverityLevel | None = None
    proximity_to_schools_m: float | None = Field(default=None, ge=0)
    proximity_to_hospitals_m: float | None = Field(default=None, ge=0)
    estimated_duration_days: int | None = Field(default=None, ge=0)
    affected_radius_m: float | None = Field(default=None, ge=0)


class CommunityEvent(BaseModel):
    """
    Canonical community event — the core data unit of PRISM.

    Every external data source is normalized into this model before
    storage in Firestore. The metrics field is a union of domain-specific
    metric models, keyed by event type.
    """

    id: str | None = None
    source: DataSource
    event_type: EventType
    location: GeoLocation
    timestamp: datetime
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    severity: SeverityLevel
    metrics: (
        AirQualityMetrics
        | WeatherMetrics
        | HealthMetrics
        | TrafficMetrics
        | ConstructionMetrics
    )
    raw_source_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metrics_match_event_type(self) -> "CommunityEvent":
        """Ensure metrics type matches event_type."""
        type_to_metrics = {
            EventType.AIR_QUALITY: AirQualityMetrics,
            EventType.WEATHER: WeatherMetrics,
            EventType.HEALTH_REPORT: HealthMetrics,
            EventType.TRAFFIC: TrafficMetrics,
            EventType.CONSTRUCTION: ConstructionMetrics,
        }
        expected = type_to_metrics[self.event_type]
        if not isinstance(self.metrics, expected):
            raise ValueError(
                f"Event type '{self.event_type}' requires "
                f"'{expected.__name__}' metrics, "
                f"got '{type(self.metrics).__name__}'"
            )
        return self

    def to_firestore_dict(self) -> dict[str, Any]:
        """
        Serialize to a Firestore-compatible dictionary.

        Converts datetime objects to ISO strings for Firestore storage.
        Firestore native timestamps are used via the client library
        when writing, but we store as ISO for portability.
        """
        data = self.model_dump(mode="json", exclude_none=True)
        return data


class CommunityEventResponse(BaseModel):
    """API response wrapper for a single community event."""

    event: CommunityEvent


class CommunityEventListResponse(BaseModel):
    """API response wrapper for paginated community events."""

    events: list[CommunityEvent]
    total: int
    limit: int
    offset: int


class IngestTriggerRequest(BaseModel):
    """Request body for triggering data ingestion."""

    sources: list[DataSource] = Field(
        default_factory=lambda: [
            DataSource.OPENAQ,
            DataSource.OPEN_METEO,
            DataSource.HEALTH,
            DataSource.CONSTRUCTION,
        ],
        description="Data sources to ingest from. Defaults to all implemented sources.",
    )
    city_id: str = Field(
        default="hyderabad",
        description="City identifier. Supported: hyderabad, delhi, bangalore, mumbai",
    )
    city: str = Field(default="")
    latitude: float = Field(default=0.0, ge=-90, le=90)
    longitude: float = Field(default=0.0, ge=-180, le=180)

    def model_post_init(self, __context: Any) -> None:
        """Resolve city config if city_id provided and lat/lon are defaults."""
        from app.config_cities import get_city_config
        config = get_city_config(self.city_id)
        if self.latitude == 0.0 and self.longitude == 0.0:
            self.latitude = config.latitude
            self.longitude = config.longitude
        if not self.city:
            self.city = f"{config.display_name}, {config.state}"


class IngestTriggerResponse(BaseModel):
    """Response from triggering data ingestion."""

    status: str
    events_ingested: int
    sources_attempted: list[str]
    sources_succeeded: list[str]
    sources_failed: list[str]
    message: str