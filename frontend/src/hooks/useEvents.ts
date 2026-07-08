"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  CommunityEventListResponse,
  IngestTriggerRequest,
  IngestTriggerResponse,
} from "@/types/community";

const EVENTS_QUERY_KEY = ["community-events"] as const;

interface UseEventsOptions {
  source?: string;
  eventType?: string;
  limit?: number;
  enabled?: boolean;
}

export function useEvents(options: UseEventsOptions = {}) {
  const { source, eventType, limit = 200, enabled = true } = options;
  const queryClient = useQueryClient();

  const params = new URLSearchParams();
  if (source) params.set("source", source);
  if (eventType) params.set("event_type", eventType);
  params.set("limit", limit.toString());

  const queryKey = [...EVENTS_QUERY_KEY, source, eventType, limit];

  const { data, isLoading, isError, error, refetch } =
    useQuery<CommunityEventListResponse>({
      queryKey,
      queryFn: () =>
        apiClient.get<CommunityEventListResponse>(
          `/ingest/events?${params.toString()}`
        ),
      enabled,
      staleTime: 30 * 1000,
      refetchInterval: false,
    });

  const triggerIngestionMutation = useMutation<
    IngestTriggerResponse,
    Error,
    IngestTriggerRequest | undefined
  >({
    mutationFn: (request) =>
      apiClient.post<IngestTriggerResponse>(
        "/ingest/trigger",
        request ?? {}
      ),
    onSuccess: async () => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await queryClient.invalidateQueries({ queryKey: EVENTS_QUERY_KEY });
      await refetch();
    },
  });

  return {
    events: data?.events ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError,
    error,
    refetch,
    triggerIngestion: triggerIngestionMutation.mutate,
    isIngesting: triggerIngestionMutation.isPending,
    ingestionResult: triggerIngestionMutation.data,
    ingestionError: triggerIngestionMutation.error,
  };
}