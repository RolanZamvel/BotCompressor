import { useEffect, useState, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

interface BotStatus {
  status: 'stopped' | 'starting' | 'running' | 'error';
  pid: number | null;
  uptime: number;
  error?: string;
}

interface LogEntry {
  message: string;
  type: 'info' | 'error' | 'success';
  timestamp: string;
}

interface UseBotMonitorReturn {
  status: BotStatus;
  logs: LogEntry[];
  isConnected: boolean;
  refreshStatus: () => Promise<void>;
  startBot: () => Promise<void>;
  stopBot: () => Promise<void>;
  restartBot: () => Promise<void>;
}

export function useBotMonitor(): UseBotMonitorReturn {
  const [status, setStatus] = useState<BotStatus>({
    status: 'stopped',
    pid: null,
    uptime: 0
  });
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  const refreshStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/bot/status');
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to refresh status:', error);
    }
  }, []);

  const startBot = useCallback(async () => {
    try {
      const response = await fetch('/api/bot/start', { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        setStatus(prev => ({ ...prev, status: 'starting' }));
        setTimeout(refreshStatus, 2000);
      }
      return data;
    } catch (error) {
      console.error('Failed to start bot:', error);
      throw error;
    }
  }, [refreshStatus]);

  const stopBot = useCallback(async () => {
    try {
      const response = await fetch('/api/bot/stop', { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        setStatus(prev => ({ ...prev, status: 'stopped' }));
        setTimeout(refreshStatus, 2000);
      }
      return data;
    } catch (error) {
      console.error('Failed to stop bot:', error);
      throw error;
    }
  }, [refreshStatus]);

  const restartBot = useCallback(async () => {
    try {
      const response = await fetch('/api/bot/restart', { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        setStatus(prev => ({ ...prev, status: 'starting' }));
        setTimeout(refreshStatus, 3000);
      }
      return data;
    } catch (error) {
      console.error('Failed to restart bot:', error);
      throw error;
    }
  }, [refreshStatus]);

  useEffect(() => {
    // Load initial status
    refreshStatus();

    // Load initial logs
    fetch('/api/bot/logs')
      .then(res => res.json())
      .then(data => {
        if (data.logs) {
          setLogs(data.logs.map((log: any) => {
            // Handle both string logs (from API) and object logs (from WebSocket)
            if (typeof log === 'string') {
              const [timestamp, type, ...message] = log.split('] ');
              const timestampStr = timestamp.replace('[', '').trim();
              return {
                message: message.join('] ').trim(),
                type: type.replace('[', '').toLowerCase() as 'info' | 'error' | 'success',
                timestamp: timestampStr || new Date().toISOString()
              };
            } else {
              return log as LogEntry;
            }
          }));
        }
      })
      .catch(console.error);

    // Setup WebSocket connection
    if (typeof window !== 'undefined' && !socketRef.current) {
      const socket = io('/?XTransformPort=3002');

      socket.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      });

      socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      });

      socket.on('status', (data: BotStatus) => {
        setStatus(data);
      });

      socket.on('log', (logEntry: LogEntry) => {
        setLogs(prev => [...prev.slice(-199), logEntry]);
      });

      socket.on('logs', (data: { logs: LogEntry[] }) => {
        setLogs(data.logs);
      });

      socketRef.current = socket;
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, [refreshStatus]);

  return {
    status,
    logs,
    isConnected,
    refreshStatus,
    startBot,
    stopBot,
    restartBot
  };
}
