/**
 * PRISM Root Layout.
 *
 * Wraps the entire application with all providers:
 * - QueryProvider: React Query for data fetching
 * - AuthProvider: Firebase Authentication state
 * - CityProvider: Selected city state
 */

import type { Metadata } from "next";
import { QueryProvider } from "@/components/layout/QueryProvider";
import { AuthProvider } from "@/components/layout/AuthProvider";
import { CityProvider } from "@/hooks/useCity";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    template: "%s | PRISM",
    default: "PRISM — Decision Intelligence System",
  },
  description:
    "AI-powered Decision Intelligence System that transforms community data into explainable, simulated, and optimized decisions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <link
          rel="stylesheet"
          href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css"
        />
      </head>
      <body className="font-sans antialiased">
        <QueryProvider>
          <AuthProvider>
            <CityProvider>
              {children}
            </CityProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}