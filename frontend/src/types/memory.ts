/**
 * Decision memory type definitions for PRISM frontend.
 *
 * Mirrors backend/app/models/memory.py.
 */

export type DecisionStatus =
  | "selected"
  | "in_progress"
  | "completed"
  | "abandoned";

export interface ActualOutcome {
  recorded_at: string;
  aqi_change_percent?: number;
  respiratory_cases_change_percent?: number;
  implementation_success?: boolean;
  obstacles_encountered: string[];
  actual_cost_level?: string;
  community_response?: string;
  notes: string;
}

export interface DecisionMemoryRecord {
  id?: string;
  created_at: string;
  updated_at: string;
  analysis_id: string;
  analysis_headline: string;
  analysis_severity: string;
  analysis_urgency: string;
  location: string;
  selected_strategy_id: string;
  selected_strategy_title: string;
  selected_strategy_type: string;
  prism_score_at_selection?: number;
  rank_at_selection?: number;
  selected_by_uid: string;
  selected_by_name: string;
  selection_reason: string;
  status: DecisionStatus;
  actual_outcome?: ActualOutcome;
  lessons_learned: string;
  domain: string;
}

export interface RecordDecisionRequest {
  analysis_id: string;
  selected_strategy_id: string;
  selection_reason: string;
}

export interface RecordOutcomeRequest {
  status: DecisionStatus;
  actual_outcome: ActualOutcome;
  lessons_learned: string;
}

export interface DecisionMemoryListResponse {
  records: DecisionMemoryRecord[];
  total: number;
}

export interface DecisionMemoryResponse {
  record: DecisionMemoryRecord;
}