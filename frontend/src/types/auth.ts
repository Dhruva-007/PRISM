/**
 * Authentication type definitions for PRISM.
 *
 * These types describe the authenticated user and auth state
 * used throughout the application.
 */

export interface PRISMUser {
  uid: string;
  email: string;
  displayName: string;
  photoURL: string | null;
  role: UserRole;
}

export type UserRole = "analyst" | "decision_maker" | "admin";

export interface AuthState {
  user: PRISMUser | null;
  loading: boolean;
  error: string | null;
}