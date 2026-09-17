import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { SessionProvider } from "@/components/session";
import { Header } from "@/components/ui";

export const metadata: Metadata = {
  title: "Turio",
  description: "AI agent for resume-based job matching and intelligent job application.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body><SessionProvider><a className="skip-link" href="#main-content">Skip to content</a><Header /><div id="main-content">{children}</div><footer className="site-footer"><span>Turio · A little clarity. A next step.</span><span>Your career. Your decisions.</span></footer></SessionProvider></body>
    </html>
  );
}
