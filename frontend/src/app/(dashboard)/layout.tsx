/**
 * Dashboard route group layout.
 *
 * Wraps all protected dashboard pages with:
 * - Authentication guard (redirects to login if not signed in)
 * - Sidebar navigation
 * - Top bar
 * - Main content area
 *
 * This layout only renders after auth state is confirmed.
 */

"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { useAuth } from "@/hooks/useAuth";
import { ROUTES } from "@/constants/routes";

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace(ROUTES.LOGIN);
    }
  }, [user, loading, router]);

  if (loading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className="ml-60 flex flex-col min-h-screen">
        <TopBar />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}