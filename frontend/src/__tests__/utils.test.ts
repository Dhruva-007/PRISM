/**
 * Tests for PRISM frontend utility functions.
 */

import { cn, capitalize, clamp, formatDate } from "@/lib/utils";

describe("cn — Tailwind class merging", () => {
  test("merges simple class strings", () => {
    expect(cn("px-4", "py-2")).toBe("px-4 py-2");
  });

  test("handles conditional classes", () => {
    expect(cn("base", true && "active", false && "inactive")).toBe(
      "base active"
    );
  });

  test("resolves Tailwind conflicts correctly", () => {
    expect(cn("px-4", "px-8")).toBe("px-8");
  });

  test("handles undefined and null values", () => {
    expect(cn("base", undefined, null as unknown as string)).toBe("base");
  });

  test("handles empty string", () => {
    expect(cn("")).toBe("");
  });

  test("merges multiple conflicting classes", () => {
    expect(cn("text-sm text-lg")).toBe("text-lg");
  });
});

describe("capitalize", () => {
  test("capitalizes first letter", () => {
    expect(capitalize("hello")).toBe("Hello");
  });

  test("lowercases rest of string", () => {
    expect(capitalize("hELLO")).toBe("Hello");
  });

  test("handles empty string", () => {
    expect(capitalize("")).toBe("");
  });

  test("handles single character", () => {
    expect(capitalize("a")).toBe("A");
  });

  test("handles already capitalized string", () => {
    expect(capitalize("Hello")).toBe("Hello");
  });
});

describe("clamp", () => {
  test("returns value within range unchanged", () => {
    expect(clamp(50, 0, 100)).toBe(50);
  });

  test("clamps value below minimum to minimum", () => {
    expect(clamp(-10, 0, 100)).toBe(0);
  });

  test("clamps value above maximum to maximum", () => {
    expect(clamp(150, 0, 100)).toBe(100);
  });

  test("handles value equal to minimum", () => {
    expect(clamp(0, 0, 100)).toBe(0);
  });

  test("handles value equal to maximum", () => {
    expect(clamp(100, 0, 100)).toBe(100);
  });

  test("handles negative ranges", () => {
    expect(clamp(-5, -10, -1)).toBe(-5);
  });
});

describe("formatDate", () => {
  test("formats date object correctly", () => {
    const date = new Date("2025-01-15T10:00:00Z");
    const result = formatDate(date);
    expect(result).toContain("2025");
    expect(result).toContain("Jan");
  });

  test("formats ISO string correctly", () => {
    const result = formatDate("2025-01-15T10:00:00Z");
    expect(result).toContain("2025");
  });

  test("accepts custom format pattern", () => {
    const date = new Date("2025-01-15");
    const result = formatDate(date, "yyyy");
    expect(result).toBe("2025");
  });
});