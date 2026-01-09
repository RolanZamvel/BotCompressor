'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, Download } from 'lucide-react';
import { useBotMonitor } from '@/hooks/useBotMonitor';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface LogViewerProps {
  className?: string;
}

export function LogViewer({ className }: LogViewerProps) {
  const { logs } = useBotMonitor();

  const getLogColor = (type: 'info' | 'error' | 'success') => {
    switch (type) {
      case 'error':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      case 'success':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      // Validar que la fecha sea válida
      if (isNaN(date.getTime())) {
        return new Date().toLocaleTimeString();
      }
      return date.toLocaleTimeString();
    } catch {
      // Si hay cualquier error, usar hora actual
      return new Date().toLocaleTimeString();
    }
  };

  const getLogType = (type: string) => {
    switch (type) {
      case 'error':
        return 'ERROR';
      case 'success':
        return 'SUCCESS';
      default:
        return 'INFO';
    }
  };

  const downloadLogs = () => {
    const logsText = logs.map(log =>
      `[${log.timestamp}] [${log.type.toUpperCase()}] ${log.message}`
    ).join('\n');

    const blob = new Blob([logsText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bot-logs-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            <CardTitle>Live Logs</CardTitle>
          </div>
          <Button
            onClick={downloadLogs}
            variant="outline"
            size="sm"
            disabled={logs.length === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
        <CardDescription>Real-time bot activity logs</CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-96 w-full rounded-md border p-4">
          <div className="font-mono text-sm space-y-2">
            {logs.length === 0 ? (
              <p className="text-muted-foreground">No logs available</p>
            ) : (
              logs.map((log, index) => (
                <div
                  key={index}
                  className={`p-2 rounded-lg ${getLogColor(log.type)}`}
                >
                  <div className="flex items-start gap-2">
                    <Badge variant="outline" className="text-xs shrink-0">
                      {getLogType(log.type)}
                    </Badge>
                    <span className="text-xs text-muted-foreground shrink-0">
                      {formatTimestamp(log.timestamp)}
                    </span>
                    <p className="text-xs break-all">{log.message}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
