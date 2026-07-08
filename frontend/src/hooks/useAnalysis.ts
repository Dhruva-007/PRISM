"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  AnalysisListResponse,
  AnalysisRequest,
  AnalysisResponse,
} from "@/types/analysis";

const ANALYSES_QUERY_KEY = ["analyses"] as const;

export function useAnalysisList(limit: number = 20) {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch } =
    useQuery<AnalysisListResponse>({
      queryKey: [...ANALYSES_QUERY_KEY, limit],
      queryFn: () =>
        apiClient.get<AnalysisListResponse>(`/analysis?limit=${limit}`),
      staleTime: 30 * 1000,
    });

  const runAnalysisMutation = useMutation<
    AnalysisResponse,
    Error,
    AnalysisRequest | undefined
  >({
    mutationFn: (request) =>
      apiClient.post<AnalysisResponse>("/analysis/run", request ?? {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ANALYSES_QUERY_KEY });
    },
  });

  return {
    analyses: data?.analyses ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError,
    refetch,
    runAnalysis: runAnalysisMutation.mutate,
    isRunning: runAnalysisMutation.isPending,
    latestResult: runAnalysisMutation.data?.analysis,
    runError: runAnalysisMutation.error,
  };
}

export function useAnalysisDetail(analysisId: string | null) {
  return useQuery<AnalysisResponse>({
    queryKey: [...ANALYSES_QUERY_KEY, analysisId],
    queryFn: () =>
      apiClient.get<AnalysisResponse>(`/analysis/${analysisId}`),
    enabled: analysisId !== null,
    staleTime: 5 * 60 * 1000,
  });
}