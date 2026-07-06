/**
 * HealthTrendChart component for PRISM.
 *
 * Displays respiratory case counts per district
 * as a horizontal bar chart.
 */

"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { CommunityEvent, HealthMetrics } from "@/types/community";

interface HealthTrendChartProps {
  events: CommunityEvent[];
}

interface ChartDataPoint {
  district: string;
  cases: number;
  er: number;
  severity: string;
}

function getSeverityColor(cases: number): string {
  if (cases >= 150) return "#ef4444";
  if (cases >= 80) return "#f97316";
  if (cases >= 30) return "#f59e0b";
  return "#10b981";
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
  return (
    <div className="bg-white border border-border rounded-lg p-3 shadow-sm text-xs space-y-1">
      <p className="font-medium text-foreground truncate max-w-40">{label}</p>
      <p className="text-muted-foreground">
        Respiratory cases:{" "}
        <span className="font-semibold text-foreground">
          {payload[0]?.value}
        </span>
      </p>
      {payload[1] && (
        <p className="text-muted-foreground">
          ER visits:{" "}
          <span className="font-semibold text-foreground">
            {payload[1]?.value}
          </span>
        </p>
      )}
    </div>
  );
};

export function HealthTrendChart({ events }: HealthTrendChartProps) {
  const healthEvents = events.filter((e) => e.event_type === "health_report");

  if (healthEvents.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center">
        <p className="text-xs text-muted-foreground">
          No health data available. Click Refresh Data to ingest.
        </p>
      </div>
    );
  }

  const data: ChartDataPoint[] = healthEvents
    .map((e) => {
      const m = e.metrics as HealthMetrics;
      return {
        district: e.location.district.split(" - ")[0].substring(0, 12),
        cases: m.respiratory_cases ?? 0,
        er: m.er_visits ?? 0,
        severity: e.severity,
      };
    })
    .sort((a, b) => b.cases - a.cases)
    .slice(0, 6);

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
          dataKey="district"
          tick={{ fontSize: 10, fill: "#78716c" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: "#78716c" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f5f5f4" }} />
        <Bar dataKey="cases" radius={[3, 3, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={index} fill={getSeverityColor(entry.cases)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}