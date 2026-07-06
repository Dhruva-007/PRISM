/**
 * Sidebar navigation component for PRISM.
 *
 * The primary navigation for the dashboard shell.
 * Shows the PRISM logo, navigation items with active states,
 * and the signed-in user's avatar with a sign-out option.
 *
 * Design: minimal, professional, Linear-inspired.
 * No gradients, no glowing borders, no neon colors.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  BrainCircuit,
  Lightbulb,
  FlaskConical,
  BookOpen,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { NAV_ITEMS } from "@/constants/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const iconMap = {
  LayoutDashboard,
  BrainCircuit,
  Lightbulb,
  FlaskConical,
  BookOpen,
} as const;

type IconName = keyof typeof iconMap;

export function Sidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  const userInitials = user?.displayName
    ? user.displayName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-sidebar border-r border-sidebar-border flex flex-col z-40">
      {/* Logo */}
      <div className="h-14 flex items-center px-5 border-b border-sidebar-border">
        <Link href="/overview" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center flex-shrink-0 group-hover:opacity-90 transition-opacity">
            <span className="text-white font-bold text-sm">P</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-foreground tracking-tight leading-none">
              PRISM
            </span>
            <span className="text-[10px] text-muted-foreground leading-none mt-0.5">
              Decision Intelligence
            </span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 mb-3">
          Workspace
        </p>
        {NAV_ITEMS.map((item) => {
          const Icon = iconMap[item.icon as IconName];
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "relative flex items-center gap-3 px-2 py-2 rounded-md text-sm transition-all duration-150 group",
                isActive
                  ? "bg-accent/10 text-accent font-medium"
                  : "text-sidebar-foreground hover:bg-stone-100 hover:text-foreground"
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute inset-0 bg-accent/10 rounded-md"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.4 }}
                />
              )}
              <Icon
                className={cn(
                  "w-4 h-4 flex-shrink-0 relative z-10",
                  isActive ? "text-accent" : "text-muted-foreground group-hover:text-foreground"
                )}
              />
              <div className="flex flex-col relative z-10">
                <span className="leading-none">{item.label}</span>
                <span className="text-[10px] text-muted-foreground leading-none mt-0.5 font-normal">
                  {item.description}
                </span>
              </div>
              {isActive && (
                <ChevronRight className="w-3 h-3 text-accent ml-auto relative z-10" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="px-3 py-3 border-t border-sidebar-border">
        <DropdownMenu>
          <DropdownMenuTrigger className="w-full flex items-center gap-3 px-2 py-2 rounded-md hover:bg-stone-100 transition-colors duration-150 group outline-none">
            <Avatar className="w-7 h-7 flex-shrink-0">
              <AvatarImage
                src={user?.photoURL ?? undefined}
                alt={user?.displayName ?? "User"}
              />
              <AvatarFallback className="text-xs bg-stone-200 text-stone-600 font-medium">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col text-left min-w-0">
              <span className="text-xs font-medium text-foreground truncate leading-none">
                {user?.displayName ?? "User"}
              </span>
              <span className="text-[10px] text-muted-foreground truncate leading-none mt-0.5">
                {user?.email ?? ""}
              </span>
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            side="top"
            align="start"
            className="w-52 mb-1"
          >
            <div className="px-2 py-1.5">
              <p className="text-xs font-medium text-foreground">
                {user?.displayName}
              </p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={signOut}
              className="text-red-600 focus:text-red-600 focus:bg-red-50 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5 mr-2" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  );
}