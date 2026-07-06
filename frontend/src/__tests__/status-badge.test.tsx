/**
 * Tests for StatusBadge component.
 */

import "@testing-library/jest-dom";
import React from "react";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/components/shared/StatusBadge";

describe("StatusBadge — severity type", () => {
  test("renders 'Low' for severity low", () => {
    render(<StatusBadge type="severity" value="low" />);
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  test("renders 'Medium' for severity medium", () => {
    render(<StatusBadge type="severity" value="medium" />);
    expect(screen.getByText("Medium")).toBeInTheDocument();
  });

  test("renders 'High' for severity high", () => {
    render(<StatusBadge type="severity" value="high" />);
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  test("renders 'Critical' for severity critical", () => {
    render(<StatusBadge type="severity" value="critical" />);
    expect(screen.getByText("Critical")).toBeInTheDocument();
  });

  test("applies correct CSS class for critical", () => {
    const { container } = render(
      <StatusBadge type="severity" value="critical" />
    );
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("red");
  });

  test("applies correct CSS class for low", () => {
    const { container } = render(
      <StatusBadge type="severity" value="low" />
    );
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("emerald");
  });
});

describe("StatusBadge — status type", () => {
  test("renders 'Pending' for status pending", () => {
    render(<StatusBadge type="status" value="pending" />);
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  test("renders 'Analyzing' for status analyzing", () => {
    render(<StatusBadge type="status" value="analyzing" />);
    expect(screen.getByText("Analyzing")).toBeInTheDocument();
  });

  test("renders 'Complete' for status complete", () => {
    render(<StatusBadge type="status" value="complete" />);
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });

  test("renders 'Failed' for status failed", () => {
    render(<StatusBadge type="status" value="failed" />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  test("accepts custom className", () => {
    const { container } = render(
      <StatusBadge type="severity" value="low" className="custom-class" />
    );
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("custom-class");
  });
});