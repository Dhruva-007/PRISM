/**
 * React Query provider for PRISM.
 *
 * Wraps the application with the QueryClientProvider so all
 * components can use useQuery, useMutation, etc.
 *
 * Must be a client component because QueryClient is browser-side.
 */

"use client";

import { useState, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { createQueryClient } from "@/lib/query-client";

interface QueryProviderProps {
  children: ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  const [queryClient] = useState(() => createQueryClient());

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}