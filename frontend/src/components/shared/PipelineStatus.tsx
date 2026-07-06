/**
 * PipelineStatus component for PRISM.
 *
 * Shows the current state of the PRISM decision intelligence pipeline:
 * Data → Analysis → Interventions → Simulation → Decision
 *
 * Each step shows whether it has been completed and links to that page.
 */

"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Database,
  BrainCircuit,
  Lightbulb,
  FlaskConical,
  BookOpen,
  ChevronRight,
  CheckCircle2,
  Circle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/constants/routes";

interface PipelineStep {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  href: string;
  completed: boolean;
  count?: number;
}

interface PipelineStatusProps {
  eventCount: number;
  analysisCount: number;
  interventionCount: number;
  simulationCount: number;
  memoryCount: number;
}

export function PipelineStatus({
  eventCount,
  analysisCount,
  interventionCount,
  simulationCount,
  memoryCount,
}: PipelineStatusProps) {
  const router = useRouter();

  const steps: PipelineStep[] = [
    {
      id: "data",
      label: "Data",
      description: "Community events",
      icon: Database,
      href: ROUTES.OVERVIEW,
      completed: eventCount > 0,
      count: eventCount,
    },
    {
      id: "analysis",
      label: "Analysis",
      description: "AI situation analysis",
      icon: BrainCircuit,
      href: ROUTES.ANALYSIS,
      completed: analysisCount > 0,
      count: analysisCount,
    },
    {
      id: "interventions",
      label: "Interventions",
      description: "Generated strategies",
      icon: Lightbulb,
      href: ROUTES.INTERVENTIONS,
      completed: interventionCount > 0,
      count: interventionCount,
    },
    {
      id: "simulation",
      label: "Simulation",
      description: "Scored outcomes",
      icon: FlaskConical,
      href: ROUTES.SIMULATION,
      completed: simulationCount > 0,
      count: simulationCount,
    },
    {
      id: "memory",
      label: "Decision",
      description: "Recorded & learning",
      icon: BookOpen,
      href: ROUTES.MEMORY,
      completed: memoryCount > 0,
      count: memoryCount,
    },
  ];

  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-1">
      {steps.map((step, index) => {
        const Icon = step.icon;
        const isLast = index === steps.length - 1;

        return (
          <div key={step.id} className="flex items-center gap-1 flex-shrink-0">
            <motion.button
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.06 }}
              onClick={() => router.push(step.href)}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition-all duration-150 hover:shadow-sm",
                step.completed
                  ? "bg-emerald-50 border-emerald-200 hover:bg-emerald-100"
                  : "bg-stone-50 border-border hover:bg-stone-100"
              )}
            >
              <div
                className={cn(
                  "w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0",
                  step.completed ? "bg-emerald-100" : "bg-stone-200"
                )}
              >
                <Icon
                  className={cn(
                    "w-3.5 h-3.5",
                    step.completed
                      ? "text-emerald-600"
                      : "text-muted-foreground"
                  )}
                />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <p
                    className={cn(
                      "text-xs font-medium leading-none",
                      step.completed ? "text-emerald-800" : "text-foreground"
                    )}
                  >
                    {step.label}
                  </p>
                  {step.completed ? (
                    <CheckCircle2 className="w-3 h-3 text-emerald-500 flex-shrink-0" />
                  ) : (
                    <Circle className="w-3 h-3 text-stone-300 flex-shrink-0" />
                  )}
                </div>
                <p className="text-[10px] text-muted-foreground leading-none mt-0.5">
                  {step.completed && step.count !== undefined
                    ? `${step.count} ${step.description}`
                    : step.description}
                </p>
              </div>
            </motion.button>

            {!isLast && (
              <ChevronRight className="w-3.5 h-3.5 text-stone-300 flex-shrink-0" />
            )}
          </div>
        );
      })}
    </div>
  );
}