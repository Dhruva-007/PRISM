/**
 * Overview page for PRISM dashboard.
 *
 * The command center — shows pipeline status, live metrics,
 * air quality chart, health chart, community map, and strategy comparison.
 * City-aware: all data and labels reflect the selected city.
 */

"use client";

import { Wind, Thermometer, Activity, AlertTriangle, RefreshCw, CheckCircle, XCircle } from "lucide-react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { PipelineStatus } from "@/components/shared/PipelineStatus";
import { AirQualityChart } from "@/components/charts/AirQualityChart";
import { HealthTrendChart } from "@/components/charts/HealthTrendChart";
import { ScoreComparisonChart } from "@/components/charts/ScoreComparisonChart";
import { CommunityMap } from "@/components/maps/CommunityMap";
import { useEvents } from "@/hooks/useEvents";
import { useAnalysisList } from "@/hooks/useAnalysis";
import { useInterventions } from "@/hooks/useInterventions";
import { useSimulation } from "@/hooks/useSimulation";
import { useDecisionMemory } from "@/hooks/useDecisionMemory";
import { useCity } from "@/hooks/useCity";
import type {
  AirQualityMetrics,
  WeatherMetrics,
  HealthMetrics,
  CommunityEvent,
} from "@/types/community";
import { formatRelativeTime } from "@/lib/utils";

type SeverityLevel = "low" | "medium" | "high" | "critical";

function deriveMetricSummary(events: CommunityEvent[]) {
  const aqEvents = events.filter((e) => e.event_type === "air_quality");
  const weatherEvents = events.filter((e) => e.event_type === "weather");
  const healthEvents = events.filter((e) => e.event_type === "health_report");
  const alertEvents = events.filter(
    (e) => e.severity === "critical" || e.severity === "high"
  );

  const avgAqi =
    aqEvents.length > 0
      ? Math.round(
          aqEvents.reduce((sum, e) => {
            const m = e.metrics as AirQualityMetrics;
            return sum + (m.aqi ?? 0);
          }, 0) / aqEvents.length
        )
      : null;

  const latestWeather =
    weatherEvents.length > 0
      ? (weatherEvents[0].metrics as WeatherMetrics)
      : null;

  const totalRespiratoryCases = healthEvents.reduce((sum, e) => {
    const m = e.metrics as HealthMetrics;
    return sum + (m.respiratory_cases ?? 0);
  }, 0);

  return {
    avgAqi,
    latestWeather,
    totalRespiratoryCases,
    activeAlerts: alertEvents.length,
  };
}

function MetricCardSkeleton() {
  return (
    <Card className="border-border shadow-none">
      <CardHeader className="pb-2 pt-4 px-4">
        <Skeleton className="h-3 w-24" />
      </CardHeader>
      <CardContent className="px-4 pb-4 space-y-2">
        <Skeleton className="h-8 w-16" />
        <Skeleton className="h-3 w-32" />
      </CardContent>
    </Card>
  );
}

export default function OverviewPage() {
  const { selectedCity } = useCity();
  const { events, isLoading, isError, triggerIngestion, isIngesting, ingestionResult } =
    useEvents({ limit: 100 });
  const { analyses } = useAnalysisList(10);
  const { strategies } = useInterventions();
  const latestComplete = analyses.find((a) => a.status === "complete");
  const { results: simResults } = useSimulation(latestComplete?.id);
  const { records: memoryRecords } = useDecisionMemory();

  const summary = deriveMetricSummary(events);

  const aqiSeverity: SeverityLevel =
    summary.avgAqi === null
      ? "low"
      : summary.avgAqi > 200
      ? "critical"
      : summary.avgAqi > 150
      ? "high"
      : summary.avgAqi > 100
      ? "medium"
      : "low";

  const cityLabel = selectedCity
    ? `${selectedCity.display_name}, ${selectedCity.state}`
    : "Select a city";

  const handleRefreshData = () => {
    if (selectedCity) {
      triggerIngestion({
        city_id: selectedCity.city_id,
        city: `${selectedCity.display_name}, ${selectedCity.state}`,
        latitude: selectedCity.latitude,
        longitude: selectedCity.longitude,
      });
    } else {
      triggerIngestion(undefined);
    }
  };

  return (
    <PageWrapper>
      <div className="space-y-6">
        {/* Pipeline Status */}
        <div className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Pipeline Status
          </p>
          <PipelineStatus
            eventCount={events.length}
            analysisCount={analyses.length}
            interventionCount={strategies.length}
            simulationCount={simResults.length}
            memoryCount={memoryRecords.length}
          />
        </div>

        {/* Header + Refresh */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-foreground">
              Community Health Snapshot
            </h2>
            <p className="text-sm text-muted-foreground">
              {cityLabel} · {events.length} events loaded
            </p>
          </div>
          <div className="flex items-center gap-2">
            {ingestionResult && (
              <div className="flex items-center gap-1.5 text-xs text-emerald-700">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>{ingestionResult.events_ingested} ingested</span>
              </div>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={handleRefreshData}
              disabled={isIngesting}
              className="text-xs h-8"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 mr-1.5 ${isIngesting ? "animate-spin" : ""}`}
              />
              {isIngesting ? "Ingesting..." : "Refresh Data"}
            </Button>
          </div>
        </div>

        {isError && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
            <XCircle className="w-4 h-4 text-red-600" />
            <p className="text-xs text-red-700">
              Failed to load events. Is the backend running on port 8000?
            </p>
          </div>
        )}

        {/* Metric cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {isLoading ? (
            <>
              <MetricCardSkeleton />
              <MetricCardSkeleton />
              <MetricCardSkeleton />
              <MetricCardSkeleton />
            </>
          ) : (
            <>
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0, ease: "easeOut" }}
              >
                <Card className="border-border shadow-none hover:shadow-sm transition-shadow duration-200">
                  <CardHeader className="pb-2 pt-4 px-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs font-medium text-muted-foreground">
                        Air Quality Index
                      </CardTitle>
                      <div className="w-7 h-7 rounded-md bg-stone-100 flex items-center justify-center">
                        <Wind className="w-3.5 h-3.5 text-stone-500" />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="px-4 pb-4">
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-2xl font-semibold text-foreground">
                        {summary.avgAqi ?? "—"}
                      </span>
                      <span className="text-xs text-muted-foreground">AQI avg</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {events.filter((e) => e.event_type === "air_quality").length} stations
                    </p>
                    <div className="mt-2">
                      <StatusBadge type="severity" value={aqiSeverity} />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.07, ease: "easeOut" }}
              >
                <Card className="border-border shadow-none hover:shadow-sm transition-shadow duration-200">
                  <CardHeader className="pb-2 pt-4 px-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs font-medium text-muted-foreground">
                        Temperature
                      </CardTitle>
                      <div className="w-7 h-7 rounded-md bg-stone-100 flex items-center justify-center">
                        <Thermometer className="w-3.5 h-3.5 text-stone-500" />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="px-4 pb-4">
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-2xl font-semibold text-foreground">
                        {summary.latestWeather?.temperature_celsius?.toFixed(1) ?? "—"}
                      </span>
                      <span className="text-xs text-muted-foreground">°C</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {summary.latestWeather?.weather_condition ?? "No data"}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Wind: {summary.latestWeather?.wind_speed_ms?.toFixed(1) ?? "—"} m/s
                    </p>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.14, ease: "easeOut" }}
              >
                <Card className="border-border shadow-none hover:shadow-sm transition-shadow duration-200">
                  <CardHeader className="pb-2 pt-4 px-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs font-medium text-muted-foreground">
                        Respiratory Cases
                      </CardTitle>
                      <div className="w-7 h-7 rounded-md bg-stone-100 flex items-center justify-center">
                        <Activity className="w-3.5 h-3.5 text-stone-500" />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="px-4 pb-4">
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-2xl font-semibold text-foreground">
                        {summary.totalRespiratoryCases > 0
                          ? summary.totalRespiratoryCases.toLocaleString()
                          : "—"}
                      </span>
                      <span className="text-xs text-muted-foreground">reported</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Across {events.filter((e) => e.event_type === "health_report").length} districts
                    </p>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.21, ease: "easeOut" }}
              >
                <Card className="border-border shadow-none hover:shadow-sm transition-shadow duration-200">
                  <CardHeader className="pb-2 pt-4 px-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs font-medium text-muted-foreground">
                        Active Alerts
                      </CardTitle>
                      <div className="w-7 h-7 rounded-md bg-stone-100 flex items-center justify-center">
                        <AlertTriangle className="w-3.5 h-3.5 text-stone-500" />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="px-4 pb-4">
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-2xl font-semibold text-foreground">
                        {summary.activeAlerts}
                      </span>
                      <span className="text-xs text-muted-foreground">high/critical</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Events requiring attention
                    </p>
                    {summary.activeAlerts > 0 && (
                      <div className="mt-2">
                        <StatusBadge
                          type="severity"
                          value={summary.activeAlerts >= 5 ? "critical" : "high"}
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </>
          )}
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card className="border-border shadow-none">
            <CardHeader className="pb-2 pt-4 px-5">
              <CardTitle className="text-sm font-semibold text-foreground">
                Air Quality by Station
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                AQI readings · WHO threshold at 100
              </p>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              <AirQualityChart events={events} />
            </CardContent>
          </Card>

          <Card className="border-border shadow-none">
            <CardHeader className="pb-2 pt-4 px-5">
              <CardTitle className="text-sm font-semibold text-foreground">
                Respiratory Cases by District
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                Daily aggregate · Color = severity
              </p>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              <HealthTrendChart events={events} />
            </CardContent>
          </Card>
        </div>

        {/* Map + Score comparison */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <Card className="border-border shadow-none">
              <CardHeader className="pb-2 pt-4 px-5">
                <CardTitle className="text-sm font-semibold text-foreground">
                  Community Event Map
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Live event locations · Color = severity
                </p>
              </CardHeader>
              <CardContent className="px-4 pb-4">
                <CommunityMap events={events} height={280} />
              </CardContent>
            </Card>
          </div>

          <Card className="border-border shadow-none">
            <CardHeader className="pb-2 pt-4 px-5">
              <CardTitle className="text-sm font-semibold text-foreground">
                Strategy Comparison
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                PRISM Score dimensions
              </p>
            </CardHeader>
            <CardContent className="px-2 pb-4">
              <ScoreComparisonChart results={simResults} />
            </CardContent>
          </Card>
        </div>

        {/* Recent events feed */}
        <Card className="border-border shadow-none">
          <CardHeader className="pb-3 pt-4 px-5">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-foreground">
                Recent Events
              </CardTitle>
              <span className="text-xs text-muted-foreground">
                {events.length} events · Live feed
              </span>
            </div>
          </CardHeader>
          <CardContent className="px-5 pb-4">
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex items-start gap-4 py-2">
                    <Skeleton className="h-3 w-20" />
                    <div className="flex-1 space-y-1.5">
                      <Skeleton className="h-3 w-full" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                    <Skeleton className="h-5 w-14" />
                  </div>
                ))}
              </div>
            ) : events.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-muted-foreground">
                  No events yet. Click &ldquo;Refresh Data&rdquo; to ingest live data.
                </p>
              </div>
            ) : (
              <div className="space-y-0">
                {events.slice(0, 12).map((event, index) => (
                  <motion.div
                    key={event.id ?? index}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2, delay: index * 0.025, ease: "easeOut" }}
                    className="flex items-start gap-4 py-2.5 border-b border-border last:border-0"
                  >
                    <span className="text-xs text-muted-foreground font-mono w-24 flex-shrink-0 pt-0.5">
                      {formatRelativeTime(event.ingested_at)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-foreground leading-relaxed">
                        {event.location.district} —{" "}
                        {event.event_type.replace("_", " ")}
                      </p>
                      <p className="text-[10px] text-muted-foreground mt-0.5 capitalize">
                        Source: {event.source.replace("_", " ")} · {event.location.city}
                      </p>
                    </div>
                    <StatusBadge
                      type="severity"
                      value={event.severity}
                      className="flex-shrink-0"
                    />
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* System status */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>
            PRISM monitoring {selectedCity?.display_name ?? "—"} · {events.length} events · {analyses.length} analyses · {simResults.length} simulations
          </span>
        </div>
      </div>
    </PageWrapper>
  );
}