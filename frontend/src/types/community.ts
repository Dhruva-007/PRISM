/**
 * Community event type definitions for PRISM frontend.
 *
 * These mirror the Pydantic models in the backend.
 * Any changes to backend models must be reflected here.
 */

export type DataSource =
  | "openaq"
  | "noaa"
  | "open_meteo"
  | "osm"
  | "health"
  | "construction";

export type EventType =
  | "air_quality"
  | "weather"
  | "traffic"
  | "health_report"
  | "construction";

export type SeverityLevel = "low" | "medium" | "high" | "critical";

export interface GeoLocation {
  latitude: number;
  longitude: number;
  district: string;
  city: string;
}

export interface AirQualityMetrics {
  aqi?: number;
  pm25?: number;
  pm10?: number;
  no2?: number;
  o3?: number;
  co?: number;
  so2?: number;
  dominant_pollutant?: string;
}

export interface WeatherMetrics {
  temperature_celsius?: number;
  humidity_percent?: number;
  wind_speed_ms?: number;
  wind_direction_degrees?: number;
  precipitation_mm?: number;
  pressure_hpa?: number;
  visibility_km?: number;
  weather_condition?: string;
}

export interface HealthMetrics {
  respiratory_cases?: number;
  er_visits?: number;
  clinic_visits?: number;
  hospitalization_rate?: number;
  affected_age_group?: string;
  condition?: string;
}

export interface ConstructionMetrics {
  activity_type?: string;
  dust_risk?: SeverityLevel;
  proximity_to_schools_m?: number;
  proximity_to_hospitals_m?: number;
  estimated_duration_days?: number;
  affected_radius_m?: number;
}

export interface CommunityEvent {
  id?: string;
  source: DataSource;
  event_type: EventType;
  location: GeoLocation;
  timestamp: string;
  ingested_at: string;
  severity: SeverityLevel;
  metrics: AirQualityMetrics | WeatherMetrics | HealthMetrics | ConstructionMetrics;
  raw_source_id?: string;
  metadata?: Record<string, unknown>;
}

export interface CommunityEventListResponse {
  events: CommunityEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface IngestTriggerRequest {
  sources?: DataSource[];
  city_id?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
}

export interface IngestTriggerResponse {
  status: string;
  events_ingested: number;
  sources_attempted: string[];
  sources_succeeded: string[];
  sources_failed: string[];
  message: string;
}