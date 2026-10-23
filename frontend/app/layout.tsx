import type { Metadata, Viewport } from "next";
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

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script id="turio-theme" dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@500;600&family=Inter:wght@400;500;600&display=swap"
        />
      </head>
      <body>
        <Atmosphere />
        <SessionProvider><MotionProvider><a className="skip-link" href="#main-content">Skip to content</a><Header /><div id="main-content">{children}</div><footer className="site-footer"><span className="footer-wordmark">Turio</span><span>Review before submitting.</span></footer></MotionProvider></SessionProvider>
      </body>
    </html>
  );
}
