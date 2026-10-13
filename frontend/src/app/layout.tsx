import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense, type ReactNode } from "react";
import { AppShell } from "@/components/layout/app-shell";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "AgriSage AI | Evidence Before Advice",
    template: "%s | AgriSage AI",
  },
  description:
    "Climate smart advisory intelligence for agricultural extension officers, built around evidence before advice.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full"><a href="#main-content" className="sr-only z-50 rounded-lg bg-surface px-4 py-3 text-sm font-semibold text-forest focus:not-sr-only focus:fixed focus:left-4 focus:top-4">Skip to main content</a><Suspense fallback={<div className="min-h-screen bg-background">{children}</div>}><AppShell>{children}</AppShell></Suspense></body>
    </html>
  );
}
