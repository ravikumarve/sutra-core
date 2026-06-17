import type { Metadata } from "next";
import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const jakartaSans = Plus_Jakarta_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["300", "400", "500", "700"],
});

export const metadata: Metadata = {
  title: "SUTRA Core | Headless Multi-Agent ERP Engine",
  description:
    "Voice. Text. Hinglish. Zero training. SUTRA Core transforms colloquial chat input into clean, synchronized enterprise ledger parameters on a single-node VPS.",
  openGraph: {
    title: "SUTRA Core | Headless Multi-Agent ERP Engine",
    description:
      "The headless ERP for Bharat. AI-powered WhatsApp ERP for Indian MSMEs.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${jakartaSans.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-dvh flex flex-col">{children}</body>
    </html>
  );
}
