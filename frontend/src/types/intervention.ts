/**
 * Intervention strategy type definitions for PRISM frontend.
 *
 * Mirrors backend/app/models/intervention.py.
 */

export type StrategyType = "immediate" | "short_term" | "long_term";
export type CostLevel = "low" | "medium" | "high" | "very_high";

export interface InterventionAction {
  action_id: string;
  title: string;
  description: string;
  responsible_party: string;
  timeline_days: number;
  estimated_cost: CostLevel;
  dependencies: string[];
  success_metric: string;
}

export interface ExpectedOutcome {
  metric: string;
  baseline_value: string;
  expected_value: string;
  timeframe: string;
  confidence: number;
}

export interface InterventionStrategy {
  id?: string;
  analysis_id: string;
  created_at: string;
  title: string;
  description: string;
  strategy_type: StrategyType;
  target_root_causes: string[];
  actions: InterventionAction[];
  total_estimated_cost: CostLevel;
  implementation_complexity: string;
  required_authorities: string[];
  prerequisites: string[];
  expected_outcomes: ExpectedOutcome[];
  primary_beneficiaries: string;
  estimated_population_impacted: string;
  risks: string[];
  trade_offs: string[];
  prism_score?: number;
  rank?: number;
  gemini_rationale: string;
}

export interface InterventionListResponse {
  strategies: InterventionStrategy[];
  analysis_id: string;
  total: number;
}

export interface GenerateInterventionsRequest {
  analysis_id: string;
  num_strategies?: number;
}