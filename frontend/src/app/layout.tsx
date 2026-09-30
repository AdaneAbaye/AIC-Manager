import type { Metadata } from "next";
import { Frank_Ruhl_Libre, IBM_Plex_Mono, IBM_Plex_Sans_Hebrew } from "next/font/google";
import "./globals.css";

const plexHebrew = IBM_Plex_Sans_Hebrew({
  subsets: ["latin", "hebrew"],
  weight: ["400", "500", "700"],
  variable: "--font-sans",
  display: "swap",
});

const frankRuhl = Frank_Ruhl_Libre({
  subsets: ["latin", "hebrew"],
  weight: ["500", "700", "900"],
  variable: "--font-display",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AIC-Manager | ועדת ההשקעות האוטונומית",
  description: "כלי מחקר השקעות מבוסס סוכנים — Autonomous Investment Committee",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="he"
      dir="rtl"
      className={`${plexHebrew.variable} ${frankRuhl.variable} ${plexMono.variable}`}
    >
      <body className="min-h-screen bg-background font-sans text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
