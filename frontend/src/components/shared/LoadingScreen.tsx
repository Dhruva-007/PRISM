/**
 * LoadingScreen component for PRISM.
 *
 * Shown while Firebase Auth is determining the initial auth state.
 * Prevents the login page from flashing before we know if
 * the user is already signed in.
 */

"use client";

import { motion } from "framer-motion";

export function LoadingScreen() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="flex flex-col items-center gap-6"
      >
        <div className="relative">
          <div className="w-14 h-14 rounded-2xl bg-accent flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-2xl tracking-tight">
              P
            </span>
          </div>
          <motion.div
            className="absolute inset-0 rounded-2xl border-2 border-accent"
            animate={{ opacity: [1, 0, 1] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>
        <div className="flex flex-col items-center gap-2">
          <p className="text-sm font-medium text-foreground">PRISM</p>
          <p className="text-xs text-muted-foreground">
            Initializing system...
          </p>
        </div>
      </motion.div>
    </div>
  );
}