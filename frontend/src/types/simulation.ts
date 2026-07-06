/**
 * Simulation type definitions for PRISM frontend.
 *
 * Mirrors backend/app/models/simulation.py.
 */

export interface ScoreBreakdown {
  health_impact: number;
  cost_efficiency: number;
  implementation_speed: number;
  community_acceptance: number;
  sustainability: number;
  composite_prism_score: number;
}

export interface ProjectedMetrics {
  aqi_reduction_percent?: number;
  respiratory_cases_reduction_percent?: number;
  pm25_reduction_percent?: number;
  construction_dust_reduction_percent?: number;
  population_protected?: string;
  narrative: string;
}

export interface TradeOffItem {
  benefit: string;
  cost: string;
  affected_group: string;
  severity: "low" | "medium" | "high";
}

export interface SimulationResult {
  id?: string;
  intervention_id: string;
  intervention_title: string;
  analysis_id: string;
  simulated_at: string;
  simulation_horizon_days: number;
  scores: ScoreBreakdown;
  projection_day_7?: ProjectedMetrics;
  projection_day_14?: ProjectedMetrics;
  projection_day_30?: ProjectedMetrics;
  trade_offs: TradeOffItem[];
  rank_among_strategies?: number;
  confidence_level: number;
  gemini_simulation_text: string;
  is_recommended: boolean;
  recommendation_reason: string;
}

export interface SimulationListResponse {
  results: SimulationResult[];
  analysis_id: string;
  total: number;
  recommended_intervention_id?: string;
}

export interface RunSimulationRequest {
  analysis_id: string;
  intervention_ids?: string[];
}