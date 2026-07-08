"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/hooks/useAuth";
import type {
  DecisionMemoryListResponse,
  DecisionMemoryResponse,
  RecordDecisionRequest,
  RecordOutcomeRequest,
} from "@/types/memory";

const MEMORY_QUERY_KEY = ["decision-memory"] as const;

export function useDecisionMemory() {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const { data, isLoading, isError, refetch } =
    useQuery<DecisionMemoryListResponse>({
      queryKey: MEMORY_QUERY_KEY,
      queryFn: () =>
        apiClient.get<DecisionMemoryListResponse>("/memory?limit=50"),
      staleTime: 30 * 1000,
    });

  const recordDecisionMutation = useMutation<
    DecisionMemoryResponse,
    Error,
    RecordDecisionRequest
  >({
    mutationFn: (request) =>
      apiClient.post<DecisionMemoryResponse>("/memory/record", request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MEMORY_QUERY_KEY });
    },
  });

  const recordOutcomeMutation = useMutation<
    DecisionMemoryResponse,
    Error,
    { memoryId: string; request: RecordOutcomeRequest }
  >({
    mutationFn: ({ memoryId, request }) =>
      apiClient.patch<DecisionMemoryResponse>(
        `/memory/${memoryId}/outcome`,
        request
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MEMORY_QUERY_KEY });
    },
  });

  return {
    records: data?.records ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError,
    refetch,
    recordDecision: recordDecisionMutation.mutate,
    isRecording: recordDecisionMutation.isPending,
    recordDecisionResult: recordDecisionMutation.data,
    recordDecisionError: recordDecisionMutation.error,
    recordOutcome: recordOutcomeMutation.mutate,
    isRecordingOutcome: recordOutcomeMutation.isPending,
  };
}