"""
Context assembler for PRISM Decision Intelligence Engine.

Gathers community events from Firestore, computes statistical summaries,
and structures everything into a clean context object ready for Gemini.

The quality of AI reasoning depends entirely on the quality of context.
This module ensures Gemini receives structured, relevant, deduplicated data.
"""

from datetime import datetime, timezone
from typing import Any

from app.integrations.firestore import get_firestore_client
from app.models.analysis import DataSummary
from app.models.community import EventType, SeverityLevel
from app.utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_EVENTS = "community_events"


def _safe_float(value: Any) -> float | None:
    """Safely convert a value to float, returning None on failure."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    """Safely convert a value to int, returning None on failure."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


async def assemble_context(
    latitude: float,
    longitude: float,
    location: str,
    time_window_hours: int,
) -> dict[str, Any]:
    """
    Assemble all relevant community data into a structured analysis context.

    Fetches recent events from Firestore, computes summaries per domain,
    and returns a dictionary structured for Gemini prompt construction.

    Args:
        latitude: Analysis center latitude
        longitude: Analysis center longitude
        location: Human-readable location name
        time_window_hours: How many hours of data to include

    Returns:
        Structured context dictionary with events, summaries, and statistics
    """
    client = get_firestore_client()

    # Fetch recent events — ordered by ingestion time descending
    # We fetch more than needed and filter client-side for flexibility
    query = (
        client.collection(COLLECTION_EVENTS)
        .order_by("ingested_at", direction="DESCENDING")
        .limit(200)
    )

    docs = list(query.stream())
    all_events = []
    for doc in docs:
        data = doc.to_dict()
        if data:
            data["id"] = doc.id
            all_events.append(data)

    logger.info(
        "Context assembler: Fetched %d events from Firestore", len(all_events)
    )

    # Separate by event type
    air_quality_events = [
        e for e in all_events if e.get("event_type") == EventType.AIR_QUALITY
    ]
    weather_events = [
        e for e in all_events if e.get("event_type") == EventType.WEATHER
    ]
    health_events = [
        e for e in all_events if e.get("event_type") == EventType.HEALTH_REPORT
    ]
    construction_events = [
        e for e in all_events if e.get("event_type") == EventType.CONSTRUCTION
    ]

    # Compute air quality summary
    aq_summary = _summarize_air_quality(air_quality_events)

    # Compute weather summary
    weather_summary = _summarize_weather(weather_events)

    # Compute health summary
    health_summary = _summarize_health(health_events)

    # Compute construction summary
    construction_summary = _summarize_construction(construction_events)

    # Determine dominant severity across all events
    severity_counts = {s.value: 0 for s in SeverityLevel}
    for event in all_events:
        sev = event.get("severity", "low")
        if sev in severity_counts:
            severity_counts[sev] += 1

    dominant_severity = max(severity_counts, key=lambda k: severity_counts[k])

    data_summary = DataSummary(
        total_events=len(all_events),
        air_quality_events=len(air_quality_events),
        weather_events=len(weather_events),
        health_events=len(health_events),
        construction_events=len(construction_events),
        time_window_hours=time_window_hours,
        location=location,
        avg_aqi=aq_summary.get("avg_aqi"),
        max_respiratory_cases=health_summary.get("max_respiratory_cases"),
        dominant_severity=dominant_severity,
    )

    context = {
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "time_window_hours": time_window_hours,
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "data_summary": data_summary,
        "event_ids": [e.get("id", "") for e in all_events],
        "air_quality": aq_summary,
        "weather": weather_summary,
        "health": health_summary,
        "construction": construction_summary,
        "severity_distribution": severity_counts,
    }

    logger.info(
        "Context assembled: %d total events | dominant_severity=%s",
        len(all_events),
        dominant_severity,
    )

    return context


def _summarize_air_quality(events: list[dict]) -> dict[str, Any]:
    """Compute statistical summary of air quality events."""
    if not events:
        return {"available": False, "station_count": 0}

    aqi_values = []
    pm25_values = []
    pm10_values = []
    no2_values = []
    dominant_pollutants = []
    stations = []

    for event in events:
        metrics = event.get("metrics", {})
        location = event.get("location", {})

        aqi = _safe_float(metrics.get("aqi"))
        if aqi is not None:
            aqi_values.append(aqi)

        pm25 = _safe_float(metrics.get("pm25"))
        if pm25 is not None:
            pm25_values.append(pm25)

        pm10 = _safe_float(metrics.get("pm10"))
        if pm10 is not None:
            pm10_values.append(pm10)

        no2 = _safe_float(metrics.get("no2"))
        if no2 is not None:
            no2_values.append(no2)

        dp = metrics.get("dominant_pollutant")
        if dp:
            dominant_pollutants.append(dp)

        station = location.get("district", "Unknown")
        if station not in stations:
            stations.append(station)

    return {
        "available": True,
        "station_count": len(events),
        "stations": stations,
        "avg_aqi": round(sum(aqi_values) / len(aqi_values), 1) if aqi_values else None,
        "max_aqi": round(max(aqi_values), 1) if aqi_values else None,
        "min_aqi": round(min(aqi_values), 1) if aqi_values else None,
        "avg_pm25_ugm3": round(sum(pm25_values) / len(pm25_values), 2) if pm25_values else None,
        "max_pm25_ugm3": round(max(pm25_values), 2) if pm25_values else None,
        "avg_pm10_ugm3": round(sum(pm10_values) / len(pm10_values), 2) if pm10_values else None,
        "avg_no2_ugm3": round(sum(no2_values) / len(no2_values), 2) if no2_values else None,
        "dominant_pollutants": list(set(dominant_pollutants)),
        "who_pm25_threshold_ugm3": 15.0,
        "pm25_exceeds_who": (
            (sum(pm25_values) / len(pm25_values)) > 15.0 if pm25_values else False
        ),
    }


def _summarize_weather(events: list[dict]) -> dict[str, Any]:
    """Compute summary of weather conditions."""
    if not events:
        return {"available": False}

    latest = events[0]
    metrics = latest.get("metrics", {})

    temp = _safe_float(metrics.get("temperature_celsius"))
    wind_speed = _safe_float(metrics.get("wind_speed_ms"))
    humidity = _safe_float(metrics.get("humidity_percent"))
    precipitation = _safe_float(metrics.get("precipitation_mm"))
    visibility = _safe_float(metrics.get("visibility_km"))

    low_wind_dispersion = wind_speed is not None and wind_speed < 2.0
    heat_stress = temp is not None and temp > 32.0
    poor_visibility = visibility is not None and visibility < 5.0

    return {
        "available": True,
        "temperature_celsius": temp,
        "wind_speed_ms": wind_speed,
        "humidity_percent": humidity,
        "precipitation_mm": precipitation,
        "visibility_km": visibility,
        "weather_condition": metrics.get("weather_condition"),
        "pressure_hpa": _safe_float(metrics.get("pressure_hpa")),
        "low_wind_dispersion": low_wind_dispersion,
        "heat_stress_conditions": heat_stress,
        "poor_visibility": poor_visibility,
        "pollutant_dispersal_risk": (
            "HIGH" if low_wind_dispersion else
            "MEDIUM" if (wind_speed is not None and wind_speed < 4.0) else "LOW"
        ),
    }


def _summarize_health(events: list[dict]) -> dict[str, Any]:
    """Compute summary of health report events."""
    if not events:
        return {"available": False, "district_count": 0}

    total_respiratory = 0
    total_er_visits = 0
    total_clinic_visits = 0
    hospitalization_rates = []
    conditions = []
    districts = []
    critical_districts = []

    for event in events:
        metrics = event.get("metrics", {})
        location = event.get("location", {})
        severity = event.get("severity", "low")
        district = location.get("district", "Unknown")

        resp = _safe_int(metrics.get("respiratory_cases"))
        if resp is not None:
            total_respiratory += resp

        er = _safe_int(metrics.get("er_visits"))
        if er is not None:
            total_er_visits += er

        clinic = _safe_int(metrics.get("clinic_visits"))
        if clinic is not None:
            total_clinic_visits += clinic

        hosp_rate = _safe_float(metrics.get("hospitalization_rate"))
        if hosp_rate is not None:
            hospitalization_rates.append(hosp_rate)

        condition = metrics.get("condition")
        if condition and condition not in conditions:
            conditions.append(condition)

        if district not in districts:
            districts.append(district)

        if severity in ("critical", "high"):
            critical_districts.append(district)

    max_cases = 0
    for event in events:
        metrics = event.get("metrics", {})
        resp = _safe_int(metrics.get("respiratory_cases"))
        if resp is not None and resp > max_cases:
            max_cases = resp

    return {
        "available": True,
        "district_count": len(events),
        "districts": districts,
        "total_respiratory_cases": total_respiratory,
        "total_er_visits": total_er_visits,
        "total_clinic_visits": total_clinic_visits,
        "avg_hospitalization_rate": (
            round(sum(hospitalization_rates) / len(hospitalization_rates), 4)
            if hospitalization_rates else None
        ),
        "max_respiratory_cases": max_cases,
        "reported_conditions": conditions,
        "critical_districts": critical_districts,
        "population_exposure_estimate": total_respiratory * 8,
    }


def _summarize_construction(events: list[dict]) -> dict[str, Any]:
    """Compute summary of construction activity events."""
    if not events:
        return {"available": False, "active_sites": 0}

    sites = []
    high_risk_sites = []
    total_affected_radius = 0.0
    min_school_proximity = float("inf")
    min_hospital_proximity = float("inf")

    for event in events:
        metrics = event.get("metrics", {})
        metadata = event.get("metadata", {})
        dust_risk = metrics.get("dust_risk", "low")
        site_name = metadata.get("site_name", "Unknown Site")

        sites.append(site_name)

        if dust_risk in ("high", "critical"):
            high_risk_sites.append(site_name)

        radius = _safe_float(metrics.get("affected_radius_m"))
        if radius is not None:
            total_affected_radius += radius

        school_prox = _safe_float(metrics.get("proximity_to_schools_m"))
        if school_prox is not None and school_prox < min_school_proximity:
            min_school_proximity = school_prox

        hosp_prox = _safe_float(metrics.get("proximity_to_hospitals_m"))
        if hosp_prox is not None and hosp_prox < min_hospital_proximity:
            min_hospital_proximity = hosp_prox

    return {
        "available": True,
        "active_sites": len(events),
        "site_names": sites,
        "high_dust_risk_sites": high_risk_sites,
        "total_affected_radius_m": round(total_affected_radius, 0),
        "closest_school_proximity_m": (
            round(min_school_proximity, 0)
            if min_school_proximity != float("inf") else None
        ),
        "closest_hospital_proximity_m": (
            round(min_hospital_proximity, 0)
            if min_hospital_proximity != float("inf") else None
        ),
        "school_proximity_risk": (
            "HIGH" if min_school_proximity < 500
            else "MEDIUM" if min_school_proximity < 1000
            else "LOW"
        ),
    }