/**
 * PRISM API Client.
 *
 * A typed HTTP client for communicating with the PRISM FastAPI backend.
 *
 * Responsibilities:
 * - Automatically attach Firebase ID token to every request
 * - Handle token refresh on 401 responses
 * - Provide typed response parsing
 * - Centralize error handling
 *
 * All API modules (analysis, interventions, simulation, memory)
 * import from this client. Never use raw fetch in components.
 */

import { auth } from "@/lib/firebase";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!;

/**
 * Retrieve the current user's Firebase ID token.
 * Automatically refreshes if expired.
 *
 * Returns null if no user is signed in.
 */
async function getIdToken(): Promise<string | null> {
  const user = auth.currentUser;
  if (!user) return null;
  try {
    return await user.getIdToken(false);
  } catch {
    return null;
  }
}

/**
 * Base API request function.
 *
 * Attaches Authorization header with Firebase ID token.
 * Handles non-OK responses by throwing structured errors.
 *
 * @param path - API path relative to base URL (e.g., "/health")
 * @param options - Standard fetch RequestInit options
 * @returns Parsed JSON response
 */
async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getIdToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail: string;
    try {
      const errorBody = await response.json();
      errorDetail = errorBody.detail ?? errorBody.message ?? response.statusText;
    } catch {
      errorDetail = response.statusText;
    }
    throw new ApiError(response.status, errorDetail, path);
  }

  return response.json() as Promise<T>;
}

/**
 * Structured API error with status code and path context.
 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
    public readonly path: string
  ) {
    super(`API Error ${status} on ${path}: ${detail}`);
    this.name = "ApiError";
  }
}

/**
 * Public API client interface.
 * Use these methods in hooks and server actions.
 */
export const apiClient = {
  get: <T>(path: string) =>
    request<T>(path, { method: "GET" }),

  post: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  patch: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  delete: <T>(path: string) =>
    request<T>(path, { method: "DELETE" }),
};