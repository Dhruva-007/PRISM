"""
Health data adapter for PRISM.

Generates realistic health event data using city-specific district
configurations. Data is seeded deterministically by date for reproducibility.
"""

import random
from datetime import datetime, timezone

from app.config_cities import get_city_config
from app.models.community import (
    CommunityEvent,
    DataSource,
    EventType,
    GeoLocation,
    HealthMetrics,
    SeverityLevel,
)
from app.services.ingestion.base_adapter import BaseAdapter

AGE_GROUPS = ["0-14 years", "15-64 years", "65+ years", "All ages"]


def _severity_from_case_count(cases: int) -> SeverityLevel:
    """Classify severity based on reported case counts."""
    if cases >= 150:
        return SeverityLevel.CRITICAL
    if cases >= 80:
        return SeverityLevel.HIGH
    if cases >= 30:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


class HealthAdapter(BaseAdapter):
    """
    Simulated health data adapter for PRISM.

    Generates realistic daily health event records per district,
    using city-specific district configurations.
    """

    def _get_source(self) -> DataSource:
        return DataSource.HEALTH

    async def fetch(
        self,
        latitude: float,
        longitude: float,
        city: str,
        city_id: str = "hyderabad",
    ) -> list[CommunityEvent]:
        """Generate realistic health events for all districts in the city."""
        today = datetime.now(timezone.utc)
        seed = int(today.strftime("%Y%m%d"))
        rng = random.Random(seed)

        config = get_city_config(city_id)
        conditions = config.health_conditions or [
            "Acute respiratory infection",
            "Asthma exacerbation",
            "Bronchitis",
        ]

        base_respiratory = rng.randint(40, 120)
        trend_multiplier = rng.uniform(0.9, 1.4)

        events: list[CommunityEvent] = []

        for district in config.districts:
            district_multiplier = rng.uniform(0.6, 1.8)

            respiratory_cases = int(
                base_respiratory * trend_multiplier * district_multiplier
            )
            er_visits = int(respiratory_cases * rng.uniform(0.08, 0.18))
            clinic_visits = int(respiratory_cases * rng.uniform(0.35, 0.55))
            hospitalization_rate = round(rng.uniform(0.02, 0.12), 3)

            condition = rng.choice(conditions)
            age_group = rng.choice(AGE_GROUPS)

            metrics = HealthMetrics(
                respiratory_cases=respiratory_cases,
                er_visits=er_visits,
                clinic_visits=clinic_visits,
                hospitalization_rate=hospitalization_rate,
                affected_age_group=age_group,
                condition=condition,
            )

            event = CommunityEvent(
                source=DataSource.HEALTH,
                event_type=EventType.HEALTH_REPORT,
                location=GeoLocation(
                    latitude=round(latitude + district.lat_offset, 6),
                    longitude=round(longitude + district.lon_offset, 6),
                    district=district.name,
                    city=city,
                ),
                timestamp=today.replace(hour=8, minute=0, second=0, microsecond=0),
                severity=_severity_from_case_count(respiratory_cases),
                metrics=metrics,
                raw_source_id=f"health_{district.name.lower().replace(' ', '_')}_{today.strftime('%Y%m%d')}",
                metadata={
                    "report_type": "daily_aggregate",
                    "data_source": "Simulated HIE",
                    "district": district.name,
                    "city_id": city_id,
                },
            )
            events.append(event)

        self.logger.info(
            "Health adapter: Generated %d health events for %s",
            len(events),
            city,
        )
        return events