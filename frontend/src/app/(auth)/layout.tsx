/**
 * Auth route group layout.
 *
 * Minimal layout for authentication pages.
 * No sidebar, no topbar.
 */

import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}