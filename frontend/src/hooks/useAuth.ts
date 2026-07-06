/**
 * useAuth hook for PRISM.
 *
 * Provides access to the current authenticated user and auth actions.
 * Must be used within the AuthProvider component tree.
 *
 * Usage:
 *   const { user, loading, signInWithGoogle, signOut } = useAuth();
 */

"use client";

import { useContext } from "react";
import { AuthContext } from "@/components/layout/AuthProvider";

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}