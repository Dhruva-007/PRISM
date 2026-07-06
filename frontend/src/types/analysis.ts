/**
 * Analysis type definitions for PRISM frontend.
 *
 * Mirrors the Pydantic models in backend/app/models/analysis.py.
 */

export type AnalysisStatus = "pending" | "analyzing" | "complete" | "failed";
export type UrgencyLevel = "routine" | "elevated" | "urgent" | "emergency";
export type SeverityLevel = "low" | "medium" | "high" | "critical";

export interface RootCause {
  cause: string;
  confidence: number;
  category: string;
  supporting_evidence: string[];
  affected_population?: string;
}

export interface DetectedPattern {
  pattern: string;
  strength: number;
  pattern_type: string;
  data_sources: string[];
}

export interface DataSummary {
  total_events: number;
  air_quality_events: number;
  weather_events: number;
  health_events: number;
  construction_events: number;
  time_window_hours: number;
  location: string;
  avg_aqi?: number;
  max_respiratory_cases?: number;
  dominant_severity?: string;
}

export interface SituationAnalysis {
  id?: string;
  created_at: string;
  status: AnalysisStatus;
  domain: string;
  time_window_hours: number;
  location: string;
  latitude: number;
  longitude: number;
  data_summary?: DataSummary;
  severity_level: SeverityLevel;
  urgency: UrgencyLevel;
  headline: string;
  summary: string;
  root_causes: RootCause[];
  patterns_detected: DetectedPattern[];
  key_findings: string[];
  population_at_risk: string;
  recommended_action_timeframe: string;
  gemini_reasoning: string;
  confidence_overall: number;
  error_message?: string;
}

export interface AnalysisResponse {
  analysis: SituationAnalysis;
}

export interface AnalysisListResponse {
  analyses: SituationAnalysis[];
  total: number;
}

export interface AnalysisRequest {
  location?: string;
  latitude?: number;
  longitude?: number;
  time_window_hours?: number;
}