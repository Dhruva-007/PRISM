/**
 * CommunityMap component for PRISM.
 *
 * Displays community events on an interactive MapLibre GL map.
 * Shows air quality, health, and construction event locations
 * with color-coded severity markers.
 *
 * Uses OpenStreetMap tiles — completely free, no API key required.
 */

"use client";

import { useEffect, useRef, useState } from "react";
import type { CommunityEvent } from "@/types/community";

interface CommunityMapProps {
  events: CommunityEvent[];
  height?: number;
}

const SEVERITY_COLORS: Record<string, string> = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  air_quality: "Air Quality",
  weather: "Weather",
  health_report: "Health",
  construction: "Construction",
  traffic: "Traffic",
};

export function CommunityMap({ events, height = 280 }: CommunityMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState(false);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    let map: {
      on: (event: string, callback: () => void) => void;
      addControl: (control: unknown, position?: string) => void;
      addSource: (id: string, source: unknown) => void;
      addLayer: (layer: unknown) => void;
      getSource: (id: string) => unknown;
      remove: () => void;
    } | null = null;

    import("maplibre-gl")
      .then((maplibre) => {
        if (!mapContainerRef.current) return;

        const defaultCenter = events.find(
          (e) => e.location.latitude && e.location.longitude
        );
        const centerLon = defaultCenter?.location.longitude ?? 78.4867;
        const centerLat = defaultCenter?.location.latitude ?? 17.3850;

        map = new maplibre.Map({
          container: mapContainerRef.current,
          style: {
            version: 8,
            sources: {
              osm: {
                type: "raster",
                tiles: [
                  "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                ],
                tileSize: 256,
                attribution:
                  '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
              },
            },
            layers: [
              {
                id: "osm-tiles",
                type: "raster",
                source: "osm",
              },
            ],
          },
          center: [centerLon, centerLat],
          zoom: 12,
        }) as typeof map;

        mapRef.current = map;

        map!.on("load", () => {
          setMapLoaded(true);

          const geojsonFeatures = events
            .filter(
              (e) =>
                e.location.latitude !== 0 && e.location.longitude !== 0
            )
            .map((e) => ({
              type: "Feature" as const,
              geometry: {
                type: "Point" as const,
                coordinates: [e.location.longitude, e.location.latitude],
              },
              properties: {
                severity: e.severity,
                event_type: e.event_type,
                district: e.location.district,
                color: SEVERITY_COLORS[e.severity] ?? "#78716c",
                label: EVENT_TYPE_LABELS[e.event_type] ?? e.event_type,
              },
            }));

          map!.addSource("events", {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: geojsonFeatures,
            },
          });

          map!.addLayer({
            id: "events-circle",
            type: "circle",
            source: "events",
            paint: {
              "circle-radius": [
                "match",
                ["get", "severity"],
                "critical", 14,
                "high", 11,
                "medium", 8,
                6,
              ],
              "circle-color": ["get", "color"],
              "circle-opacity": 0.85,
              "circle-stroke-width": 2,
              "circle-stroke-color": "#ffffff",
            },
          });
        });
      })
      .catch(() => {
        setMapError(true);
      });

    return () => {
      if (map) {
        map.remove();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;

    const map = mapRef.current as {
      getSource: (id: string) => { setData: (data: unknown) => void } | undefined;
    };

    const source = map.getSource("events");
    if (!source) return;

    const geojsonFeatures = events
      .filter(
        (e) => e.location.latitude !== 0 && e.location.longitude !== 0
      )
      .map((e) => ({
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: [e.location.longitude, e.location.latitude],
        },
        properties: {
          severity: e.severity,
          event_type: e.event_type,
          district: e.location.district,
          color: SEVERITY_COLORS[e.severity] ?? "#78716c",
          label: EVENT_TYPE_LABELS[e.event_type] ?? e.event_type,
        },
      }));

    source.setData({
      type: "FeatureCollection",
      features: geojsonFeatures,
    });
  }, [events, mapLoaded]);

  if (mapError) {
    return (
      <div
        style={{ height }}
        className="rounded-lg bg-stone-100 border border-border flex items-center justify-center"
      >
        <p className="text-xs text-muted-foreground">
          Map unavailable — network error
        </p>
      </div>
    );
  }

  return (
    <div className="relative rounded-lg overflow-hidden border border-border">
      <div ref={mapContainerRef} style={{ height, width: "100%" }} />

      {/* Legend */}
      <div className="absolute bottom-2 left-2 bg-white/95 backdrop-blur-sm rounded-md border border-border p-2 space-y-1">
        {Object.entries(SEVERITY_COLORS).map(([level, color]) => (
          <div key={level} className="flex items-center gap-1.5">
            <div
              className="w-2.5 h-2.5 rounded-full border border-white shadow-sm"
              style={{ backgroundColor: color }}
            />
            <span className="text-[10px] text-foreground capitalize">
              {level}
            </span>
          </div>
        ))}
      </div>

      {!mapLoaded && (
        <div className="absolute inset-0 bg-stone-50 flex items-center justify-center">
          <p className="text-xs text-muted-foreground">Loading map...</p>
        </div>
      )}
    </div>
  );
}