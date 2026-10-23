import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { SessionProvider } from "@/components/session";
import { Header } from "@/components/ui";
import { Atmosphere } from "@/components/atmosphere";
import { MotionProvider } from "@/components/route-motion";
import { THEME_BOOTSTRAP } from "@/lib/theme";

export const metadata: Metadata = {
  title: "Turio",
  description: "Search jobs, reuse your resume and track your applications with Turio.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head><script id="turio-theme" dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} /></head>
      <body>
        <Atmosphere />
        <SessionProvider><MotionProvider><a className="skip-link" href="#main-content">Skip to content</a><Header /><div id="main-content">{children}</div><footer className="site-footer"><span className="footer-wordmark">Turio</span><span>Review before submitting.</span></footer></MotionProvider></SessionProvider>
      </body>
    </html>
  );
}
