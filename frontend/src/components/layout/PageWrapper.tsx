/**
 * PageWrapper component for PRISM.
 *
 * Wraps every dashboard page with consistent padding,
 * max-width constraints, and entrance animation.
 *
 * Usage:
 *   <PageWrapper>
 *     <YourPageContent />
 *   </PageWrapper>
 */

"use client";

import { motion } from "framer-motion";
import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PageWrapperProps {
  children: ReactNode;
  className?: string;
}

export function PageWrapper({ children, className }: PageWrapperProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn("p-6 max-w-7xl mx-auto w-full", className)}
    >
      {children}
    </motion.div>
  );
}