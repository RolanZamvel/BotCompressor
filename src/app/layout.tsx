import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { SessionProvider } from "@/components/auth/session-provider";
import { getServerSession } from "@/lib/auth";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "BotCompressor Dashboard - Telegram Bot Monitor",
  description: "Monitor and control your BotCompressor Telegram bot from a modern web dashboard.",
  keywords: ["BotCompressor", "Telegram", "Bot", "Dashboard", "Next.js"],
  authors: [{ name: "BotCompressor Team" }],
  icons: {
    icon: "/logo.svg",
  },
  openGraph: {
    title: "BotCompressor Dashboard",
    description: "Monitor and control your BotCompressor Telegram bot from a modern web dashboard",
    url: "https://github.com/RolanZamvel/BotCompressor",
    siteName: "BotCompressor",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "BotCompressor Dashboard",
    description: "Monitor and control your BotCompressor Telegram bot from a modern web dashboard",
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await getServerSession();

  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        <SessionProvider session={session}>
          {children}
          <Toaster />
        </SessionProvider>
      </body>
    </html>
  );
}
