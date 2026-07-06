"""
Open-Meteo weather adapter for PRISM.

Open-Meteo is a free, open-source weather API that requires no API key.
It provides current weather conditions using high-resolution forecast models.

API documentation: https://open-meteo.com/en/docs
"""

from datetime import datetime, timezone

import httpx

from app.models.community import (
    CommunityEvent,
    DataSource,
    EventType,
    GeoLocation,
    SeverityLevel,
    WeatherMetrics,
)
from app.services.ingestion.base_adapter import BaseAdapter


def _classify_weather_condition(
    weather_code: int | None,
    wind_speed: float | None,
    precipitation: float | None,
) -> str:
    """
    Map WMO weather interpretation codes to human-readable conditions.

    WMO codes: https://open-meteo.com/en/docs#weathervariables
    """
    if weather_code is None:
        return "Unknown"

    wmo_map = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight showers",
        81: "Moderate showers",
        82: "Violent showers",
        95: "Thunderstorm",
        99: "Thunderstorm with hail",
    }

    return wmo_map.get(weather_code, f"WMO code {weather_code}")


def _calculate_weather_severity(
    temperature: float | None,
    wind_speed: float | None,
    precipitation: float | None,
    weather_code: int | None,
) -> SeverityLevel:
    """
    Calculate weather severity based on combined factors.

    Factors relevant to respiratory health:
    - High temperature: increases ozone formation
    - Low wind speed: reduces pollutant dispersal
    - High precipitation: washes pollutants (actually helpful)
    - Storm conditions: air quality impacts
    """
    score = 0

    if temperature is not None:
        if temperature >= 38:
            score += 3
        elif temperature >= 33:
            score += 2
        elif temperature >= 28:
            score += 1

    if wind_speed is not None:
        if wind_speed <= 1.0:
            score += 3
        elif wind_speed <= 3.0:
            score += 2
        elif wind_speed <= 5.0:
            score += 1

    if weather_code in (95, 99):
        score += 2
    elif weather_code in (45, 48):
        score += 2
    elif weather_code in (65, 82):
        score += 1

    if score >= 6:
        return SeverityLevel.CRITICAL
    if score >= 4:
        return SeverityLevel.HIGH
    if score >= 2:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


class OpenMeteoAdapter(BaseAdapter):
    """
    Adapter for Open-Meteo free weather API.

    Fetches current weather conditions for the target location.
    No API key required. Rate limit: 10,000 requests/day (generous).
    """

    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

    def _get_source(self) -> DataSource:
        return DataSource.OPEN_METEO

    async def fetch(
        self,
        latitude: float,
        longitude: float,
        city: str,
        city_id: str = "hyderabad"
    ) -> list[CommunityEvent]:
        """
        Fetch current weather for the target location.

        Returns a single CommunityEvent with weather metrics.
        """
        try:
            async with await self._get_http_client() as client:
                response = await client.get(
                    self.OPEN_METEO_URL,
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "current": [
                            "temperature_2m",
                            "relative_humidity_2m",
                            "precipitation",
                            "weather_code",
                            "wind_speed_10m",
                            "wind_direction_10m",
                            "surface_pressure",
                            "visibility",
                        ],
                        "wind_speed_unit": "ms",
                        "timezone": "auto",
                    },
                )

                if response.status_code != 200:
                    self.logger.warning(
                        "Open-Meteo returned status %d", response.status_code
                    )
                    return []

                data = response.json()
                current = data.get("current", {})

                if not current:
                    self.logger.warning("Open-Meteo: No current weather data")
                    return []

                temperature = current.get("temperature_2m")
                humidity = current.get("relative_humidity_2m")
                precipitation = current.get("precipitation")
                weather_code = current.get("weather_code")
                wind_speed = current.get("wind_speed_10m")
                wind_direction = current.get("wind_direction_10m")
                pressure = current.get("surface_pressure")
                visibility_m = current.get("visibility")

                visibility_km = (
                    round(visibility_m / 1000, 2)
                    if visibility_m is not None
                    else None
                )

                metrics = WeatherMetrics(
                    temperature_celsius=(
                        round(temperature, 1) if temperature is not None else None
                    ),
                    humidity_percent=(
                        round(humidity, 1) if humidity is not None else None
                    ),
                    wind_speed_ms=(
                        round(wind_speed, 2) if wind_speed is not None else None
                    ),
                    wind_direction_degrees=(
                        round(wind_direction, 1)
                        if wind_direction is not None
                        else None
                    ),
                    precipitation_mm=(
                        round(precipitation, 2)
                        if precipitation is not None
                        else None
                    ),
                    pressure_hpa=(
                        round(pressure, 1) if pressure is not None else None
                    ),
                    visibility_km=visibility_km,
                    weather_condition=_classify_weather_condition(
                        weather_code, wind_speed, precipitation
                    ),
                )

                severity = _calculate_weather_severity(
                    temperature, wind_speed, precipitation, weather_code
                )

                time_str = current.get("time", "")
                try:
                    event_time = datetime.fromisoformat(time_str).replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    event_time = datetime.now(timezone.utc)

                event = CommunityEvent(
                    source=DataSource.OPEN_METEO,
                    event_type=EventType.WEATHER,
                    location=GeoLocation(
                        latitude=latitude,
                        longitude=longitude,
                        district="Meteorological Station",
                        city=city,
                    ),
                    timestamp=event_time,
                    severity=severity,
                    metrics=metrics,
                    raw_source_id=f"open_meteo_{latitude}_{longitude}",
                    metadata={
                        "timezone": data.get("timezone"),
                        "elevation_m": data.get("elevation"),
                        "weather_code": weather_code,
                    },
                )

                self.logger.info(
                    "Open-Meteo: Ingested weather event | temp=%.1f°C wind=%.1f m/s",
                    temperature or 0,
                    wind_speed or 0,
                )
                return [event]

        except httpx.TimeoutException:
            self.logger.error("Open-Meteo: Request timed out")
        except httpx.HTTPError as exc:
            self.logger.error("Open-Meteo: HTTP error: %s", exc)
        except Exception as exc:
            self.logger.error("Open-Meteo: Unexpected error: %s", exc)

        return []