"""
Intervention strategy generator for PRISM.

Takes a completed SituationAnalysis and generates multiple distinct,
actionable intervention strategies using Gemini 2.5 Flash.

Prompt engineering principles:
1. Force strategy diversity — immediate vs short-term vs long-term
2. Ground every action in the specific root causes identified
3. Require concrete, measurable success metrics
4. Require realistic responsible parties (not "the government")
5. Explicitly prohibit generic or vague recommendations
6. Require trade-off acknowledgment for every strategy
"""

import json

from app.integrations.vertex_ai import get_gemini_model, get_generation_config
from app.models.analysis import SituationAnalysis
from app.models.intervention import (
    CostLevel,
    ExpectedOutcome,
    InterventionAction,
    InterventionStrategy,
    StrategyType,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _build_intervention_prompt(
    analysis: SituationAnalysis,
    num_strategies: int,
) -> str:
    """
    Build the Gemini intervention generation prompt.

    Constructs a detailed prompt that includes the complete analysis
    findings and instructs Gemini to generate diverse, realistic,
    evidence-based intervention strategies.
    """
    root_causes_text = "\n".join([
        f"  {i+1}. [{rc.category.upper()}] {rc.cause} "
        f"(confidence: {rc.confidence:.0%}, affects: {rc.affected_population or 'general population'})"
        for i, rc in enumerate(analysis.root_causes)
    ])

    patterns_text = "\n".join([
        f"  - {p.pattern} (strength: {p.strength:.0%})"
        for p in analysis.patterns_detected
    ])

    key_findings_text = "\n".join([
        f"  {i+1}. {f}" for i, f in enumerate(analysis.key_findings)
    ])

    data_context = ""
    if analysis.data_summary:
        ds = analysis.data_summary
        data_context = f"""
DATA CONTEXT:
- Total events analyzed: {ds.total_events}
- Air quality readings: {ds.air_quality_events} stations
- Health reports: {ds.health_events} districts  
- Construction sites: {ds.construction_events} active
- Average AQI: {ds.avg_aqi or 'Not available'}
- Max respiratory cases in single district: {ds.max_respiratory_cases or 'Not available'}"""

    prompt = f"""You are PRISM, an expert Decision Intelligence System advising a municipal government on community health interventions.

SITUATION ANALYSIS SUMMARY:
Location: {analysis.location}
Severity: {analysis.severity_level.upper()}
Urgency: {analysis.urgency.upper()}
Overall Assessment: {analysis.headline}

{data_context}

ROOT CAUSES IDENTIFIED:
{root_causes_text if root_causes_text else "  No specific root causes identified — use general assessment"}

KEY PATTERNS:
{patterns_text if patterns_text else "  No specific patterns detected"}

KEY FINDINGS:
{key_findings_text if key_findings_text else "  See overall assessment"}

SITUATION SUMMARY:
{analysis.summary[:800]}

POPULATION AT RISK: {analysis.population_at_risk}
ACTION TIMEFRAME: {analysis.recommended_action_timeframe}

YOUR TASK:
Generate exactly {num_strategies} intervention strategies that directly address the root causes and patterns identified above.

CRITICAL REQUIREMENTS:
1. Strategies MUST be genuinely different from each other:
   - Strategy 1: IMMEDIATE (0-7 days) — fastest possible action, minimal process
   - Strategy 2: SHORT_TERM (1-4 weeks) — moderate complexity, higher impact
   - Strategy 3: LONG_TERM (1-6 months) — comprehensive solution, sustained impact
   {f"- Strategy 4: Wildcard — most creative evidence-based approach" if num_strategies == 4 else ""}

2. Each action must have:
   - A SPECIFIC responsible party (e.g., "City Traffic Management Department", not "authorities")
   - A SPECIFIC success metric that can be measured (e.g., "PM2.5 reduced below 15 µg/m³")
   - A realistic timeline in days

3. Expected outcomes must reference SPECIFIC metrics from the data:
   - Use actual numbers from the analysis (respiratory cases, AQI values, etc.)
   - Be conservative — do not over-promise

4. Trade-offs must be honest — acknowledge what is sacrificed

5. NEVER generate generic strategies like "raise awareness" or "consult stakeholders"
   Every action must be operationally specific.

Respond with ONLY valid JSON in this exact format:

{{
  "strategies": [
    {{
      "title": "Strategy title (max 60 chars)",
      "description": "2-3 sentence description of the overall strategy approach",
      "strategy_type": "immediate|short_term|long_term",
      "target_root_causes": ["Root cause 1 addressed", "Root cause 2 addressed"],
      "implementation_complexity": "Low|Medium|High|Very High",
      "total_estimated_cost": "low|medium|high|very_high",
      "required_authorities": ["Department 1", "Department 2"],
      "prerequisites": ["Prerequisite 1 if any"],
      "primary_beneficiaries": "Who benefits most and estimated numbers",
      "estimated_population_impacted": "e.g., 45,000 residents in Districts 3 and 4",
      "risks": ["Risk 1", "Risk 2"],
      "trade_offs": ["Trade-off 1", "Trade-off 2"],
      "gemini_rationale": "Why this specific strategy addresses the root causes, what evidence supports it, and how it differs from the other strategies",
      "actions": [
        {{
          "action_id": "A1",
          "title": "Specific action title",
          "description": "Detailed description of exactly what must be done",
          "responsible_party": "Specific department or role",
          "timeline_days": 2,
          "estimated_cost": "low|medium|high|very_high",
          "dependencies": [],
          "success_metric": "Specific measurable outcome"
        }}
      ],
      "expected_outcomes": [
        {{
          "metric": "PM2.5 concentration",
          "baseline_value": "Current measured value",
          "expected_value": "Expected value after intervention",
          "timeframe": "e.g., Within 48 hours",
          "confidence": 0.75
        }}
      ]
    }}
  ]
}}

Generate {num_strategies} strategies. Each strategy must have 2-4 actions and 2-3 expected outcomes.
Make strategies genuinely different — different mechanisms, different timescales, different trade-offs."""

    return prompt


def _parse_strategy(
    raw: dict,
    analysis_id: str,
    index: int,
) -> InterventionStrategy | None:
    """
    Parse a single strategy dictionary from Gemini response.

    Returns None if the strategy cannot be parsed — the caller
    skips invalid strategies rather than failing entirely.
    """
    try:
        strategy_type_raw = raw.get("strategy_type", "immediate")
        try:
            strategy_type = StrategyType(strategy_type_raw)
        except ValueError:
            strategy_type = StrategyType.IMMEDIATE

        cost_raw = raw.get("total_estimated_cost", "medium")
        try:
            total_cost = CostLevel(cost_raw)
        except ValueError:
            total_cost = CostLevel.MEDIUM

        actions = []
        for i, a in enumerate(raw.get("actions", [])):
            action_cost_raw = a.get("estimated_cost", "medium")
            try:
                action_cost = CostLevel(action_cost_raw)
            except ValueError:
                action_cost = CostLevel.MEDIUM

            actions.append(
                InterventionAction(
                    action_id=a.get("action_id", f"A{i+1}"),
                    title=a.get("title", "Action"),
                    description=a.get("description", ""),
                    responsible_party=a.get("responsible_party", "Municipal Authority"),
                    timeline_days=int(a.get("timeline_days", 7)),
                    estimated_cost=action_cost,
                    dependencies=a.get("dependencies", []),
                    success_metric=a.get("success_metric", "To be defined"),
                )
            )

        outcomes = []
        for o in raw.get("expected_outcomes", []):
            outcomes.append(
                ExpectedOutcome(
                    metric=o.get("metric", "Health outcome"),
                    baseline_value=o.get("baseline_value", "Current"),
                    expected_value=o.get("expected_value", "Improved"),
                    timeframe=o.get("timeframe", "Within 30 days"),
                    confidence=float(o.get("confidence", 0.6)),
                )
            )

        return InterventionStrategy(
            analysis_id=analysis_id,
            title=raw.get("title", f"Intervention Strategy {index + 1}"),
            description=raw.get("description", ""),
            strategy_type=strategy_type,
            target_root_causes=raw.get("target_root_causes", []),
            actions=actions,
            total_estimated_cost=total_cost,
            implementation_complexity=raw.get("implementation_complexity", "Medium"),
            required_authorities=raw.get("required_authorities", []),
            prerequisites=raw.get("prerequisites", []),
            expected_outcomes=outcomes,
            primary_beneficiaries=raw.get("primary_beneficiaries", "General population"),
            estimated_population_impacted=raw.get(
                "estimated_population_impacted", "To be determined"
            ),
            risks=raw.get("risks", []),
            trade_offs=raw.get("trade_offs", []),
            gemini_rationale=raw.get("gemini_rationale", ""),
        )

    except Exception as exc:
        logger.warning("Failed to parse strategy %d: %s", index, exc)
        return None


async def generate_interventions(
    analysis: SituationAnalysis,
    num_strategies: int = 3,
) -> list[InterventionStrategy]:
    """
    Generate intervention strategies for a situation analysis.

    Calls Gemini 2.5 Flash with a structured prompt containing
    the complete analysis findings, and parses the response into
    validated InterventionStrategy instances.

    Args:
        analysis: Complete SituationAnalysis from Phase 5
        num_strategies: Number of distinct strategies to generate (2-4)

    Returns:
        List of InterventionStrategy instances.
        Returns empty list only if Gemini fails completely.
    """
    logger.info(
        "Generating %d intervention strategies for analysis %s",
        num_strategies,
        analysis.id,
    )

    prompt = _build_intervention_prompt(analysis, num_strategies)
    logger.debug("Intervention prompt length: %d characters", len(prompt))

    try:
        model = get_gemini_model()
        config = get_generation_config(
            temperature=0.3,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )

        response = model.generate_content(
            contents=prompt,
            generation_config=config,
        )

        raw_text = response.text
        logger.info(
            "Gemini intervention response: %d characters", len(raw_text)
        )

        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            parts = raw_text.split("```")
            if len(parts) >= 2:
                raw_text = parts[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]

        data = json.loads(raw_text)
        raw_strategies = data.get("strategies", [])

        if not raw_strategies:
            logger.error("Gemini returned no strategies")
            return []

        strategies = []
        for i, raw in enumerate(raw_strategies[:num_strategies]):
            strategy = _parse_strategy(raw, analysis.id or "", i)
            if strategy is not None:
                strategies.append(strategy)

        logger.info(
            "Generated %d valid intervention strategies", len(strategies)
        )
        return strategies

    except json.JSONDecodeError as exc:
        logger.error("Gemini returned invalid JSON for interventions: %s", exc)
        return []
    except Exception as exc:
        logger.error("Intervention generation failed: %s", exc, exc_info=True)
        return []