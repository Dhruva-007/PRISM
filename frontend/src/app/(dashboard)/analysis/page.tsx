/**
 * Analysis page for PRISM dashboard.
 *
 * Displays AI-powered situation analyses from Gemini 2.5 Flash.
 * Users can trigger new analyses and view complete results
 * including root causes, patterns, and Gemini reasoning.
 */

"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BrainCircuit,
  ChevronDown,
  ChevronUp,
  Clock,
  MapPin,
  AlertTriangle,
  Zap,
  Target,
  FileText,
  Loader2,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useAnalysisList } from "@/hooks/useAnalysis";
import type { SituationAnalysis } from "@/types/analysis";
import { formatRelativeTime } from "@/lib/utils";

const urgencyConfig = {
  routine: { label: "Routine", className: "text-stone-600 bg-stone-50 border-stone-200" },
  elevated: { label: "Elevated", className: "text-amber-700 bg-amber-50 border-amber-200" },
  urgent: { label: "Urgent", className: "text-orange-700 bg-orange-50 border-orange-200" },
  emergency: { label: "Emergency", className: "text-red-700 bg-red-50 border-red-200" },
};

function AnalysisCard({ analysis }: { analysis: SituationAnalysis }) {
  const [expanded, setExpanded] = useState(false);
  const urgency = urgencyConfig[analysis.urgency] ?? urgencyConfig.routine;

  return (
    <Card className="border-border shadow-none hover:shadow-sm transition-shadow duration-200">
      <CardHeader className="pb-3 pt-4 px-5">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2 flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge type="severity" value={analysis.severity_level} />
              <span
                className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium border ${urgency.className}`}
              >
                {urgency.label}
              </span>
              <StatusBadge type="status" value={analysis.status} />
            </div>
            <CardTitle className="text-sm font-semibold text-foreground leading-snug">
              {analysis.headline || "Situation Analysis"}
            </CardTitle>
            <div className="flex items-center gap-4 text-[10px] text-muted-foreground flex-wrap">
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {analysis.location}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatRelativeTime(analysis.created_at)}
              </span>
              {analysis.data_summary && (
                <span className="flex items-center gap-1">
                  <FileText className="w-3 h-3" />
                  {analysis.data_summary.total_events} events analyzed
                </span>
              )}
              {analysis.confidence_overall > 0 && (
                <span>
                  Confidence: {Math.round(analysis.confidence_overall * 100)}%
                </span>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="h-8 w-8 p-0 flex-shrink-0"
            disabled={analysis.status !== "complete"}
          >
            {expanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {analysis.status === "complete" && (
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

                {/* Summary */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-accent" />
                    Situation Summary
                  </h4>
                  <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-line">
                    {analysis.summary}
                  </p>
                </div>

                {/* Key findings */}
                {analysis.key_findings.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-accent" />
                      Key Findings
                    </h4>
                    <ul className="space-y-1.5">
                      {analysis.key_findings.map((finding, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="w-4 h-4 rounded-full bg-accent/10 text-accent text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                            {i + 1}
                          </span>
                          <p className="text-xs text-muted-foreground leading-relaxed">
                            {finding}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Root causes */}
                {analysis.root_causes.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-accent" />
                      Root Causes
                    </h4>
                    <div className="space-y-3">
                      {analysis.root_causes.map((rc, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-lg bg-stone-50 border border-border space-y-2"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-xs font-medium text-foreground leading-relaxed flex-1">
                              {rc.cause}
                            </p>
                            <span className="text-[10px] text-muted-foreground flex-shrink-0 capitalize">
                              {rc.category}
                            </span>
                          </div>
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] text-muted-foreground">
                                Confidence
                              </span>
                              <span className="text-[10px] font-medium text-foreground">
                                {Math.round(rc.confidence * 100)}%
                              </span>
                            </div>
                            <Progress
                              value={rc.confidence * 100}
                              className="h-1"
                            />
                          </div>
                          {rc.affected_population && (
                            <p className="text-[10px] text-muted-foreground">
                              <span className="font-medium">At risk: </span>
                              {rc.affected_population}
                            </p>
                          )}
                          {rc.supporting_evidence.length > 0 && (
                            <div className="space-y-0.5">
                              {rc.supporting_evidence.map((ev, j) => (
                                <p
                                  key={j}
                                  className="text-[10px] text-muted-foreground pl-2 border-l border-accent/30"
                                >
                                  {ev}
                                </p>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Patterns */}
                {analysis.patterns_detected.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-accent" />
                      Detected Patterns
                    </h4>
                    <div className="space-y-2">
                      {analysis.patterns_detected.map((pattern, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-3 p-2.5 rounded-md bg-stone-50 border border-border"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-muted-foreground leading-relaxed">
                              {pattern.pattern}
                            </p>
                            <div className="flex items-center gap-2 mt-1.5">
                              <span className="text-[10px] text-muted-foreground capitalize">
                                {pattern.pattern_type}
                              </span>
                              <span className="text-[10px] text-muted-foreground">·</span>
                              <span className="text-[10px] text-muted-foreground">
                                Sources: {pattern.data_sources.join(", ")}
                              </span>
                            </div>
                          </div>
                          <div className="flex-shrink-0 text-right">
                            <span className="text-xs font-semibold text-accent">
                              {Math.round(pattern.strength * 100)}%
                            </span>
                            <p className="text-[10px] text-muted-foreground">
                              strength
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Population at risk + action timeframe */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {analysis.population_at_risk && (
                    <div className="p-3 rounded-lg bg-red-50 border border-red-100">
                      <p className="text-[10px] font-semibold text-red-700 mb-1">
                        Population at Risk
                      </p>
                      <p className="text-xs text-red-600 leading-relaxed">
                        {analysis.population_at_risk}
                      </p>
                    </div>
                  )}
                  {analysis.recommended_action_timeframe && (
                    <div className="p-3 rounded-lg bg-amber-50 border border-amber-100">
                      <p className="text-[10px] font-semibold text-amber-700 mb-1">
                        Action Timeframe
                      </p>
                      <p className="text-xs text-amber-600 leading-relaxed">
                        {analysis.recommended_action_timeframe}
                      </p>
                    </div>
                  )}
                </div>

                {/* Gemini reasoning — collapsible */}
                {analysis.gemini_reasoning && (
                  <div className="p-3 rounded-lg bg-stone-50 border border-border">
                    <p className="text-[10px] font-semibold text-muted-foreground mb-2 flex items-center gap-1.5">
                      <BrainCircuit className="w-3 h-3" />
                      Gemini 2.5 Reasoning
                    </p>
                    <p className="text-[10px] text-muted-foreground leading-relaxed whitespace-pre-line">
                      {analysis.gemini_reasoning}
                    </p>
                  </div>
                )}
              </CardContent>
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {analysis.status === "failed" && analysis.error_message && (
        <CardContent className="px-5 pb-4">
          <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
            <XCircle className="w-3.5 h-3.5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-red-700">{analysis.error_message}</p>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export default function AnalysisPage() {
  const { analyses, isLoading, isError, runAnalysis, isRunning} =
    useAnalysisList(20);

  return (
    <PageWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-foreground">
              Situation Analyses
            </h2>
            <p className="text-sm text-muted-foreground">
              AI-powered root cause analysis using Gemini 2.5 Flash
            </p>
          </div>
          <Button
            size="sm"
            className="bg-accent hover:bg-accent/90 text-white text-xs h-8"
            onClick={() => runAnalysis(undefined)}
            disabled={isRunning}
          >
            {isRunning ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <BrainCircuit className="w-3.5 h-3.5 mr-1.5" />
                Run Analysis
              </>
            )}
          </Button>
        </div>

        {/* Running indicator */}
        {isRunning && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 p-4 rounded-lg bg-accent/5 border border-accent/20"
          >
            <Loader2 className="w-4 h-4 text-accent animate-spin flex-shrink-0" />
            <div className="space-y-0.5">
              <p className="text-xs font-medium text-foreground">
                Gemini 2.5 Flash is analyzing your community data
              </p>
              <p className="text-[10px] text-muted-foreground">
                Assembling context → Detecting patterns → Reasoning → Storing results
                (15–30 seconds)
              </p>
            </div>
          </motion.div>
        )}

        {/* Error state */}
        {isError && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
            <XCircle className="w-4 h-4 text-red-600" />
            <p className="text-xs text-red-700">
              Failed to load analyses. Is the backend running?
            </p>
          </div>
        )}

        {/* Analysis list */}
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
        ) : analyses.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <BrainCircuit className="w-10 h-10 text-muted-foreground mx-auto" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                No analyses yet
              </p>
              <p className="text-xs text-muted-foreground">
                Click &ldquo;Run Analysis&rdquo; to start your first Gemini-powered
                situation analysis
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {analyses.map((analysis, index) => (
              <motion.div
                key={analysis.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.25,
                  delay: index * 0.05,
                  ease: "easeOut",
                }}
              >
                <AnalysisCard analysis={analysis} />
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </PageWrapper>
  );
}