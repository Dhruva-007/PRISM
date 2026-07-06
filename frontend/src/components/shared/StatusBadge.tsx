/**
 * StatusBadge component for PRISM.
 *
 * Displays severity and status levels consistently across the application.
 * Used in event lists, analysis cards, and intervention displays.
 */

import { cn } from "@/lib/utils";

type Severity = "low" | "medium" | "high" | "critical";
type Status = "pending" | "analyzing" | "complete" | "failed";

interface StatusBadgeProps {
  type: "severity" | "status";
  value: Severity | Status;
  className?: string;
}

const severityConfig: Record<
  Severity,
  { label: string; className: string }
> = {
  low: {
    label: "Low",
    className: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  },
  medium: {
    label: "Medium",
    className: "bg-amber-50 text-amber-700 border border-amber-200",
  },
  high: {
    label: "High",
    className: "bg-orange-50 text-orange-700 border border-orange-200",
  },
  critical: {
    label: "Critical",
    className: "bg-red-50 text-red-700 border border-red-200",
  },
};

const statusConfig: Record<Status, { label: string; className: string }> = {
  pending: {
    label: "Pending",
    className: "bg-stone-50 text-stone-600 border border-stone-200",
  },
  analyzing: {
    label: "Analyzing",
    className: "bg-blue-50 text-blue-700 border border-blue-200",
  },
  complete: {
    label: "Complete",
    className: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  },
  failed: {
    label: "Failed",
    className: "bg-red-50 text-red-700 border border-red-200",
  },
};

export function StatusBadge({ type, value, className }: StatusBadgeProps) {
  const config =
    type === "severity"
      ? severityConfig[value as Severity]
      : statusConfig[value as Status];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  );
}