"""
Gemini 2.5 Flash reasoning engine for PRISM.

This module is the core of PRISM's Decision Intelligence capability.
It constructs carefully engineered prompts, sends them to Gemini 2.5 Flash
via Vertex AI, validates the structured JSON response, and returns
a complete SituationAnalysis.

Prompt engineering principles used here:
1. Explicit JSON schema definition in the prompt
2. Persona assignment (expert public health analyst)
3. Chain-of-thought reasoning before conclusions
4. Explicit uncertainty quantification
5. Evidence grounding — every conclusion must cite specific data
6. Conservative bias — err toward higher severity when uncertain
"""

import json
from typing import Any

from app.integrations.vertex_ai import get_gemini_model, get_generation_config
from app.models.analysis import (
    DataSummary,
    DetectedPattern,
    RootCause,
    SeverityLevel,
    SituationAnalysis,
    UrgencyLevel,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _build_analysis_prompt(
    context: dict[str, Any],
    patterns: list[dict[str, Any]],
) -> str:
    """
    Build the Gemini analysis prompt.

    The prompt is structured to produce consistent, high-quality
    JSON output every time. It includes:
    - Role and context framing
    - Complete data summary
    - Pre-detected patterns
    - Exact JSON schema required
    - Reasoning instructions
    """
    aq = context.get("air_quality", {})
    weather = context.get("weather", {})
    health = context.get("health", {})
    construction = context.get("construction", {})
    location = context.get("location", "Metro Area")
    time_window = context.get("time_window_hours", 24)

    patterns_text = ""
    if patterns:
        patterns_text = "\n".join([
            f"- [{p['pattern_type'].upper()}] (strength={p['strength']:.2f}) {p['pattern']}"
            for p in patterns
        ])
    else:
        patterns_text = "No significant patterns pre-detected. Analyze the raw data."

    aq_section = ""
    if aq.get("available"):
        aq_section = f"""
AIR QUALITY DATA ({aq.get('station_count', 0)} monitoring stations):
- Average AQI: {aq.get('avg_aqi', 'N/A')} | Max AQI: {aq.get('max_aqi', 'N/A')}
- Average PM2.5: {aq.get('avg_pm25_ugm3', 'N/A')} µg/m³ (WHO limit: 15.0 µg/m³)
- Average PM10: {aq.get('avg_pm10_ugm3', 'N/A')} µg/m³ (WHO limit: 45.0 µg/m³)
- Average NO2: {aq.get('avg_no2_ugm3', 'N/A')} µg/m³
- Dominant pollutants: {', '.join(aq.get('dominant_pollutants', [])) or 'None identified'}
- Exceeds WHO PM2.5 guideline: {aq.get('pm25_exceeds_who', False)}
- Monitoring stations: {', '.join(aq.get('stations', [])[:5])}"""
    else:
        aq_section = "\nAIR QUALITY DATA: Not available in current dataset."

    weather_section = ""
    if weather.get("available"):
        weather_section = f"""
METEOROLOGICAL CONDITIONS:
- Temperature: {weather.get('temperature_celsius', 'N/A')}°C
- Wind speed: {weather.get('wind_speed_ms', 'N/A')} m/s
- Humidity: {weather.get('humidity_percent', 'N/A')}%
- Precipitation: {weather.get('precipitation_mm', 'N/A')} mm
- Visibility: {weather.get('visibility_km', 'N/A')} km
- Weather condition: {weather.get('weather_condition', 'N/A')}
- Pollutant dispersal risk: {weather.get('pollutant_dispersal_risk', 'UNKNOWN')}
- Atmospheric stagnation: {weather.get('low_wind_dispersion', False)}
- Heat stress conditions: {weather.get('heat_stress_conditions', False)}"""
    else:
        weather_section = "\nMETEOROLOGICAL CONDITIONS: Not available."

    health_section = ""
    if health.get("available"):
        health_section = f"""
PUBLIC HEALTH DATA ({health.get('district_count', 0)} districts):
- Total respiratory cases reported: {health.get('total_respiratory_cases', 0)}
- Total ER visits: {health.get('total_er_visits', 0)}
- Total clinic visits: {health.get('total_clinic_visits', 0)}
- Average hospitalization rate: {health.get('avg_hospitalization_rate', 'N/A')}
- Reported conditions: {', '.join(health.get('reported_conditions', []))}
- Critical/high severity districts: {', '.join(health.get('critical_districts', [])) or 'None'}
- Estimated exposed population: {health.get('population_exposure_estimate', 0):,}"""
    else:
        health_section = "\nPUBLIC HEALTH DATA: Not available."

    construction_section = ""
    if construction.get("available"):
        construction_section = f"""
CONSTRUCTION ACTIVITY ({construction.get('active_sites', 0)} active sites):
- Active construction sites: {', '.join(construction.get('site_names', []))}
- High dust risk sites: {', '.join(construction.get('high_dust_risk_sites', [])) or 'None'}
- Closest school proximity: {construction.get('closest_school_proximity_m', 'N/A')} meters
- Closest hospital proximity: {construction.get('closest_hospital_proximity_m', 'N/A')} meters
- School proximity risk level: {construction.get('school_proximity_risk', 'UNKNOWN')}
- Total affected area radius: {construction.get('total_affected_radius_m', 0)} meters"""
    else:
        construction_section = "\nCONSTRUCTION ACTIVITY: No active sites detected."

    prompt = f"""You are PRISM, an expert Decision Intelligence System specializing in community health and environmental analysis. You work for municipal governments and international health organizations.

ANALYSIS REQUEST:
Location: {location}
Time window: Last {time_window} hours
Domain: Community Health & Environmental Intervention

COMMUNITY DATA SUMMARY:
{aq_section}
{weather_section}
{health_section}
{construction_section}

PRE-DETECTED PATTERNS (computed from statistical analysis):
{patterns_text}

YOUR TASK:
Perform a comprehensive situation analysis of the community health and environmental conditions described above. Identify root causes, assess severity, determine urgency, and provide an evidence-based assessment that will guide intervention decisions.

CRITICAL INSTRUCTIONS:
1. Ground every conclusion in specific data points from the summary above
2. Identify the interactions between domains (air quality + weather + health + construction)
3. Be specific about which populations are most at risk and why
4. Distinguish between primary causes and contributing factors
5. Quantify your confidence based on data completeness
6. If data is limited, state this explicitly and adjust confidence accordingly

Respond with ONLY valid JSON matching this exact schema:

{{
  "headline": "One sentence summarizing the most critical finding (max 100 chars)",
  "summary": "2-3 paragraph comprehensive situation summary with evidence citations",
  "severity_level": "low|medium|high|critical",
  "urgency": "routine|elevated|urgent|emergency",
  "confidence_overall": 0.0,
  "population_at_risk": "Description of who is most at risk and estimated numbers",
  "recommended_action_timeframe": "How quickly action should be taken and why",
  "key_findings": [
    "Finding 1 with specific data citation",
    "Finding 2 with specific data citation",
    "Finding 3 with specific data citation"
  ],
  "root_causes": [
    {{
      "cause": "Clear description of root cause",
      "confidence": 0.0,
      "category": "environmental|behavioral|infrastructure|meteorological",
      "supporting_evidence": ["Evidence 1", "Evidence 2"],
      "affected_population": "Who this specifically impacts"
    }}
  ],
  "patterns_detected": [
    {{
      "pattern": "Description of detected pattern",
      "strength": 0.0,
      "pattern_type": "temporal|spatial|correlation|anomaly",
      "data_sources": ["source1", "source2"]
    }}
  ],
  "gemini_reasoning": "Your detailed reasoning process — show your analytical work, explain how you weighted different factors, and explain any uncertainties or limitations in your analysis"
}}

Produce between 2 and 4 root causes. Produce between 1 and 4 patterns. All float values between 0.0 and 1.0. Be thorough but precise."""

    return prompt


def _parse_gemini_response(
    raw_response: str,
    context: dict[str, Any],
    patterns: list[dict[str, Any]],
) -> SituationAnalysis:
    """
    Parse and validate Gemini's JSON response into a SituationAnalysis.

    Handles partial responses and validation errors gracefully.
    Always returns a valid SituationAnalysis, even if degraded.
    """
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned invalid JSON: %s", exc)
        logger.debug("Raw response: %s", raw_response[:500])
        return _create_fallback_analysis(context, str(exc))

    try:
        root_causes = [
            RootCause(
                cause=rc.get("cause", "Unknown cause"),
                confidence=float(rc.get("confidence", 0.5)),
                category=rc.get("category", "environmental"),
                supporting_evidence=rc.get("supporting_evidence", []),
                affected_population=rc.get("affected_population"),
            )
            for rc in data.get("root_causes", [])
        ]
    except Exception as exc:
        logger.warning("Failed to parse root causes: %s", exc)
        root_causes = []

    try:
        detected_patterns = [
            DetectedPattern(
                pattern=p.get("pattern", "Unknown pattern"),
                strength=float(p.get("strength", 0.5)),
                pattern_type=p.get("pattern_type", "anomaly"),
                data_sources=p.get("data_sources", []),
            )
            for p in data.get("patterns_detected", [])
        ]
    except Exception as exc:
        logger.warning("Failed to parse patterns: %s", exc)
        detected_patterns = [
            DetectedPattern(
                pattern=p["pattern"],
                strength=p["strength"],
                pattern_type=p["pattern_type"],
                data_sources=p["data_sources"],
            )
            for p in patterns[:3]
        ]

    try:
        severity = SeverityLevel(data.get("severity_level", "low"))
    except ValueError:
        severity = SeverityLevel.MEDIUM

    try:
        urgency = UrgencyLevel(data.get("urgency", "routine"))
    except ValueError:
        urgency = UrgencyLevel.ELEVATED

    data_summary = context.get("data_summary")

    return SituationAnalysis(
        severity_level=severity,
        urgency=urgency,
        headline=data.get("headline", "Community health situation analysis complete"),
        summary=data.get("summary", "Analysis complete. See key findings for details."),
        root_causes=root_causes,
        patterns_detected=detected_patterns,
        key_findings=data.get("key_findings", []),
        population_at_risk=data.get("population_at_risk", "General population"),
        recommended_action_timeframe=data.get("recommended_action_timeframe", ""),
        gemini_reasoning=data.get("gemini_reasoning", ""),
        confidence_overall=float(data.get("confidence_overall", 0.5)),
        data_summary=data_summary,
    )


def _create_fallback_analysis(
    context: dict[str, Any],
    error: str,
) -> SituationAnalysis:
    """
    Create a degraded but valid analysis when Gemini fails.

    This ensures the API never returns an error — it returns a
    clearly marked fallback analysis instead.
    """
    data_summary = context.get("data_summary")
    return SituationAnalysis(
        severity_level=SeverityLevel.MEDIUM,
        urgency=UrgencyLevel.ELEVATED,
        headline="Analysis degraded — AI reasoning unavailable",
        summary=(
            "The PRISM AI reasoning engine encountered an error. "
            "Data was successfully ingested but Gemini analysis failed. "
            f"Error: {error}"
        ),
        root_causes=[],
        patterns_detected=[],
        key_findings=["AI analysis unavailable — review raw data manually"],
        population_at_risk="Unable to determine — AI analysis failed",
        recommended_action_timeframe="Manual review required",
        gemini_reasoning=f"Analysis failed: {error}",
        confidence_overall=0.0,
        data_summary=data_summary,
        error_message=error,
    )


async def run_analysis(
    context: dict[str, Any],
    patterns: list[dict[str, Any]],
) -> SituationAnalysis:
    """
    Run the full Gemini 2.5 Flash analysis.

    Builds the prompt, calls Gemini, parses the response,
    and returns a validated SituationAnalysis.

    Args:
        context: Assembled community context
        patterns: Pre-detected patterns from pattern_detector

    Returns:
        Complete SituationAnalysis with AI reasoning
    """
    logger.info("Starting Gemini analysis...")

    prompt = _build_analysis_prompt(context, patterns)

    logger.debug("Prompt length: %d characters", len(prompt))

    try:
        model = get_gemini_model()
        config = get_generation_config(
            temperature=0.1,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )

        response = model.generate_content(
            contents=prompt,
            generation_config=config,
        )

        raw_text = response.text
        logger.info(
            "Gemini response received: %d characters", len(raw_text)
        )
        logger.debug("Gemini raw response: %s", raw_text[:1000])

        analysis = _parse_gemini_response(raw_text, context, patterns)

        logger.info(
            "Analysis complete: severity=%s urgency=%s confidence=%.2f",
            analysis.severity_level,
            analysis.urgency,
            analysis.confidence_overall,
        )

        return analysis

    except Exception as exc:
        logger.error("Gemini analysis failed: %s", exc, exc_info=True)
        return _create_fallback_analysis(context, str(exc))