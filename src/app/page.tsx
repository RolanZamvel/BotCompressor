'use client';

import { StatusCard } from '@/components/bot-dashboard/StatusCard';
import { LogViewer } from '@/components/bot-dashboard/LogViewer';
import { StatsCard } from '@/components/bot-dashboard/StatsCard';
import { InfoCard } from '@/components/bot-dashboard/InfoCard';
import { Activity } from 'lucide-react';

export default function BotDashboard() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-muted/20 to-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Activity className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">BotCompressor</h1>
              <p className="text-sm text-muted-foreground">Telegram Bot Control Dashboard</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Top Row - Status and Stats */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <StatusCard />
            <StatsCard />
          </div>

          {/* Middle Row - Info */}
          <InfoCard />

          {/* Bottom Row - Logs */}
          <LogViewer />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 mt-auto">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <p>© 2024 BotCompressor Dashboard. All rights reserved.</p>
            <p>Made with ❤️ for easy bot management</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
