/**
 * Simulation page for PRISM dashboard.
 *
 * Displays scenario simulation results comparing all intervention
 * strategies across 5 dimensions with PRISM Score ranking.
 */

"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FlaskConical,
  Trophy,
  ChevronDown,
  ChevronUp,
  TrendingDown,
  ArrowRight,
  Loader2,
  AlertTriangle,
  CheckCircle,
  Info,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { useSimulation } from "@/hooks/useSimulation";
import { useAnalysisList } from "@/hooks/useAnalysis";
import type { SimulationResult, TradeOffItem } from "@/types/simulation";
import { cn } from "@/lib/utils";

const SCORE_DIMENSIONS = [
  {
    key: "health_impact" as const,
    label: "Health Impact",
    weight: "35%",
    description: "Reduction in health burden",
  },
  {
    key: "cost_efficiency" as const,
    label: "Cost Efficiency",
    weight: "20%",
    description: "Impact per resource spent",
  },
  {
    key: "implementation_speed" as const,
    label: "Speed",
    weight: "20%",
    description: "Time to deployment",
  },
  {
    key: "community_acceptance" as const,
    label: "Acceptance",
    weight: "15%",
    description: "Community and political support",
  },
  {
    key: "sustainability" as const,
    label: "Sustainability",
    weight: "10%",
    description: "Durability of improvement",
  },
] as const;

function scoreColor(score: number): string {
  if (score >= 75) return "text-emerald-600";
  if (score >= 55) return "text-blue-600";
  if (score >= 35) return "text-amber-600";
  return "text-red-600";
}

function scoreBarColor(score: number): string {
  if (score >= 75) return "bg-emerald-500";
  if (score >= 55) return "bg-blue-500";
  if (score >= 35) return "bg-amber-500";
  return "bg-red-500";
}

function PRISMScoreRing({ score }: { score: number }) {
  const color =
    score >= 75
      ? "text-emerald-600"
      : score >= 55
      ? "text-blue-600"
      : score >= 35
      ? "text-amber-600"
      : "text-red-600";

  return (
    <div className="flex flex-col items-center">
      <div
        className={cn(
          "w-16 h-16 rounded-full border-4 flex items-center justify-center",
          score >= 75
            ? "border-emerald-200"
            : score >= 55
            ? "border-blue-200"
            : score >= 35
            ? "border-amber-200"
            : "border-red-200"
        )}
      >
        <span className={cn("text-xl font-bold", color)}>
          {Math.round(score)}
        </span>
      </div>
      <span className="text-[10px] text-muted-foreground mt-1">PRISM Score</span>
    </div>
  );
}

function ProjectionRow({
  label,
  value,
}: {
  label: string;
  value: number | undefined | null;
}) {
  if (value === null || value === undefined) return null;
  return (
    <div className="flex items-center justify-between">
      <span className="text-[10px] text-muted-foreground">{label}</span>
      <span className="text-[10px] font-semibold text-emerald-700">
        ↓ {value.toFixed(1)}%
      </span>
    </div>
  );
}

function TradeOffRow({ item }: { item: TradeOffItem }) {
  const severityColor =
    item.severity === "high"
      ? "border-red-300 bg-red-50"
      : item.severity === "medium"
      ? "border-amber-300 bg-amber-50"
      : "border-stone-200 bg-stone-50";

  return (
    <div className={cn("p-2.5 rounded-lg border space-y-1", severityColor)}>
      <div className="flex items-start gap-2">
        <CheckCircle className="w-3 h-3 text-emerald-600 flex-shrink-0 mt-0.5" />
        <p className="text-[10px] text-foreground leading-relaxed">{item.benefit}</p>
      </div>
      <div className="flex items-start gap-2">
        <AlertTriangle className="w-3 h-3 text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          {item.cost} — {item.affected_group}
        </p>
      </div>
    </div>
  );
}

function SimulationCard({
  result,
  index,
}: {
  result: SimulationResult;
  index: number;
}) {
  const [expanded, setExpanded] = useState(index === 0);

  return (
    <Card
      className={cn(
        "border shadow-none transition-shadow duration-200 hover:shadow-sm",
        result.is_recommended
          ? "border-accent/30 bg-accent/[0.02]"
          : "border-border"
      )}
    >
      <CardHeader className="pb-3 pt-4 px-5">
        <div className="flex items-start gap-4">
          <PRISMScoreRing score={result.scores.composite_prism_score} />

          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              {result.rank_among_strategies === 1 && (
                <span className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                  <Trophy className="w-3 h-3" />
                  Top Ranked
                </span>
              )}
              {result.is_recommended && (
                <span className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-semibold bg-accent/10 text-accent border border-accent/20">
                  <CheckCircle className="w-3 h-3" />
                  Recommended
                </span>
              )}
              <span className="text-[10px] text-muted-foreground">
                Rank #{result.rank_among_strategies} of {result.rank_among_strategies ? "all strategies" : "—"}
              </span>
              <span className="text-[10px] text-muted-foreground">
                Confidence: {Math.round(result.confidence_level * 100)}%
              </span>
            </div>

            <CardTitle className="text-sm font-semibold text-foreground leading-snug">
              {result.intervention_title}
            </CardTitle>

            {result.is_recommended && result.recommendation_reason && (
              <p className="text-[10px] text-accent leading-relaxed">
                {result.recommendation_reason}
              </p>
            )}

            {/* Score bar mini-summary */}
            <div className="grid grid-cols-5 gap-1">
              {SCORE_DIMENSIONS.map((dim) => {
                const score = result.scores[dim.key];
                return (
                  <div key={dim.key} className="space-y-0.5">
                    <div className="text-[9px] text-muted-foreground truncate">
                      {dim.label}
                    </div>
                    <div className="h-1 rounded-full bg-stone-100 overflow-hidden">
                      <div
                        className={cn("h-full rounded-full", scoreBarColor(score))}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                    <div className={cn("text-[9px] font-semibold", scoreColor(score))}>
                      {Math.round(score)}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="h-8 w-8 p-0 flex-shrink-0"
          >
            {expanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <CardContent className="px-5 pb-5 space-y-5">
              <Separator />

              {/* Detailed scores */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-foreground">
                  Score Breakdown
                </h4>
                <div className="space-y-2.5">
                  {SCORE_DIMENSIONS.map((dim) => {
                    const score = result.scores[dim.key];
                    return (
                      <div key={dim.key} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs text-foreground">
                              {dim.label}
                            </span>
                            <span className="text-[10px] text-muted-foreground">
                              ({dim.weight})
                            </span>
                          </div>
                          <span
                            className={cn(
                              "text-xs font-semibold",
                              scoreColor(score)
                            )}
                          >
                            {Math.round(score)}
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-stone-100 overflow-hidden">
                          <motion.div
                            className={cn(
                              "h-full rounded-full",
                              scoreBarColor(score)
                            )}
                            initial={{ width: 0 }}
                            animate={{ width: `${score}%` }}
                            transition={{ duration: 0.6, ease: "easeOut" }}
                          />
                        </div>
                        <p className="text-[10px] text-muted-foreground">
                          {dim.description}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* 30-day projections */}
              {(result.projection_day_7 ||
                result.projection_day_14 ||
                result.projection_day_30) && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <TrendingDown className="w-3.5 h-3.5 text-emerald-600" />
                    30-Day Projections
                  </h4>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: "Day 7", data: result.projection_day_7 },
                      { label: "Day 14", data: result.projection_day_14 },
                      { label: "Day 30", data: result.projection_day_30 },
                    ].map(({ label, data }) => (
                      <div
                        key={label}
                        className="p-2.5 rounded-lg bg-stone-50 border border-border space-y-1.5"
                      >
                        <p className="text-[10px] font-semibold text-foreground">
                          {label}
                        </p>
                        <ProjectionRow
                          label="AQI"
                          value={data?.aqi_reduction_percent}
                        />
                        <ProjectionRow
                          label="Resp. cases"
                          value={data?.respiratory_cases_reduction_percent}
                        />
                        <ProjectionRow
                          label="PM2.5"
                          value={data?.pm25_reduction_percent}
                        />
                        {data?.narrative && (
                          <p className="text-[9px] text-muted-foreground leading-relaxed pt-1 border-t border-border">
                            {data.narrative}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Trade-offs */}
              {result.trade_offs.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-foreground">
                    Trade-offs
                  </h4>
                  <div className="space-y-2">
                    {result.trade_offs.map((item, i) => (
                      <TradeOffRow key={i} item={item} />
                    ))}
                  </div>
                </div>
              )}

              {/* Gemini simulation reasoning */}
              {result.gemini_simulation_text && (
                <div className="p-3 rounded-lg bg-stone-50 border border-border">
                  <p className="text-[10px] font-semibold text-muted-foreground mb-1.5 flex items-center gap-1">
                    <FlaskConical className="w-3 h-3" />
                    Gemini Simulation Reasoning
                  </p>
                  <p className="text-[10px] text-muted-foreground leading-relaxed">
                    {result.gemini_simulation_text}
                  </p>
                </div>
              )}
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

export default function SimulationPage() {
  const { analyses } = useAnalysisList(5);
  const latestComplete = analyses.find((a) => a.status === "complete");

  const { results, isLoading, isError, runSimulation, isRunning } =
    useSimulation(latestComplete?.id);

  const handleRun = () => {
    if (!latestComplete?.id) return;
    runSimulation({ analysis_id: latestComplete.id });
  };

  return (
    <PageWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-foreground">
              Scenario Simulation
            </h2>
            <p className="text-sm text-muted-foreground">
              30-day outcome projections ranked by composite PRISM Score
            </p>
          </div>
          <Button
            size="sm"
            className="bg-accent hover:bg-accent/90 text-white text-xs h-8"
            onClick={handleRun}
            disabled={isRunning || !latestComplete}
          >
            {isRunning ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Simulating...
              </>
            ) : (
              <>
                <FlaskConical className="w-3.5 h-3.5 mr-1.5" />
                Run Simulation
              </>
            )}
          </Button>
        </div>

        {/* Score weights info */}
        <div className="flex items-start gap-2 p-3 rounded-lg bg-stone-50 border border-border">
          <Info className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0 mt-0.5" />
          <p className="text-xs text-muted-foreground">
            PRISM Score is a weighted composite: Health Impact (35%) + Cost
            Efficiency (20%) + Speed (20%) + Community Acceptance (15%) +
            Sustainability (10%). Higher is better.
          </p>
        </div>

        {!latestComplete && !isLoading && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <p className="text-xs text-amber-700">
              No completed analysis found. Complete the Analysis and
              Interventions steps first.
            </p>
          </div>
        )}

        {isRunning && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 p-4 rounded-lg bg-accent/5 border border-accent/20"
          >
            <Loader2 className="w-4 h-4 text-accent animate-spin flex-shrink-0" />
            <div className="space-y-0.5">
              <p className="text-xs font-medium text-foreground">
                Gemini 2.5 Flash is simulating 30-day outcomes
              </p>
              <p className="text-[10px] text-muted-foreground">
                Evaluating all strategies simultaneously → Scoring 5 dimensions
                → Computing PRISM Scores (20–45 seconds)
              </p>
            </div>
          </motion.div>
        )}

        {isError && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200">
            <p className="text-xs text-red-700">
              Failed to load simulation results. Is the backend running?
            </p>
          </div>
        )}

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="border-border shadow-none">
                <CardContent className="p-5">
                  <div className="flex gap-4 animate-pulse">
                    <div className="w-16 h-16 rounded-full bg-stone-100" />
                    <div className="flex-1 space-y-3">
                      <div className="h-4 w-3/4 bg-stone-100 rounded" />
                      <div className="grid grid-cols-5 gap-1">
                        {[1, 2, 3, 4, 5].map((j) => (
                          <div key={j} className="h-6 bg-stone-100 rounded" />
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : results.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <FlaskConical className="w-10 h-10 text-muted-foreground mx-auto" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                No simulations yet
              </p>
              <p className="text-xs text-muted-foreground">
                Generate interventions first, then click &ldquo;Run
                Simulation&rdquo; to compare outcomes
              </p>
            </div>
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <span>Analysis</span>
              <ArrowRight className="w-3 h-3" />
              <span>Interventions</span>
              <ArrowRight className="w-3 h-3" />
              <span className="font-medium text-foreground">Simulation</span>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {results.map((result, index) => (
              <motion.div
                key={result.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.25,
                  delay: index * 0.08,
                  ease: "easeOut",
                }}
              >
                <SimulationCard result={result} index={index} />
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </PageWrapper>
  );
}