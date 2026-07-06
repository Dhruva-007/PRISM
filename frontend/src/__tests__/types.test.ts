/**
 * Tests for PRISM TypeScript type definitions.
 *
 * These tests verify that our type structures match what the backend returns.
 * They catch regressions when backend API contracts change.
 */

import type { CommunityEvent, IngestTriggerRequest } from "@/types/community";
import type { SituationAnalysis } from "@/types/analysis";
import type { SimulationResult } from "@/types/simulation";
import type { CityInfo } from "@/types/city";

describe("CommunityEvent type structure", () => {
  test("valid air quality event satisfies type", () => {
    const event: CommunityEvent = {
      id: "test-001",
      source: "openaq",
      event_type: "air_quality",
      location: {
        latitude: 17.385,
        longitude: 78.4867,
        district: "Secunderabad",
        city: "Hyderabad",
      },
      timestamp: "2025-01-15T10:00:00Z",
      ingested_at: "2025-01-15T10:01:00Z",
      severity: "high",
      metrics: {
        aqi: 142,
        pm25: 38.5,
        pm10: 72.3,
        dominant_pollutant: "PM2.5",
      },
    };
    expect(event.source).toBe("openaq");
    expect(event.event_type).toBe("air_quality");
    expect(event.severity).toBe("high");
  });

  test("valid health event satisfies type", () => {
    const event: CommunityEvent = {
      source: "health",
      event_type: "health_report",
      location: {
        latitude: 17.365,
        longitude: 78.4967,
        district: "Old City",
        city: "Hyderabad",
      },
      timestamp: "2025-01-15T08:00:00Z",
      ingested_at: "2025-01-15T08:01:00Z",
      severity: "critical",
      metrics: {
        respiratory_cases: 183,
        er_visits: 27,
        clinic_visits: 100,
      },
    };
    expect(event.severity).toBe("critical");
  });
});

describe("IngestTriggerRequest type", () => {
  test("accepts city_id field", () => {
    const request: IngestTriggerRequest = {
      city_id: "hyderabad",
      city: "Hyderabad, Telangana",
      latitude: 17.385,
      longitude: 78.4867,
    };
    expect(request.city_id).toBe("hyderabad");
  });

  test("city_id is optional", () => {
    const request: IngestTriggerRequest = {};
    expect(request.city_id).toBeUndefined();
  });
});

describe("SituationAnalysis type structure", () => {
  test("valid analysis satisfies type", () => {
    const analysis: SituationAnalysis = {
      id: "analysis-001",
      created_at: "2025-01-15T10:00:00Z",
      status: "complete",
      domain: "health_environment",
      time_window_hours: 24,
      location: "Hyderabad, Telangana",
      latitude: 17.385,
      longitude: 78.4867,
      severity_level: "high",
      urgency: "urgent",
      headline: "Critical respiratory risk detected",
      summary: "Elevated PM2.5 and construction dust.",
      root_causes: [
        {
          cause: "Metro construction dust",
          confidence: 0.87,
          category: "infrastructure",
          supporting_evidence: ["PM2.5 at 38.5 µg/m³"],
        },
      ],
      patterns_detected: [],
      key_findings: ["PM2.5 exceeds WHO limit"],
      population_at_risk: "Children and elderly",
      recommended_action_timeframe: "24-48 hours",
      gemini_reasoning: "Analysis complete.",
      confidence_overall: 0.78,
    };
    expect(analysis.severity_level).toBe("high");
    expect(analysis.urgency).toBe("urgent");
    expect(analysis.root_causes).toHaveLength(1);
  });
});

describe("CityInfo type structure", () => {
  test("valid city info satisfies type", () => {
    const city: CityInfo = {
      city_id: "hyderabad",
      display_name: "Hyderabad",
      state: "Telangana",
      country: "India",
      latitude: 17.385,
      longitude: 78.4867,
      map_zoom: 12,
      district_count: 7,
      construction_sites: 5,
    };
    expect(city.city_id).toBe("hyderabad");
    expect(city.district_count).toBe(7);
  });
});

describe("SimulationResult type structure", () => {
  test("valid simulation result satisfies type", () => {
    const result: SimulationResult = {
      intervention_id: "strategy-001",
      intervention_title: "Emergency Dust Suppression",
      analysis_id: "analysis-001",
      simulated_at: "2025-01-15T12:00:00Z",
      simulation_horizon_days: 30,
      scores: {
        health_impact: 88,
        cost_efficiency: 91,
        implementation_speed: 95,
        community_acceptance: 72,
        sustainability: 45,
        composite_prism_score: 79.2,
      },
      trade_offs: [],
      confidence_level: 0.78,
      gemini_simulation_text: "High speed strategy.",
      is_recommended: true,
      recommendation_reason: "Best PRISM Score",
    };
    expect(result.scores.composite_prism_score).toBe(79.2);
    expect(result.is_recommended).toBe(true);
  });
});