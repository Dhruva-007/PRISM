/**
 * Interventions page for PRISM dashboard.
 *
 * Displays AI-generated intervention strategies.
 * Users can generate new strategies from a completed analysis.
 */

"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lightbulb,
  Clock,
  DollarSign,
  Users,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Loader2,
  BrainCircuit,
  Target,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { useInterventions } from "@/hooks/useInterventions";
import { useAnalysisList } from "@/hooks/useAnalysis";
import type { InterventionStrategy, CostLevel } from "@/types/intervention";
import { cn } from "@/lib/utils";

const strategyTypeConfig = {
  immediate: {
    label: "Immediate",
    className: "bg-red-50 text-red-700 border-red-200",
  },
  short_term: {
    label: "Short-term",
    className: "bg-amber-50 text-amber-700 border-amber-200",
  },
  long_term: {
    label: "Long-term",
    className: "bg-blue-50 text-blue-700 border-blue-200",
  },
};

const costConfig: Record<CostLevel, { label: string; dots: number }> = {
  low: { label: "Low", dots: 1 },
  medium: { label: "Medium", dots: 2 },
  high: { label: "High", dots: 3 },
  very_high: { label: "Very High", dots: 4 },
};

function CostIndicator({ level }: { level: CostLevel }) {
  const config = costConfig[level] ?? costConfig.medium;
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4].map((dot) => (
        <div
          key={dot}
          className={cn(
            "w-1.5 h-1.5 rounded-full",
            dot <= config.dots ? "bg-foreground" : "bg-stone-200"
          )}
        />
      ))}
      <span className="text-xs text-muted-foreground ml-1">{config.label}</span>
    </div>
  );
}

function StrategyCard({
  strategy,
  index,
}: {
  strategy: InterventionStrategy;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const typeConfig =
    strategyTypeConfig[strategy.strategy_type] ??
    strategyTypeConfig.immediate;

  const maxTimeline =
    strategy.actions.length > 0
      ? Math.max(...strategy.actions.map((a) => a.timeline_days))
      : 0;

  return (
    <Card className="border-border shadow-none hover:shadow-sm transition-shadow duration-200">
      <CardHeader className="pb-3 pt-4 px-5">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2 flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                #{index + 1}
              </span>
              <span
                className={cn(
                  "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium border",
                  typeConfig.className
                )}
              >
                {typeConfig.label}
              </span>
              <CostIndicator level={strategy.total_estimated_cost} />
            </div>
            <CardTitle className="text-sm font-semibold text-foreground leading-snug">
              {strategy.title}
            </CardTitle>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {strategy.description}
            </p>
            <div className="flex items-center gap-4 text-[10px] text-muted-foreground flex-wrap">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {maxTimeline > 0 ? `${maxTimeline} days` : "TBD"}
              </span>
              <span className="flex items-center gap-1">
                <Users className="w-3 h-3" />
                {strategy.estimated_population_impacted}
              </span>
              <span className="flex items-center gap-1">
                <Lightbulb className="w-3 h-3" />
                {strategy.actions.length} actions
              </span>
              <span className="capitalize text-muted-foreground">
                Complexity: {strategy.implementation_complexity}
              </span>
            </div>
          </div>

          {strategy.prism_score !== null &&
            strategy.prism_score !== undefined && (
              <div className="flex-shrink-0 text-right">
                <p className="text-[10px] text-muted-foreground">PRISM</p>
                <p className="text-xl font-bold text-accent">
                  {Math.round(strategy.prism_score)}
                </p>
              </div>
            )}

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

              {/* Actions */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-accent" />
                  Action Plan
                </h4>
                <div className="space-y-2">
                  {strategy.actions.map((action) => (
                    <div
                      key={action.action_id}
                      className="p-3 rounded-lg bg-stone-50 border border-border space-y-1.5"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2 flex-1">
                          <span className="text-[10px] font-bold text-accent bg-accent/10 rounded px-1 py-0.5 flex-shrink-0 mt-0.5">
                            {action.action_id}
                          </span>
                          <p className="text-xs font-medium text-foreground">
                            {action.title}
                          </p>
                        </div>
                        <span className="text-[10px] text-muted-foreground flex-shrink-0">
                          Day {action.timeline_days}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed pl-6">
                        {action.description}
                      </p>
                      <div className="flex items-center gap-3 pl-6 flex-wrap">
                        <span className="text-[10px] text-muted-foreground">
                          <span className="font-medium">Owner:</span>{" "}
                          {action.responsible_party}
                        </span>
                        <ArrowRight className="w-3 h-3 text-muted-foreground" />
                        <span className="text-[10px] text-emerald-700">
                          ✓ {action.success_metric}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Expected Outcomes */}
              {strategy.expected_outcomes.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5 text-accent" />
                    Expected Outcomes
                  </h4>
                  <div className="space-y-2">
                    {strategy.expected_outcomes.map((outcome, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg bg-emerald-50 border border-emerald-100 space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-medium text-emerald-800">
                            {outcome.metric}
                          </p>
                          <span className="text-[10px] text-emerald-600">
                            {outcome.timeframe}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-emerald-700">
                          <span className="line-through text-emerald-400">
                            {outcome.baseline_value}
                          </span>
                          <ArrowRight className="w-3 h-3" />
                          <span className="font-medium">
                            {outcome.expected_value}
                          </span>
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-[10px] text-emerald-600">
                              Confidence
                            </span>
                            <span className="text-[10px] font-medium text-emerald-700">
                              {Math.round(outcome.confidence * 100)}%
                            </span>
                          </div>
                          <Progress
                            value={outcome.confidence * 100}
                            className="h-1"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Trade-offs and Risks */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {strategy.trade_offs.length > 0 && (
                  <div className="p-3 rounded-lg bg-amber-50 border border-amber-100 space-y-1.5">
                    <p className="text-[10px] font-semibold text-amber-700 flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      Trade-offs
                    </p>
                    <ul className="space-y-1">
                      {strategy.trade_offs.map((tradeoff, i) => (
                        <li
                          key={i}
                          className="text-[10px] text-amber-700 leading-relaxed pl-1 border-l border-amber-300"
                        >
                          {tradeoff}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {strategy.risks.length > 0 && (
                  <div className="p-3 rounded-lg bg-red-50 border border-red-100 space-y-1.5">
                    <p className="text-[10px] font-semibold text-red-700 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      Risks
                    </p>
                    <ul className="space-y-1">
                      {strategy.risks.map((risk, i) => (
                        <li
                          key={i}
                          className="text-[10px] text-red-700 leading-relaxed pl-1 border-l border-red-300"
                        >
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Required Authorities */}
              {strategy.required_authorities.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {strategy.required_authorities.map((auth, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center rounded-md bg-stone-100 px-2 py-0.5 text-[10px] text-stone-600 font-medium"
                    >
                      {auth}
                    </span>
                  ))}
                </div>
              )}

              {/* Gemini rationale */}
              {strategy.gemini_rationale && (
                <div className="p-3 rounded-lg bg-stone-50 border border-border">
                  <p className="text-[10px] font-semibold text-muted-foreground mb-1.5 flex items-center gap-1">
                    <BrainCircuit className="w-3 h-3" />
                    Gemini Rationale
                  </p>
                  <p className="text-[10px] text-muted-foreground leading-relaxed">
                    {strategy.gemini_rationale}
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

export default function InterventionsPage() {
  const { analyses } = useAnalysisList(5);
  const latestCompleteAnalysis = analyses.find(
    (a) => a.status === "complete"
  );

  const { strategies, isLoading, isError, generateInterventions, isGenerating } =
    useInterventions();

  const handleGenerate = () => {
    if (!latestCompleteAnalysis?.id) return;
    generateInterventions({
      analysis_id: latestCompleteAnalysis.id,
      num_strategies: 3,
    });
  };

  return (
    <PageWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-foreground">
              Intervention Strategies
            </h2>
            <p className="text-sm text-muted-foreground">
              AI-generated strategies ranked by feasibility and impact
            </p>
          </div>
          <Button
            size="sm"
            className="bg-accent hover:bg-accent/90 text-white text-xs h-8"
            onClick={handleGenerate}
            disabled={isGenerating || !latestCompleteAnalysis}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Lightbulb className="w-3.5 h-3.5 mr-1.5" />
                Generate Strategies
              </>
            )}
          </Button>
        </div>

        {!latestCompleteAnalysis && !isLoading && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <p className="text-xs text-amber-700">
              No completed analysis found. Run an analysis first on the Analysis
              page, then return here to generate interventions.
            </p>
          </div>
        )}

        {isGenerating && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 p-4 rounded-lg bg-accent/5 border border-accent/20"
          >
            <Loader2 className="w-4 h-4 text-accent animate-spin flex-shrink-0" />
            <div className="space-y-0.5">
              <p className="text-xs font-medium text-foreground">
                Gemini 2.5 Flash is generating intervention strategies
              </p>
              <p className="text-[10px] text-muted-foreground">
                Analyzing root causes → Generating diverse strategies → Defining
                actions (15–40 seconds)
              </p>
            </div>
          </motion.div>
        )}

        {isError && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200">
            <p className="text-xs text-red-700">
              Failed to load interventions. Is the backend running?
            </p>
          </div>
        )}

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="border-border shadow-none">
                <CardContent className="p-5">
                  <div className="space-y-3 animate-pulse">
                    <div className="flex gap-2">
                      <div className="h-5 w-16 bg-stone-100 rounded" />
                      <div className="h-5 w-20 bg-stone-100 rounded" />
                    </div>
                    <div className="h-4 w-3/4 bg-stone-100 rounded" />
                    <div className="h-3 w-full bg-stone-100 rounded" />
                    <div className="h-3 w-1/2 bg-stone-100 rounded" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : strategies.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <Lightbulb className="w-10 h-10 text-muted-foreground mx-auto" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                No strategies yet
              </p>
              <p className="text-xs text-muted-foreground">
                Run an analysis first, then click &ldquo;Generate
                Strategies&rdquo;
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {strategies.map((strategy, index) => (
              <motion.div
                key={strategy.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.25,
                  delay: index * 0.07,
                  ease: "easeOut",
                }}
              >
                <StrategyCard strategy={strategy} index={index} />
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </PageWrapper>
  );
}