import type { Metadata } from "next";
import { Geist, Geist_Mono, Instrument_Serif } from "next/font/google";
import { AppShell } from "@/components/app-shell";
import { ClerkProvider } from "@clerk/nextjs";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const instrument = Instrument_Serif({
  variable: "--font-instrument",
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: {
    default: "ROLEWISE",
    template: "%s · ROLEWISE",
  },
  description:
    "Role-wise interview prep for SDE 1 through Principal — coding, LLD, HLD, and behavioral, with structured problem breakdowns and a trend analyzer.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html
        lang="en"
        className={`${geistSans.variable} ${geistMono.variable} ${instrument.variable} h-full antialiased`}
        suppressHydrationWarning
      >
        <body className="flex min-h-full flex-col bg-rw-bg text-rw-ink overflow-x-hidden">
          <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <AppShell>{children}</AppShell>
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
