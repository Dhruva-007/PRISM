"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  RunSimulationRequest,
  SimulationListResponse,
} from "@/types/simulation";

const SIMULATION_QUERY_KEY = ["simulation"] as const;

export function useSimulation(analysisId?: string) {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch } =
    useQuery<SimulationListResponse>({
      queryKey: [...SIMULATION_QUERY_KEY, analysisId],
      queryFn: () =>
        apiClient.get<SimulationListResponse>(
          `/simulation/${analysisId}`
        ),
      enabled: !!analysisId,
      staleTime: 60 * 1000,
    });

  const runSimulationMutation = useMutation<
    SimulationListResponse,
    Error,
    RunSimulationRequest
  >({
    mutationFn: (request) =>
      apiClient.post<SimulationListResponse>(
        "/simulation/run",
        request
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SIMULATION_QUERY_KEY });
    },
  });

  return {
    results: data?.results ?? [],
    total: data?.total ?? 0,
    recommendedInterventionId: data?.recommended_intervention_id,
    isLoading,
    isError,
    refetch,
    runSimulation: runSimulationMutation.mutate,
    isRunning: runSimulationMutation.isPending,
    simulationData: runSimulationMutation.data,
    runError: runSimulationMutation.error,
  };
}