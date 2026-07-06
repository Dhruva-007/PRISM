/**
 * PRISM sidebar navigation items.
 *
 * Each item maps to a dashboard route.
 * Icons use Lucide React icon names.
 */

import { ROUTES } from "./routes";

export const NAV_ITEMS = [
  {
    label: "Overview",
    href: ROUTES.OVERVIEW,
    icon: "LayoutDashboard",
    description: "Community health snapshot",
  },
  {
    label: "Analysis",
    href: ROUTES.ANALYSIS,
    icon: "BrainCircuit",
    description: "AI situation analysis",
  },
  {
    label: "Interventions",
    href: ROUTES.INTERVENTIONS,
    icon: "Lightbulb",
    description: "Generated strategies",
  },
  {
    label: "Simulation",
    href: ROUTES.SIMULATION,
    icon: "FlaskConical",
    description: "Scenario outcomes",
  },
  {
    label: "Memory",
    href: ROUTES.MEMORY,
    icon: "BookOpen",
    description: "Decision history",
  },
] as const;