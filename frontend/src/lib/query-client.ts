/**
 * React Query client configuration for PRISM.
 *
 * Defines global defaults for all queries and mutations:
 * - Stale time: how long data is considered fresh
 * - Retry behavior: how many times to retry failed requests
 * - Error handling defaults
 *
 * The QueryClient is created once and passed to QueryClientProvider
 * in the root layout. All React Query hooks share this configuration.
 */

import { QueryClient } from "@tanstack/react-query";

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Data stays fresh for 2 minutes before React Query refetches
        staleTime: 2 * 60 * 1000,

        // Keep unused data in cache for 5 minutes
        gcTime: 5 * 60 * 1000,

        // Retry failed requests up to 2 times
        retry: 2,

        // Wait 1 second before first retry, 2 seconds before second
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),

        // Refetch when browser window regains focus
        refetchOnWindowFocus: false,

        // Do not refetch on reconnect by default (user can manually refresh)
        refetchOnReconnect: true,
      },
      mutations: {
        // Retry mutations once on failure
        retry: 1,
      },
    },
  });
}