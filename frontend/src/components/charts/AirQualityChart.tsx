/**
 * AirQualityChart component for PRISM.
 *
 * Displays AQI readings from ingested OpenAQ events
 * as a bar chart with WHO threshold reference line.
 */

"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { CommunityEvent, AirQualityMetrics } from "@/types/community";

interface AirQualityChartProps {
  events: CommunityEvent[];
}

interface ChartDataPoint {
  station: string;
  aqi: number;
  pm25: number;
}

function getBarColor(aqi: number): string {
  if (aqi <= 50) return "#10b981";
  if (aqi <= 100) return "#f59e0b";
  if (aqi <= 150) return "#f97316";
  if (aqi <= 200) return "#ef4444";
  return "#7c3aed";
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; name: string }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  const aqi = payload[0]?.value ?? 0;
  return (
    <div className="bg-white border border-border rounded-lg p-3 shadow-sm text-xs space-y-1">
      <p className="font-medium text-foreground truncate max-w-40">{label}</p>
      <p className="text-muted-foreground">
        AQI:{" "}
        <span className="font-semibold text-foreground">{aqi.toFixed(0)}</span>
      </p>
      <p
        className="text-[10px]"
        style={{ color: getBarColor(aqi) }}
      >
        {aqi <= 50
          ? "Good"
          : aqi <= 100
          ? "Moderate"
          : aqi <= 150
          ? "Unhealthy (Sensitive)"
          : aqi <= 200
          ? "Unhealthy"
          : "Very Unhealthy"}
      </p>
    </div>
  );
};

export function AirQualityChart({ events }: AirQualityChartProps) {
  const aqEvents = events.filter((e) => e.event_type === "air_quality");

  if (aqEvents.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center">
        <p className="text-xs text-muted-foreground">
          No air quality data available. Click Refresh Data to ingest.
        </p>
      </div>
    );
  }

  const data: ChartDataPoint[] = aqEvents
    .map((e) => {
      const m = e.metrics as AirQualityMetrics;
      return {
        station: e.location.district.split(" - ")[0].substring(0, 15),
        aqi: m.aqi ?? 0,
        pm25: m.pm25 ?? 0,
      };
    })
    .filter((d) => d.aqi > 0)
    .slice(0, 8);

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart
        data={data}
        margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
        barCategoryGap="30%"
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#e7e5e4"
          vertical={false}
        />
        <XAxis
          dataKey="station"
          tick={{ fontSize: 10, fill: "#78716c" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: "#78716c" }}
          axisLine={false}
          tickLine={false}
          domain={[0, "dataMax + 20"]}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f5f5f4" }} />
        <ReferenceLine
          y={100}
          stroke="#f59e0b"
          strokeDasharray="4 4"
          label={{
            value: "WHO",
            position: "right",
            fontSize: 9,
            fill: "#f59e0b",
          }}
        />
        <Bar dataKey="aqi" radius={[3, 3, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={index} fill={getBarColor(entry.aqi)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}