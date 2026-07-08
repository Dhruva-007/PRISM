"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  GenerateInterventionsRequest,
  InterventionListResponse,
} from "@/types/intervention";

const INTERVENTIONS_QUERY_KEY = ["interventions"] as const;

export function useInterventions(analysisId?: string) {
  const queryClient = useQueryClient();

  const url = analysisId
    ? `/interventions?analysis_id=${analysisId}`
    : `/interventions?limit=20`;

  const { data, isLoading, isError, refetch } =
    useQuery<InterventionListResponse>({
      queryKey: [...INTERVENTIONS_QUERY_KEY, analysisId],
      queryFn: () =>
        apiClient.get<InterventionListResponse>(url),
      staleTime: 60 * 1000,
    });

  const generateMutation = useMutation<
    InterventionListResponse,
    Error,
    GenerateInterventionsRequest
  >({
    mutationFn: (request) =>
      apiClient.post<InterventionListResponse>(
        "/interventions/generate",
        request
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: INTERVENTIONS_QUERY_KEY });
    },
  });

  return {
    strategies: data?.strategies ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError,
    refetch,
    generateInterventions: generateMutation.mutate,
    isGenerating: generateMutation.isPending,
    generationResult: generateMutation.data,
    generationError: generateMutation.error,
  };
}