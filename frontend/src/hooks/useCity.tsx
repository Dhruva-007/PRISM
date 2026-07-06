/**
 * useCity hook for PRISM.
 *
 * Manages the currently selected city across the entire application.
 * Stores selection in localStorage for persistence between sessions.
 */

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type JSX,
  type ReactNode,
} from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { CityInfo, CitiesResponse } from "@/types/city";

interface CityContextValue {
  cities: CityInfo[];
  selectedCity: CityInfo | null;
  selectCity: (cityId: string) => void;
  isLoading: boolean;
}

const CityContext = createContext<CityContextValue | undefined>(undefined);

const STORAGE_KEY = "prism_selected_city";
const DEFAULT_CITY_ID = "hyderabad";

const FALLBACK_CITIES: CityInfo[] = [
  {
    city_id: "hyderabad",
    display_name: "Hyderabad",
    state: "Telangana",
    country: "India",
    latitude: 17.385,
    longitude: 78.4867,
    map_zoom: 12,
    district_count: 7,
    construction_sites: 5,
  },
  {
    city_id: "delhi",
    display_name: "Delhi",
    state: "NCT",
    country: "India",
    latitude: 28.6139,
    longitude: 77.209,
    map_zoom: 11,
    district_count: 8,
    construction_sites: 4,
  },
  {
    city_id: "bangalore",
    display_name: "Bangalore",
    state: "Karnataka",
    country: "India",
    latitude: 12.9716,
    longitude: 77.5946,
    map_zoom: 12,
    district_count: 7,
    construction_sites: 4,
  },
  {
    city_id: "mumbai",
    display_name: "Mumbai",
    state: "Maharashtra",
    country: "India",
    latitude: 19.076,
    longitude: 72.8777,
    map_zoom: 12,
    district_count: 7,
    construction_sites: 4,
  },
];

interface CityProviderProps {
  children: ReactNode;
}

export function CityProvider({ children }: CityProviderProps): JSX.Element {
  const [selectedCityId, setSelectedCityId] = useState<string>(DEFAULT_CITY_ID);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setSelectedCityId(stored);
      }
    } catch {
      // localStorage unavailable in SSR or private browsing
    }
  }, []);

  const { data, isLoading } = useQuery<CitiesResponse>({
    queryKey: ["cities"],
    queryFn: () => apiClient.get<CitiesResponse>("/cities"),
    staleTime: Infinity,
    retry: 1,
  });

  const cities =
    data?.cities && data.cities.length > 0 ? data.cities : FALLBACK_CITIES;

  const selectedCity =
    cities.find((c) => c.city_id === selectedCityId) ?? cities[0];

  const selectCity = useCallback((cityId: string) => {
    setSelectedCityId(cityId);
    try {
      localStorage.setItem(STORAGE_KEY, cityId);
    } catch {
      // localStorage unavailable
    }
  }, []);

  return (
    <CityContext.Provider value={{ cities, selectedCity, selectCity, isLoading }}>
      {children}
    </CityContext.Provider>
  );
}

export function useCity(): CityContextValue {
  const context = useContext(CityContext);
  if (context === undefined) {
    throw new Error("useCity must be used within a CityProvider");
  }
  return context;
}