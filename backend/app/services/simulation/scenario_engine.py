"""
Scenario simulation engine for PRISM.

Evaluates all intervention strategies simultaneously using Gemini 2.5 Flash,
scoring each across 5 dimensions and projecting 30-day outcomes.

Key design decisions:
1. All strategies scored in ONE Gemini call — ensures relative scoring
   (scores are meaningful compared to each other, not absolute)
2. Composite PRISM Score uses weighted average reflecting health mission
3. Scores are 0-100 with explicit rubrics in the prompt
4. Projections use actual baseline data from the analysis
5. Trade-offs must reference specific affected populations
"""

import json
from typing import Any

from app.integrations.vertex_ai import get_gemini_model, get_generation_config
from app.models.analysis import SituationAnalysis
from app.models.intervention import InterventionStrategy
from app.models.simulation import (
    ProjectedMetrics,
    ScoreBreakdown,
    SimulationResult,
    TradeOffItem,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

# PRISM Score dimension weights — reflect health-first mission
PRISM_WEIGHTS = {
    "health_impact": 0.35,
    "cost_efficiency": 0.20,
    "implementation_speed": 0.20,
    "community_acceptance": 0.15,
    "sustainability": 0.10,
}


def _compute_composite_score(scores: dict[str, float]) -> float:
    """
    Compute the composite PRISM Score from dimension scores.

    Weighted average reflecting PRISM's health-first mission.
    Health impact is weighted highest (35%) because PRISM's purpose
    is to improve community health outcomes.
    """
    composite = sum(
        scores.get(dim, 0) * weight
        for dim, weight in PRISM_WEIGHTS.items()
    )
    return round(composite, 1)


def _build_simulation_prompt(
    analysis: SituationAnalysis,
    strategies: list[InterventionStrategy],
) -> str:
    """
    Build the simulation prompt for Gemini.

    Includes all strategies in a single prompt to ensure
    relative scoring — scores only have meaning when compared
    to each other within the same analysis context.
    """
    strategies_text = ""
    for i, strategy in enumerate(strategies):
        actions_text = "\n".join([
            f"      - {a.action_id}: {a.title} (Day {a.timeline_days}, "
            f"Owner: {a.responsible_party})"
            for a in strategy.actions
        ])
        outcomes_text = "\n".join([
            f"      - {o.metric}: {o.baseline_value} → {o.expected_value} "
            f"({o.timeframe}, confidence: {o.confidence:.0%})"
            for o in strategy.expected_outcomes
        ])
        
        strategies_text += f"""
  STRATEGY {i+1} (index={i}): {strategy.title}
  Type: {strategy.strategy_type} | Cost: {strategy.total_estimated_cost}
  Description: {strategy.description[:300]}
  Actions: {"; ".join([f"{a.action_id}:{a.title}(Day {a.timeline_days})" for a in strategy.actions])}
  Key trade-offs: {"; ".join(strategy.trade_offs[:2])}
"""

    baseline_data = ""
    if analysis.data_summary:
        ds = analysis.data_summary
        baseline_data = f"""
BASELINE CONDITIONS:
- Location: {ds.location}
- Average AQI: {ds.avg_aqi or "Not available"}
- Total respiratory cases: {ds.max_respiratory_cases or "Not available"} (max district)
- Air quality stations: {ds.air_quality_events}
- Active construction sites: {ds.construction_events}
- Dominant severity: {ds.dominant_severity}"""

    prompt = f"""You are PRISM, an expert scenario simulation system for community health interventions.

SITUATION CONTEXT:
Severity: {analysis.severity_level.upper()} | Urgency: {analysis.urgency.upper()}
Assessment: {analysis.headline}
Population at risk: {analysis.population_at_risk}
{baseline_data}

STRATEGIES TO SIMULATE:
{strategies_text}

YOUR TASK:
Simulate the 30-day outcomes for ALL {len(strategies)} strategies and score each one.

SCORING RUBRIC (0-100 for each dimension):

health_impact (weight 35%):
  90-100: Eliminates or nearly eliminates the health risk
  70-89:  Significantly reduces health burden (>40% reduction)
  50-69:  Moderate reduction (20-40%)
  30-49:  Modest improvement (<20%)
  0-29:   Minimal or no health improvement

cost_efficiency (weight 20%):
  90-100: Very low cost, high impact ratio
  70-89:  Good cost-benefit balance
  50-69:  Moderate efficiency
  30-49:  High cost relative to benefit
  0-29:   Very poor cost efficiency

implementation_speed (weight 20%):
  90-100: Deployable within 24-48 hours
  70-89:  Deployable within 1 week
  50-69:  Deployable within 2-4 weeks
  30-49:  Requires 1-3 months
  0-29:   Requires more than 3 months

community_acceptance (weight 15%):
  90-100: High public support, minimal opposition
  70-89:  Broad acceptance with minor concerns
  50-69:  Mixed reception, some stakeholder resistance
  30-49:  Significant opposition expected
  0-29:   High likelihood of public/political rejection

sustainability (weight 10%):
  90-100: Creates permanent structural change
  70-89:  Durable improvement (>6 months)
  50-69:  Medium-term benefit (1-6 months)
  30-49:  Short-term improvement (<1 month)
  0-29:   Temporary fix with no lasting change

IMPORTANT: Scores must be RELATIVE to each other.
If Strategy 1 is clearly better than Strategy 2 on health impact, its score must be higher.
Do not give all strategies similar scores — differentiation is essential for decision-making.

For projections, use the baseline data provided. Be specific and quantitative.

Respond with ONLY valid JSON:

{{
  "simulations": [
    {{
      "strategy_index": 0,
      "scores": {{
        "health_impact": 0.0,
        "cost_efficiency": 0.0,
        "implementation_speed": 0.0,
        "community_acceptance": 0.0,
        "sustainability": 0.0
      }},
      "projection_day_7": {{
        "aqi_reduction_percent": 0.0,
        "respiratory_cases_reduction_percent": 0.0,
        "pm25_reduction_percent": 0.0,
        "construction_dust_reduction_percent": 0.0,
        "population_protected": "e.g., 12,000 residents in District 4",
        "narrative": "What the situation looks like on day 7"
      }},
      "projection_day_14": {{
        "aqi_reduction_percent": 0.0,
        "respiratory_cases_reduction_percent": 0.0,
        "pm25_reduction_percent": 0.0,
        "construction_dust_reduction_percent": 0.0,
        "population_protected": "...",
        "narrative": "What the situation looks like on day 14"
      }},
      "projection_day_30": {{
        "aqi_reduction_percent": 0.0,
        "respiratory_cases_reduction_percent": 0.0,
        "pm25_reduction_percent": 0.0,
        "construction_dust_reduction_percent": 0.0,
        "population_protected": "...",
        "narrative": "What the situation looks like on day 30"
      }},
      "trade_offs": [
        {{
          "benefit": "Specific benefit",
          "cost": "Specific cost or sacrifice",
          "affected_group": "Who is affected",
          "severity": "low|medium|high"
        }}
      ],
      "confidence_level": 0.0,
      "gemini_simulation_text": "2-3 sentence reasoning for scores and projections"
    }}
  ],
  "recommended_strategy_index": 0,
  "recommendation_reason": "Why this strategy is recommended over the others given the specific situation"
}}

Score ALL {len(strategies)} strategies. strategy_index is 0-based."""

    return prompt


def _parse_projection(raw: dict | None) -> ProjectedMetrics | None:
    """Parse a projection dictionary from Gemini response."""
    if not raw:
        return None
    try:
        return ProjectedMetrics(
            aqi_reduction_percent=_safe_float(raw.get("aqi_reduction_percent")),
            respiratory_cases_reduction_percent=_safe_float(
                raw.get("respiratory_cases_reduction_percent")
            ),
            pm25_reduction_percent=_safe_float(raw.get("pm25_reduction_percent")),
            construction_dust_reduction_percent=_safe_float(
                raw.get("construction_dust_reduction_percent")
            ),
            population_protected=raw.get("population_protected"),
            narrative=raw.get("narrative", ""),
        )
    except Exception:
        return None


def _safe_float(value: Any) -> float | None:
    """Safely convert to float."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_simulation_results(
    raw_text: str,
    strategies: list[InterventionStrategy],
    analysis_id: str,
) -> list[SimulationResult]:
    """
    Parse Gemini simulation response into SimulationResult instances.

    Handles:
    - JSON extraction from potential markdown wrapping
    - Truncated JSON responses (attempts repair)
    - Partial results (returns whatever was successfully parsed)
    """
    raw_text = raw_text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        parts = raw_text.split("```")
        if len(parts) >= 2:
            raw_text = parts[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()

    # Attempt to repair truncated JSON by finding the last complete simulation
    def attempt_repair(text: str) -> str:
        """
        Attempt to repair truncated JSON.

        Strategy: find the last complete simulation object by scanning
        backwards for a closing brace followed by array/object close.
        Truncated responses are closed manually.
        """
        # Find the last complete simulation entry
        # Look for the pattern that ends a simulation object
        last_complete = -1

        # Try to find the last '}' that closes a simulation entry
        depth = 0
        in_string = False
        escape_next = False
        sim_end_positions = []

        for i, ch in enumerate(text):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 1:
                    sim_end_positions.append(i)

        if not sim_end_positions:
            return text

        last_close = sim_end_positions[-1]
        repaired = text[:last_close + 1]

        repaired += (
            '\n  ],\n'
            '  "recommended_strategy_index": 0,\n'
            '  "recommendation_reason": "Based on available simulation data"\n'
            '}'
        )
        return repaired

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.warning(
            "Simulation JSON truncated (%d chars), attempting repair: %s",
            len(raw_text),
            exc,
        )
        repaired = attempt_repair(raw_text)
        try:
            data = json.loads(repaired)
            logger.info("JSON repair succeeded")
        except json.JSONDecodeError as exc2:
            logger.error("Simulation JSON repair failed: %s", exc2)
            return []

    simulations_raw = data.get("simulations", [])
    recommended_index = data.get("recommended_strategy_index", 0)
    recommendation_reason = data.get("recommendation_reason", "")

    results = []
    composite_scores = []

    for sim_raw in simulations_raw:
        strategy_index = int(sim_raw.get("strategy_index", 0))

        if strategy_index >= len(strategies):
            logger.warning("Strategy index %d out of range", strategy_index)
            continue

        strategy = strategies[strategy_index]

        raw_scores = sim_raw.get("scores", {})
        health_impact = float(raw_scores.get("health_impact", 50))
        cost_efficiency = float(raw_scores.get("cost_efficiency", 50))
        impl_speed = float(raw_scores.get("implementation_speed", 50))
        community = float(raw_scores.get("community_acceptance", 50))
        sustainability = float(raw_scores.get("sustainability", 50))

        composite = _compute_composite_score({
            "health_impact": health_impact,
            "cost_efficiency": cost_efficiency,
            "implementation_speed": impl_speed,
            "community_acceptance": community,
            "sustainability": sustainability,
        })

        scores = ScoreBreakdown(
            health_impact=round(health_impact, 1),
            cost_efficiency=round(cost_efficiency, 1),
            implementation_speed=round(impl_speed, 1),
            community_acceptance=round(community, 1),
            sustainability=round(sustainability, 1),
            composite_prism_score=composite,
        )

        composite_scores.append((strategy_index, composite))

        trade_offs = []
        for to_raw in sim_raw.get("trade_offs", []):
            try:
                trade_offs.append(
                    TradeOffItem(
                        benefit=to_raw.get("benefit", ""),
                        cost=to_raw.get("cost", ""),
                        affected_group=to_raw.get("affected_group", ""),
                        severity=to_raw.get("severity", "medium"),
                    )
                )
            except Exception:
                pass

        is_recommended = strategy_index == recommended_index

        result = SimulationResult(
            intervention_id=strategy.id or "",
            intervention_title=strategy.title,
            analysis_id=analysis_id,
            simulation_horizon_days=30,
            scores=scores,
            projection_day_7=_parse_projection(sim_raw.get("projection_day_7")),
            projection_day_14=_parse_projection(sim_raw.get("projection_day_14")),
            projection_day_30=_parse_projection(sim_raw.get("projection_day_30")),
            trade_offs=trade_offs,
            confidence_level=float(sim_raw.get("confidence_level", 0.7)),
            gemini_simulation_text=sim_raw.get("gemini_simulation_text", ""),
            is_recommended=is_recommended,
            recommendation_reason=recommendation_reason if is_recommended else "",
        )
        results.append(result)

    composite_scores.sort(key=lambda x: x[1], reverse=True)
    rank_map = {
        idx: rank + 1
        for rank, (idx, _) in enumerate(composite_scores)
    }

    for result in results:
        strategy_idx = next(
            (
                i for i, s in enumerate(strategies)
                if (s.id or "") == result.intervention_id
            ),
            None,
        )
        if strategy_idx is not None:
            result.rank_among_strategies = rank_map.get(strategy_idx, len(results))

    results.sort(key=lambda r: r.rank_among_strategies or 999)

    logger.info(
        "Parsed %d simulation results | recommended=%d",
        len(results),
        recommended_index,
    )

    return results


async def simulate_strategies(
    analysis: SituationAnalysis,
    strategies: list[InterventionStrategy],
) -> list[SimulationResult]:
    """
    Simulate outcomes for all intervention strategies simultaneously.

    Calls Gemini 2.5 Flash with all strategies in a single prompt
    to ensure relative scoring consistency.

    Args:
        analysis: The situation analysis providing context
        strategies: List of intervention strategies to simulate

    Returns:
        List of SimulationResult instances ordered by PRISM Score (highest first)
    """
    if not strategies:
        logger.warning("No strategies to simulate")
        return []

    logger.info(
        "Simulating %d strategies for analysis %s",
        len(strategies),
        analysis.id,
    )

    prompt = _build_simulation_prompt(analysis, strategies)
    logger.debug("Simulation prompt length: %d characters", len(prompt))

    try:
        model = get_gemini_model()
        config = get_generation_config(
            temperature=0.15,
            max_output_tokens=16384,
            response_mime_type="application/json",
        )

        response = model.generate_content(
            contents=prompt,
            generation_config=config,
        )

        raw_text = response.text
        logger.info(
            "Gemini simulation response: %d characters", len(raw_text)
        )

        results = _parse_simulation_results(
            raw_text,
            strategies,
            analysis.id or "",
        )

        return results

    except Exception as exc:
        logger.error("Simulation failed: %s", exc, exc_info=True)
        return []