/**
 * ScoreComparisonChart component for PRISM.
 *
 * Radar/bar chart comparing intervention strategies
 * across all 5 PRISM Score dimensions.
 */

"use client";

import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import type { SimulationResult } from "@/types/simulation";

interface ScoreComparisonChartProps {
  results: SimulationResult[];
}

const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444"];

const DIMENSION_LABELS = {
  health_impact: "Health",
  cost_efficiency: "Cost",
  implementation_speed: "Speed",
  community_acceptance: "Acceptance",
  sustainability: "Sustainability",
};

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-border rounded-lg p-3 shadow-sm text-xs space-y-1">
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground truncate max-w-32">
            {entry.name}:
          </span>
          <span className="font-semibold text-foreground">{entry.value}</span>
        </div>
      ))}
    </div>
  );
};

export function ScoreComparisonChart({ results }: ScoreComparisonChartProps) {
  if (results.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center">
        <p className="text-xs text-muted-foreground">
          Run simulation to see strategy comparison.
        </p>
      </div>
    );
  }

  const dimensions = Object.keys(DIMENSION_LABELS) as Array<
    keyof typeof DIMENSION_LABELS
  >;

  const data = dimensions.map((dim) => {
    const entry: Record<string, string | number> = {
      dimension: DIMENSION_LABELS[dim],
    };
    results.slice(0, 3).forEach((result, i) => {
      entry[`strategy${i}`] = result.scores[dim];
    });
    return entry;
  });

  return (
    <ResponsiveContainer width="100%" height={200}>
      <RadarChart data={data} margin={{ top: 8, right: 24, left: 24, bottom: 8 }}>
        <PolarGrid stroke="#e7e5e4" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fontSize: 10, fill: "#78716c" }}
        />
        <Tooltip content={<CustomTooltip />} />
        {results.slice(0, 3).map((result, i) => (
          <Radar
            key={result.id}
            name={result.intervention_title.substring(0, 20)}
            dataKey={`strategy${i}`}
            stroke={COLORS[i]}
            fill={COLORS[i]}
            fillOpacity={0.08}
            strokeWidth={2}
          />
        ))}
        <Legend
          wrapperStyle={{ fontSize: "10px", paddingTop: "8px" }}
          formatter={(value) =>
            value.length > 22 ? value.substring(0, 22) + "…" : value
          }
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}