"""
Construction activity adapter for PRISM.

Generates realistic construction event data using city-specific
construction site configurations.
"""

import random
from datetime import datetime, timezone

from app.config_cities import get_city_config
from app.models.community import (
    CommunityEvent,
    ConstructionMetrics,
    DataSource,
    EventType,
    GeoLocation,
    SeverityLevel,
)
from app.services.ingestion.base_adapter import BaseAdapter


def _calculate_dust_risk(
    proximity_schools: float,
    proximity_hospitals: float,
    activity: str,
) -> SeverityLevel:
    """Calculate dust risk based on proximity and activity type."""
    score = 0
    high_dust = ["excavation", "demolition", "boring", "paving", "pile driving", "clearing"]
    if any(term in activity.lower() for term in high_dust):
        score += 2

    if proximity_schools < 500:
        score += 3
    elif proximity_schools < 1000:
        score += 2
    elif proximity_schools < 1500:
        score += 1

    if proximity_hospitals < 500:
        score += 3
    elif proximity_hospitals < 1000:
        score += 2

    if score >= 7:
        return SeverityLevel.CRITICAL
    if score >= 4:
        return SeverityLevel.HIGH
    if score >= 2:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


class ConstructionAdapter(BaseAdapter):
    """
    Simulated construction activity adapter for PRISM.

    Uses city-specific construction site configurations.
    """

    def _get_source(self) -> DataSource:
        return DataSource.CONSTRUCTION

    async def fetch(
        self,
        latitude: float,
        longitude: float,
        city: str,
        city_id: str = "hyderabad",
    ) -> list[CommunityEvent]:
        """Generate construction events for the city's active sites."""
        today = datetime.now(timezone.utc)
        seed = int(today.strftime("%Y%m%d")) + 42
        rng = random.Random(seed)

        config = get_city_config(city_id)
        events: list[CommunityEvent] = []

        for site in config.construction_sites:
            is_active_today = rng.random() > 0.15
            if not is_active_today:
                continue

            dust_risk = _calculate_dust_risk(
                site.proximity_schools,
                site.proximity_hospitals,
                site.activity,
            )

            metrics = ConstructionMetrics(
                activity_type=site.activity,
                dust_risk=dust_risk,
                proximity_to_schools_m=site.proximity_schools,
                proximity_to_hospitals_m=site.proximity_hospitals,
                estimated_duration_days=site.duration_days,
                affected_radius_m=site.radius_m,
            )

            safe_name = site.name.lower().replace(" ", "_").replace("—", "").replace("-", "_")

            event = CommunityEvent(
                source=DataSource.CONSTRUCTION,
                event_type=EventType.CONSTRUCTION,
                location=GeoLocation(
                    latitude=round(latitude + site.lat_offset, 6),
                    longitude=round(longitude + site.lon_offset, 6),
                    district=site.district,
                    city=city,
                ),
                timestamp=today.replace(
                    hour=rng.randint(6, 9), minute=0, second=0, microsecond=0
                ),
                severity=dust_risk,
                metrics=metrics,
                raw_source_id=f"construction_{safe_name}",
                metadata={
                    "site_name": site.name,
                    "permit_status": "Active",
                    "data_source": "Simulated Municipal Permit System",
                    "city_id": city_id,
                },
            )
            events.append(event)

        self.logger.info(
            "Construction adapter: Generated %d events for %s",
            len(events),
            city,
        )
        return events