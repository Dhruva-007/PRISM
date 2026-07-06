/**
 * TopBar component for PRISM dashboard.
 *
 * Displays the current page title, city selector, and action buttons.
 */

"use client";

import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Activity, BrainCircuit } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CitySelector } from "@/components/layout/CitySelector";
import { NAV_ITEMS } from "@/constants/navigation";
import { ROUTES } from "@/constants/routes";

function usePageTitle(): { title: string; description: string } {
  const pathname = usePathname();
  const navItem = NAV_ITEMS.find(
    (item) =>
      pathname === item.href || pathname.startsWith(item.href + "/")
  );
  if (navItem) {
    return { title: navItem.label, description: navItem.description };
  }
  return { title: "PRISM", description: "Decision Intelligence System" };
}

export function TopBar() {
  const { title, description } = usePageTitle();
  const router = useRouter();

  return (
    <header className="h-14 border-b border-border bg-background/95 backdrop-blur-sm flex items-center justify-between px-6 sticky top-0 z-30">
      <motion.div
        key={title}
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="flex flex-col"
      >
        <h1 className="text-sm font-semibold text-foreground leading-none">
          {title}
        </h1>
        <p className="text-xs text-muted-foreground leading-none mt-0.5">
          {description}
        </p>
      </motion.div>

      <div className="flex items-center gap-2">
        <CitySelector />
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-emerald-50 border border-emerald-200">
          <Activity className="w-3 h-3 text-emerald-600" />
          <span className="text-xs text-emerald-700 font-medium">Live</span>
        </div>
        <Button
          size="sm"
          className="bg-accent hover:bg-accent/90 text-white text-xs h-8 px-3"
          onClick={() => router.push(ROUTES.ANALYSIS)}
        >
          <BrainCircuit className="w-3.5 h-3.5 mr-1.5" />
          Run Analysis
        </Button>
      </div>
    </header>
  );
}