"""
Pattern detector for PRISM Decision Intelligence Engine.

Identifies statistical anomalies and cross-domain correlations
in community data before sending context to Gemini.

Pre-computed patterns improve Gemini reasoning quality by providing
structured observations rather than requiring the model to perform
numerical analysis on raw data.
"""

from typing import Any

from app.utils.logging import get_logger

logger = get_logger(__name__)

# WHO air quality guideline thresholds (24-hour mean)
WHO_PM25_THRESHOLD = 15.0
WHO_PM10_THRESHOLD = 45.0
WHO_NO2_THRESHOLD = 25.0

# AQI risk thresholds
AQI_MODERATE = 51
AQI_UNHEALTHY_SENSITIVE = 101
AQI_UNHEALTHY = 151
AQI_VERY_UNHEALTHY = 201

# Wind speed thresholds for pollutant dispersal (m/s)
WIND_POOR_DISPERSAL = 2.0
WIND_MODERATE_DISPERSAL = 4.0

# Health case count thresholds for anomaly detection
HEALTH_ELEVATED_THRESHOLD = 80
HEALTH_HIGH_THRESHOLD = 150


def detect_patterns(context: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect patterns and anomalies in the assembled community context.

    Analyzes cross-domain relationships that indicate compounding risk —
    e.g., high PM2.5 + low wind speed + high respiratory cases is a
    much stronger signal than any single factor alone.

    Args:
        context: Assembled community context from context_assembler

    Returns:
        List of detected pattern dictionaries with type, description,
        strength, and supporting evidence
    """
    patterns = []

    aq = context.get("air_quality", {})
    weather = context.get("weather", {})
    health = context.get("health", {})
    construction = context.get("construction", {})

    # Pattern 1: Air quality WHO threshold exceedance
    if aq.get("available") and aq.get("pm25_exceeds_who"):
        avg_pm25 = aq.get("avg_pm25_ugm3", 0) or 0
        excess_ratio = avg_pm25 / WHO_PM25_THRESHOLD if WHO_PM25_THRESHOLD > 0 else 1
        strength = min(1.0, excess_ratio / 3.0)

        patterns.append({
            "pattern": (
                f"PM2.5 concentration averaging {avg_pm25:.1f} µg/m³ exceeds "
                f"WHO 24-hour guideline of {WHO_PM25_THRESHOLD} µg/m³ "
                f"by {excess_ratio:.1f}x across {aq.get('station_count', 0)} monitoring stations"
            ),
            "strength": round(strength, 3),
            "pattern_type": "anomaly",
            "data_sources": ["openaq"],
        })

    # Pattern 2: Atmospheric stagnation — low wind trapping pollutants
    if weather.get("available") and weather.get("low_wind_dispersion"):
        wind_speed = weather.get("wind_speed_ms", 0) or 0
        strength = max(0.3, 1.0 - (wind_speed / WIND_POOR_DISPERSAL))

        patterns.append({
            "pattern": (
                f"Atmospheric stagnation detected: wind speed {wind_speed:.1f} m/s "
                f"is below {WIND_POOR_DISPERSAL} m/s threshold for adequate "
                f"pollutant dispersal, causing ground-level pollutant accumulation"
            ),
            "strength": round(min(1.0, strength), 3),
            "pattern_type": "meteorological",
            "data_sources": ["open_meteo"],
        })

    # Pattern 3: Heat stress amplifying pollution effects
    if weather.get("available") and weather.get("heat_stress_conditions"):
        temp = weather.get("temperature_celsius", 0) or 0
        heat_strength = min(1.0, (temp - 32.0) / 10.0)

        patterns.append({
            "pattern": (
                f"Heat stress conditions: {temp:.1f}°C promotes ozone formation "
                f"and increases physiological vulnerability to air pollutants, "
                f"particularly for elderly and children"
            ),
            "strength": round(heat_strength, 3),
            "pattern_type": "correlation",
            "data_sources": ["open_meteo"],
        })

    # Pattern 4: Construction + poor air quality convergence
    if construction.get("available") and aq.get("available"):
        high_risk_sites = construction.get("high_dust_risk_sites", [])
        if high_risk_sites and (aq.get("avg_aqi") or 0) > AQI_MODERATE:
            school_risk = construction.get("school_proximity_risk", "LOW")
            strength = 0.6 if school_risk == "HIGH" else 0.4

            patterns.append({
                "pattern": (
                    f"{len(high_risk_sites)} high-dust-risk construction site(s) "
                    f"operating during elevated AQI conditions "
                    f"(AQI {aq.get('avg_aqi', 0):.0f}). "
                    f"Construction dust is compounding background pollution. "
                    f"School proximity risk: {school_risk}"
                ),
                "strength": round(strength, 3),
                "pattern_type": "correlation",
                "data_sources": ["construction", "openaq"],
            })

    # Pattern 5: Elevated respiratory cases in critical districts
    if health.get("available"):
        critical_districts = health.get("critical_districts", [])
        total_resp = health.get("total_respiratory_cases", 0) or 0

        if total_resp > HEALTH_HIGH_THRESHOLD or len(critical_districts) >= 2:
            strength = min(1.0, total_resp / 500.0)

            patterns.append({
                "pattern": (
                    f"Elevated respiratory case burden: {total_resp} total cases "
                    f"across {health.get('district_count', 0)} districts. "
                    f"{len(critical_districts)} district(s) at critical/high severity: "
                    f"{', '.join(critical_districts[:3])}"
                ),
                "strength": round(strength, 3),
                "pattern_type": "anomaly",
                "data_sources": ["health"],
            })

    # Pattern 6: Compound environmental health risk (cross-domain)
    if (
        aq.get("available")
        and weather.get("available")
        and health.get("available")
        and (aq.get("avg_aqi") or 0) > AQI_MODERATE
        and weather.get("low_wind_dispersion")
        and (health.get("total_respiratory_cases") or 0) > HEALTH_ELEVATED_THRESHOLD
    ):
        patterns.append({
            "pattern": (
                "COMPOUND RISK DETECTED: Simultaneous occurrence of elevated air "
                "pollution, atmospheric stagnation, and increased respiratory health "
                "burden indicates a compounding environmental health crisis. "
                "Individual factors are reinforcing each other."
            ),
            "strength": 0.92,
            "pattern_type": "correlation",
            "data_sources": ["openaq", "open_meteo", "health"],
        })

    # Sort by strength descending
    patterns.sort(key=lambda p: p["strength"], reverse=True)

    logger.info(
        "Pattern detector: Identified %d patterns", len(patterns)
    )

    return patterns