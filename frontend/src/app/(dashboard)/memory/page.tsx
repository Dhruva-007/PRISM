/**
 * Memory page for PRISM dashboard.
 *
 * Displays decision history and allows recording new decisions
 * from completed simulation results. Decision makers can also
 * record actual outcomes to close the learning loop.
 */

"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  CheckCircle,
  Clock,
  MapPin,
  Trophy,
  ChevronDown,
  ChevronUp,
  Plus,
  TrendingDown,
  AlertTriangle,
  Loader2,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useDecisionMemory } from "@/hooks/useDecisionMemory";
import { useSimulation } from "@/hooks/useSimulation";
import { useAnalysisList } from "@/hooks/useAnalysis";
import type { DecisionMemoryRecord, DecisionStatus } from "@/types/memory";
import { formatRelativeTime, formatDate, cn } from "@/lib/utils";

const statusConfig: Record<
  DecisionStatus,
  { label: string; icon: React.ElementType; className: string }
> = {
  selected: {
    label: "Selected",
    icon: Clock,
    className: "text-blue-600 bg-blue-50 border-blue-200",
  },
  in_progress: {
    label: "In Progress",
    icon: Clock,
    className: "text-amber-600 bg-amber-50 border-amber-200",
  },
  completed: {
    label: "Completed",
    icon: CheckCircle,
    className: "text-emerald-600 bg-emerald-50 border-emerald-200",
  },
  abandoned: {
    label: "Abandoned",
    icon: XCircle,
    className: "text-red-600 bg-red-50 border-red-200",
  },
};

function MemoryCard({ record }: { record: DecisionMemoryRecord }) {
  const [expanded, setExpanded] = useState(false);
  const config = statusConfig[record.status] ?? statusConfig.selected;
  const StatusIcon = config.icon;

  return (
    <Card className="border-border shadow-none hover:shadow-sm transition-shadow duration-200">
      <CardHeader className="pb-3 pt-4 px-5">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2 flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge
                type="severity"
                value={record.analysis_severity as "low" | "medium" | "high" | "critical"}
              />
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium border",
                  config.className
                )}
              >
                <StatusIcon className="w-3 h-3" />
                {config.label}
              </span>
              <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatRelativeTime(record.created_at)}
              </span>
              <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {record.location}
              </span>
            </div>

            <CardTitle className="text-sm font-semibold text-foreground leading-snug">
              {record.analysis_headline}
            </CardTitle>

            <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
              <span>
                Strategy:{" "}
                <span className="font-medium text-foreground">
                  {record.selected_strategy_title}
                </span>
              </span>
              {record.prism_score_at_selection !== null &&
                record.prism_score_at_selection !== undefined && (
                  <span className="flex items-center gap-1">
                    <Trophy className="w-3 h-3 text-amber-500" />
                    PRISM {record.prism_score_at_selection.toFixed(1)}
                  </span>
                )}
              {record.rank_at_selection !== null &&
                record.rank_at_selection !== undefined && (
                  <span>Rank #{record.rank_at_selection}</span>
                )}
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
            <CardContent className="px-5 pb-5 space-y-4">
              <Separator />

              {/* Decision rationale */}
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-foreground">
                  Decision Rationale
                </p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {record.selection_reason}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  Decided by{" "}
                  <span className="font-medium">{record.selected_by_name}</span>{" "}
                  on {formatDate(record.created_at)}
                </p>
              </div>

              {/* Actual outcomes */}
              {record.actual_outcome ? (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <TrendingDown className="w-3.5 h-3.5 text-emerald-600" />
                    Actual Outcomes
                  </p>
                  <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-100 space-y-2">
                    {record.actual_outcome.aqi_change_percent !== null &&
                      record.actual_outcome.aqi_change_percent !== undefined && (
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-emerald-700">
                            AQI Change
                          </span>
                          <span className="text-xs font-semibold text-emerald-800">
                            {record.actual_outcome.aqi_change_percent > 0
                              ? "+"
                              : ""}
                            {record.actual_outcome.aqi_change_percent.toFixed(1)}%
                          </span>
                        </div>
                      )}
                    {record.actual_outcome
                      .respiratory_cases_change_percent !== null &&
                      record.actual_outcome
                        .respiratory_cases_change_percent !== undefined && (
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-emerald-700">
                            Respiratory Cases
                          </span>
                          <span className="text-xs font-semibold text-emerald-800">
                            {record.actual_outcome
                              .respiratory_cases_change_percent > 0
                              ? "+"
                              : ""}
                            {record.actual_outcome.respiratory_cases_change_percent.toFixed(
                              1
                            )}%
                          </span>
                        </div>
                      )}
                    {record.actual_outcome.implementation_success !==
                      null &&
                      record.actual_outcome.implementation_success !==
                        undefined && (
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-emerald-700">
                            Implementation
                          </span>
                          <span className="text-xs font-semibold text-emerald-800">
                            {record.actual_outcome.implementation_success
                              ? "Successful"
                              : "Partial/Failed"}
                          </span>
                        </div>
                      )}
                    {record.actual_outcome.notes && (
                      <p className="text-[10px] text-emerald-700 leading-relaxed pt-1 border-t border-emerald-200">
                        {record.actual_outcome.notes}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-stone-50 border border-border">
                  <Clock className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                  <p className="text-xs text-muted-foreground">
                    No outcomes recorded yet. Update once the intervention
                    has been running long enough to observe results.
                  </p>
                </div>
              )}

              {/* Lessons learned */}
              {record.lessons_learned && (
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-accent" />
                    Lessons Learned
                  </p>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {record.lessons_learned}
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

function RecordDecisionPanel({
  onRecord,
  isRecording,
}: {
  onRecord: (analysisId: string, strategyId: string, reason: string) => void;
  isRecording: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const { analyses } = useAnalysisList(5);
  const latestComplete = analyses.find((a) => a.status === "complete");
  const { results } = useSimulation(latestComplete?.id);
  const topStrategy = results.find((r) => r.rank_among_strategies === 1);

  const handleSubmit = () => {
    if (!latestComplete?.id || !topStrategy?.intervention_id || reason.length < 10)
      return;
    onRecord(latestComplete.id, topStrategy.intervention_id, reason);
    setOpen(false);
    setReason("");
  };

  if (!latestComplete || !topStrategy) return null;

  return (
    <div className="space-y-3">
      <Button
        size="sm"
        variant="outline"
        onClick={() => setOpen(!open)}
        className="text-xs h-8"
      >
        <Plus className="w-3.5 h-3.5 mr-1.5" />
        Record Decision
      </Button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <Card className="border-accent/30 bg-accent/[0.02]">
              <CardContent className="px-5 py-4 space-y-3">
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-foreground">
                    Record Decision
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    Recording selection of:{" "}
                    <span className="font-medium text-foreground">
                      {topStrategy.intervention_title}
                    </span>{" "}
                    (PRISM Score: {topStrategy.scores.composite_prism_score})
                  </p>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-medium text-foreground">
                    Why did you choose this strategy? (min 10 characters)
                  </label>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Describe your rationale for selecting this intervention strategy..."
                    className="w-full text-xs border border-border rounded-md p-2.5 resize-none h-20 bg-background focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    className="bg-accent hover:bg-accent/90 text-white text-xs h-8"
                    onClick={handleSubmit}
                    disabled={isRecording || reason.length < 10}
                  >
                    {isRecording ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      "Save Decision"
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-xs h-8"
                    onClick={() => setOpen(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function MemoryPage() {
  const {
    records,
    isLoading,
    isError,
    recordDecision,
    isRecording,
    recordDecisionResult,
  } = useDecisionMemory();

  const handleRecord = (
    analysisId: string,
    strategyId: string,
    reason: string
  ) => {
    recordDecision({
      analysis_id: analysisId,
      selected_strategy_id: strategyId,
      selection_reason: reason,
    });
  };

  return (
    <PageWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-foreground">
              Decision Memory
            </h2>
            <p className="text-sm text-muted-foreground">
              Historical decisions and actual outcomes — PRISM learns from
              every intervention
            </p>
          </div>
        </div>

        {/* Record decision panel */}
        <RecordDecisionPanel
          onRecord={handleRecord}
          isRecording={isRecording}
        />

        {/* Success message */}
        {recordDecisionResult && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 p-3 rounded-lg bg-emerald-50 border border-emerald-200"
          >
            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <p className="text-xs text-emerald-700">
              Decision recorded successfully. PRISM will use this to improve
              future recommendations.
            </p>
          </motion.div>
        )}

        {/* Error state */}
        {isError && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <p className="text-xs text-red-700">
              Failed to load decision memory. Is the backend running?
            </p>
          </div>
        )}

        {/* Memory records */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <Card key={i} className="border-border shadow-none">
                <CardContent className="p-5">
                  <div className="space-y-3 animate-pulse">
                    <div className="flex gap-2">
                      <div className="h-5 w-16 bg-stone-100 rounded" />
                      <div className="h-5 w-20 bg-stone-100 rounded" />
                    </div>
                    <div className="h-4 w-3/4 bg-stone-100 rounded" />
                    <div className="h-3 w-1/2 bg-stone-100 rounded" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : records.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <BookOpen className="w-10 h-10 text-muted-foreground mx-auto" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                No decisions recorded yet
              </p>
              <p className="text-xs text-muted-foreground">
                Complete the full pipeline (Analysis → Interventions →
                Simulation), then record your decision here
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {records.map((record, index) => (
              <motion.div
                key={record.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.25,
                  delay: index * 0.06,
                  ease: "easeOut",
                }}
              >
                <MemoryCard record={record} />
              </motion.div>
            ))}
          </div>
        )}

        {/* Learning indicator */}
        {records.length > 0 && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>
              {records.length} decision{records.length !== 1 ? "s" : ""}{" "}
              recorded · PRISM learning from outcomes
            </span>
          </div>
        )}
      </div>
    </PageWrapper>
  );
}