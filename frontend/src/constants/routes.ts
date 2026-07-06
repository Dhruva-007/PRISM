/**
 * PRISM application route constants.
 *
 * All navigation paths are defined here.
 * Never hardcode route strings in components.
 */

export const ROUTES = {
  ROOT: "/",
  LOGIN: "/login",
  OVERVIEW: "/overview",
  ANALYSIS: "/analysis",
  ANALYSIS_DETAIL: (id: string) => `/analysis/${id}`,
  INTERVENTIONS: "/interventions",
  SIMULATION: "/simulation",
  MEMORY: "/memory",
} as const;