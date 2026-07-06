"""
OpenAQ data adapter for PRISM.

Fetches real air quality measurements from the OpenAQ API v3.
OpenAQ aggregates data from government air quality monitoring
stations worldwide — no API key required for basic access.

API documentation: https://docs.openaq.org/
"""

from datetime import datetime, timezone

import httpx

from app.models.community import (
    AirQualityMetrics,
    CommunityEvent,
    DataSource,
    EventType,
    GeoLocation,
    SeverityLevel,
)
from app.services.ingestion.base_adapter import BaseAdapter


def _calculate_aqi_severity(aqi: float | None, pm25: float | None) -> SeverityLevel:
    """
    Determine severity from AQI or PM2.5 value.

    Uses US EPA AQI breakpoints:
    0-50: Good (low)
    51-100: Moderate (low)
    101-150: Unhealthy for Sensitive Groups (medium)
    151-200: Unhealthy (high)
    201+: Very Unhealthy / Hazardous (critical)
    """
    value = aqi if aqi is not None else (pm25 * 4 if pm25 is not None else None)

    if value is None:
        return SeverityLevel.LOW
    if value <= 50:
        return SeverityLevel.LOW
    if value <= 100:
        return SeverityLevel.LOW
    if value <= 150:
        return SeverityLevel.MEDIUM
    if value <= 200:
        return SeverityLevel.HIGH
    return SeverityLevel.CRITICAL


def _determine_dominant_pollutant(
    pm25: float | None,
    pm10: float | None,
    no2: float | None,
    o3: float | None,
) -> str | None:
    """Return the pollutant with the highest normalized concentration."""
    candidates = {
        "PM2.5": pm25,
        "PM10": pm10,
        "NO2": no2,
        "O3": o3,
    }
    valid = {k: v for k, v in candidates.items() if v is not None}
    if not valid:
        return None
    return max(valid, key=lambda k: valid[k])


class OpenAQAdapter(BaseAdapter):
    """
    Adapter for OpenAQ API v3.

    Fetches the latest air quality measurements for monitoring
    stations within a radius of the target location.
    """

    OPENAQ_BASE_URL = "https://api.openaq.org/v3"
    SEARCH_RADIUS_KM = 50
    MAX_LOCATIONS = 5

    def _get_source(self) -> DataSource:
        return DataSource.OPENAQ

    async def fetch(
        self,
        latitude: float,
        longitude: float,
        city: str,
        city_id: str = "hyderabad"
    ) -> list[CommunityEvent]:
        """
        Fetch air quality measurements near the target location.

        Strategy:
        1. Find monitoring locations within SEARCH_RADIUS_KM
        2. For each location, fetch latest measurements
        3. Normalize each measurement into CommunityEvent
        """
        events: list[CommunityEvent] = []

        try:
            async with await self._get_http_client() as client:
                locations = await self._fetch_nearby_locations(
                    client, latitude, longitude
                )

                if not locations:
                    self.logger.warning(
                        "OpenAQ: No monitoring stations found near lat=%s lon=%s",
                        latitude,
                        longitude,
                    )
                    return []

                self.logger.info(
                    "OpenAQ: Found %d monitoring stations", len(locations)
                )

                for location in locations[: self.MAX_LOCATIONS]:
                    event = await self._fetch_location_measurements(
                        client, location, city
                    )
                    if event is not None:
                        events.append(event)

        except httpx.TimeoutException:
            self.logger.error("OpenAQ: Request timed out")
        except httpx.HTTPError as exc:
            self.logger.error("OpenAQ: HTTP error: %s", exc)
        except Exception as exc:
            self.logger.error("OpenAQ: Unexpected error: %s", exc)

        self.logger.info("OpenAQ: Ingested %d air quality events", len(events))
        return events

    async def _fetch_nearby_locations(
        self,
        client: httpx.AsyncClient,
        latitude: float,
        longitude: float,
    ) -> list[dict]:
        """Find monitoring stations near the target coordinates."""
        response = await client.get(
            f"{self.OPENAQ_BASE_URL}/locations",
            params={
                "coordinates": f"{latitude},{longitude}",
                "radius": self.SEARCH_RADIUS_KM * 1000,
                "limit": self.MAX_LOCATIONS,
                "order_by": "distance",
            },
        )

        if response.status_code != 200:
            self.logger.warning(
                "OpenAQ locations endpoint returned %d", response.status_code
            )
            return []

        data = response.json()
        return data.get("results", [])

    async def _fetch_location_measurements(
        self,
        client: httpx.AsyncClient,
        location: dict,
        city: str,
    ) -> CommunityEvent | None:
        """Fetch and normalize the latest measurements for a location."""
        location_id = location.get("id")
        if not location_id:
            return None

        try:
            response = await client.get(
                f"{self.OPENAQ_BASE_URL}/locations/{location_id}/latest",
            )

            if response.status_code != 200:
                return None

            data = response.json()
            results = data.get("results", [])
            if not results:
                return None

            pm25: float | None = None
            pm10: float | None = None
            no2: float | None = None
            o3: float | None = None
            co: float | None = None
            so2: float | None = None

            latest_time: datetime | None = None

            for measurement in results:
                parameter = measurement.get("parameter", "").lower()
                value = measurement.get("value")
                unit = measurement.get("unit", "")

                if value is None or value < 0:
                    continue

                datetime_str = measurement.get("lastUpdated") or measurement.get(
                    "datetime", {}).get("utc")
                if datetime_str:
                    try:
                        t = datetime.fromisoformat(
                            datetime_str.replace("Z", "+00:00")
                        )
                        if latest_time is None or t > latest_time:
                            latest_time = t
                    except ValueError:
                        pass

                if parameter in ("pm25", "pm2.5"):
                    pm25 = round(float(value), 2)
                elif parameter == "pm10":
                    pm10 = round(float(value), 2)
                elif parameter == "no2":
                    no2 = round(float(value), 2)
                elif parameter in ("o3", "ozone"):
                    o3 = round(float(value), 2)
                elif parameter == "co":
                    co = round(float(value), 2)
                elif parameter == "so2":
                    so2 = round(float(value), 2)

            aqi = self._estimate_aqi_from_pm25(pm25)

            metrics = AirQualityMetrics(
                aqi=aqi,
                pm25=pm25,
                pm10=pm10,
                no2=no2,
                o3=o3,
                co=co,
                so2=so2,
                dominant_pollutant=_determine_dominant_pollutant(
                    pm25, pm10, no2, o3
                ),
            )

            coords = location.get("coordinates", {})
            loc_lat = coords.get("latitude", 0.0)
            loc_lon = coords.get("longitude", 0.0)

            return CommunityEvent(
                source=DataSource.OPENAQ,
                event_type=EventType.AIR_QUALITY,
                location=GeoLocation(
                    latitude=loc_lat,
                    longitude=loc_lon,
                    district=location.get("name", "Unknown Station"),
                    city=city,
                ),
                timestamp=latest_time or datetime.now(timezone.utc),
                severity=_calculate_aqi_severity(aqi, pm25),
                metrics=metrics,
                raw_source_id=str(location_id),
                metadata={
                    "station_name": location.get("name"),
                    "country": location.get("country", {}).get("code"),
                    "is_mobile": location.get("isMobile", False),
                },
            )

        except Exception as exc:
            self.logger.warning(
                "OpenAQ: Failed to parse location %s: %s", location_id, exc
            )
            return None

    def _estimate_aqi_from_pm25(self, pm25: float | None) -> float | None:
        """
        Estimate AQI from PM2.5 using US EPA linear interpolation.

        PM2.5 breakpoints (µg/m³) → AQI breakpoints:
        0.0-12.0  → 0-50
        12.1-35.4 → 51-100
        35.5-55.4 → 101-150
        55.5-150.4 → 151-200
        150.5-250.4 → 201-300
        """
        if pm25 is None:
            return None

        breakpoints = [
            (0.0, 12.0, 0, 50),
            (12.1, 35.4, 51, 100),
            (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200),
            (150.5, 250.4, 201, 300),
            (250.5, 500.0, 301, 500),
        ]

        for c_low, c_high, i_low, i_high in breakpoints:
            if c_low <= pm25 <= c_high:
                aqi = ((i_high - i_low) / (c_high - c_low)) * (
                    pm25 - c_low
                ) + i_low
                return round(aqi, 1)

        return min(500.0, pm25 * 2)