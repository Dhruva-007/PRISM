/**
 * City type definitions for PRISM frontend.
 */

export interface CityInfo {
  city_id: string;
  display_name: string;
  state: string;
  country: string;
  latitude: number;
  longitude: number;
  map_zoom: number;
  district_count: number;
  construction_sites: number;
}

export interface CitiesResponse {
  cities: CityInfo[];
}