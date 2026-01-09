'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Play, Square, RefreshCw, Activity } from 'lucide-react';
import { useBotMonitor } from '@/hooks/useBotMonitor';

interface StatusCardProps {
  className?: string;
}

export function StatusCard({ className }: StatusCardProps) {
  const { status, startBot, stopBot, restartBot, refreshStatus } = useBotMonitor();

  const getStatusColor = () => {
    switch (status.status) {
      case 'running':
        return 'bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30';
      case 'starting':
        return 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 border-yellow-500/30';
      case 'stopped':
        return 'bg-gray-500/15 text-gray-700 dark:text-gray-400 border-gray-500/30';
      case 'error':
        return 'bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/30';
      default:
        return 'bg-gray-500/15 text-gray-700 dark:text-gray-400 border-gray-500/30';
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case 'running':
        return 'Running';
      case 'starting':
        return 'Starting...';
      case 'stopped':
        return 'Stopped';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const formatUptime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            <CardTitle>Bot Status</CardTitle>
          </div>
          <Badge className={getStatusColor()}>
            {getStatusText()}
          </Badge>
        </div>
        <CardDescription>Monitor and control the Telegram bot</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {status.status === 'running' && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Process ID</p>
                <p className="text-2xl font-bold">{status.pid || 'N/A'}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Uptime</p>
                <p className="text-2xl font-bold">{formatUptime(status.uptime)}</p>
              </div>
            </div>
          )}

          {status.error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-700 dark:text-red-400">{status.error}</p>
            </div>
          )}

          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <Button
                onClick={startBot}
                disabled={status.status === 'running' || status.status === 'starting'}
                className="flex-1"
                variant="default"
              >
                <Play className="h-4 w-4 mr-2" />
                Start
              </Button>
              <Button
                onClick={stopBot}
                disabled={status.status === 'stopped' || status.status === 'starting'}
                className="flex-1"
                variant="destructive"
              >
                <Square className="h-4 w-4 mr-2" />
                Stop
              </Button>
            </div>
            <Button
              onClick={restartBot}
              disabled={status.status === 'starting'}
              variant="outline"
              className="w-full"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Restart Bot
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
