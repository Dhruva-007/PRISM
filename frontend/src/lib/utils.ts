/**
 * Shared utility functions for PRISM frontend.
 *
 * Contains:
 * - cn(): Tailwind class merging (required by shadcn/ui)
 * - formatDate(): Human-readable date formatting
 * - formatRelativeTime(): Relative time strings ("2 hours ago")
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow, format } from "date-fns";

/**
 * Merge Tailwind CSS classes with conflict resolution.
 *
 * Used by all shadcn/ui components and custom components
 * to safely combine conditional class strings.
 *
 * @example
 * cn("px-4 py-2", isActive && "bg-emerald-600", className)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a date as a human-readable string.
 *
 * @param date - Date object or ISO string
 * @param pattern - date-fns format pattern
 * @returns Formatted date string
 *
 * @example
 * formatDate(new Date()) // "Jan 15, 2025"
 */
export function formatDate(
  date: Date | string,
  pattern: string = "MMM d, yyyy"
): string {
  const dateObj = typeof date === "string" ? new Date(date) : date;
  return format(dateObj, pattern);
}

/**
 * Format a date as a relative time string.
 *
 * @param date - Date object or ISO string
 * @returns Relative time string
 *
 * @example
 * formatRelativeTime(twoHoursAgo) // "2 hours ago"
 */
export function formatRelativeTime(date: Date | string): string {
  const dateObj = typeof date === "string" ? new Date(date) : date;
  return formatDistanceToNow(dateObj, { addSuffix: true });
}

/**
 * Capitalize the first letter of a string.
 */
export function capitalize(str: string): string {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Clamp a number between min and max values.
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}