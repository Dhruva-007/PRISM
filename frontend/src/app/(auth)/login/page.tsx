/**
 * PRISM Login Page.
 *
 * The authentication entry point for PRISM.
 * Provides Google Sign-In via Firebase Authentication.
 *
 * Design: clean, professional, minimal.
 * Left panel: product information and value proposition.
 * Right panel: sign-in form.
 */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { AlertCircle, ArrowRight, Shield, Zap, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { ROUTES } from "@/constants/routes";
import { LoadingScreen } from "@/components/shared/LoadingScreen";

const features = [
  {
    icon: Zap,
    title: "Real-time Intelligence",
    description: "Continuous analysis of air quality, weather, and health data",
  },
  {
    icon: BarChart3,
    title: "Scenario Simulation",
    description: "Evaluate every intervention before committing resources",
  },
  {
    icon: Shield,
    title: "Evidence-based Decisions",
    description: "Every recommendation explained with supporting data",
  },
];

export default function LoginPage() {
  const { user, loading, error, signInWithGoogle } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.replace(ROUTES.OVERVIEW);
    }
  }, [user, loading, router]);

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left panel — product information */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 bg-stone-50 border-r border-border p-12">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-accent flex items-center justify-center">
            <span className="text-white font-bold text-base">P</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground tracking-tight">
              PRISM
            </p>
            <p className="text-xs text-muted-foreground">
              Decision Intelligence System
            </p>
          </div>
        </div>

        <div className="space-y-8">
          <div className="space-y-3">
            <h1 className="text-3xl font-semibold text-foreground tracking-tight leading-tight">
              Helping communities choose the best future, not just predict it.
            </h1>
            <p className="text-base text-muted-foreground leading-relaxed">
              PRISM transforms multimodal community data into explainable,
              simulated, and optimized decisions — enabling communities to act
              before small problems become major crises.
            </p>
          </div>

          <div className="space-y-4">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                  className="flex items-start gap-4"
                >
                  <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Icon className="w-4 h-4 text-accent" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {feature.title}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          India · Hyderabad · Delhi · Bangalore · Mumbai
        </p>
      </div>

      {/* Right panel — sign in */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="w-full max-w-sm space-y-8"
        >
          {/* Mobile logo */}
          <div className="flex items-center gap-3 lg:hidden">
            <div className="w-9 h-9 rounded-xl bg-accent flex items-center justify-center">
              <span className="text-white font-bold text-base">P</span>
            </div>
            <p className="text-sm font-semibold text-foreground">PRISM</p>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-semibold text-foreground tracking-tight">
              Sign in to PRISM
            </h2>
            <p className="text-sm text-muted-foreground">
              Use your Google account to access the Decision Intelligence
              System.
            </p>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3 p-3 rounded-lg bg-red-50 border border-red-200"
            >
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-red-700">{error}</p>
            </motion.div>
          )}

          <div className="space-y-3">
            <Button
              onClick={signInWithGoogle}
              disabled={loading}
              className="w-full h-10 bg-foreground hover:bg-foreground/90 text-background text-sm font-medium"
            >
              <svg
                className="w-4 h-4 mr-2"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Continue with Google
            </Button>
          </div>

          <div className="flex items-center gap-2 p-3 rounded-lg bg-stone-50 border border-border">
            <Shield className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
            <p className="text-xs text-muted-foreground">
              Secured by Firebase Authentication. Your data is never shared.
            </p>
          </div>

          <div className="flex items-center justify-center">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              Decision Intelligence Platform
              <ArrowRight className="w-3 h-3" />
              Community Health MVP
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}