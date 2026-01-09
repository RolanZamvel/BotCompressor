import { useEffect, useState, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useToast } from '@/hooks/use-toast';

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
  const { toast } = useToast();

  const showToast = (title: string, description: string, variant: 'default' | 'destructive' = 'default') => {
    toast({
      title,
      description,
      variant,
    });
  };

  const refreshStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/bot/status');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to refresh status:', error);
      const errorMessage = error instanceof Error ? error.message : 'Error al conectar con el bot service';
      showToast(
        'Error al actualizar estado',
        errorMessage,
        'destructive'
      );
      setStatus(prev => ({ ...prev, status: 'error', error: errorMessage }));
    }
  }, [toast]);

  const startBot = useCallback(async () => {
    try {
      showToast('Iniciando bot...', 'El bot se está iniciando', 'default');
      setStatus(prev => ({ ...prev, status: 'starting', error: undefined }));

      const response = await fetch('/api/bot/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.success) {
        showToast('Bot iniciado correctamente', 'El bot se está iniciando', 'default');
        setTimeout(refreshStatus, 2000);
      } else {
        throw new Error(data.error || 'Error desconocido al iniciar el bot');
      }
      return data;
    } catch (error) {
      console.error('Failed to start bot:', error);
      const errorMessage = error instanceof Error ? error.message : 'Error al iniciar el bot';
      setStatus(prev => ({ ...prev, status: 'error', error: errorMessage }));
      showToast(
        'Error al iniciar bot',
        errorMessage,
        'destructive'
      );
      throw error;
    }
  }, [refreshStatus, toast]);

  const stopBot = useCallback(async () => {
    try {
      showToast('Deteniendo bot...', 'El bot se está deteniendo', 'default');
      setStatus(prev => ({ ...prev, status: 'stopped', error: undefined }));

      const response = await fetch('/api/bot/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.success) {
        showToast('Bot detenido correctamente', 'El bot se ha detenido', 'default');
        setTimeout(refreshStatus, 2000);
      } else {
        throw new Error(data.error || 'Error desconocido al detener el bot');
      }
      return data;
    } catch (error) {
      console.error('Failed to stop bot:', error);
      const errorMessage = error instanceof Error ? error.message : 'Error al detener el bot';
      setStatus(prev => ({ ...prev, status: 'error', error: errorMessage }));
      showToast(
        'Error al detener bot',
        errorMessage,
        'destructive'
      );
      throw error;
    }
  }, [refreshStatus, toast]);

  const restartBot = useCallback(async () => {
    try {
      showToast('Reiniciando bot...', 'El bot se está reiniciando', 'default');
      setStatus(prev => ({ ...prev, status: 'starting', error: undefined }));

      const response = await fetch('/api/bot/restart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.success) {
        showToast('Bot reiniciado correctamente', 'El bot se está reiniciando', 'default');
        setTimeout(refreshStatus, 3000);
      } else {
        throw new Error(data.error || 'Error desconocido al reiniciar el bot');
      }
      return data;
    } catch (error) {
      console.error('Failed to restart bot:', error);
      const errorMessage = error instanceof Error ? error.message : 'Error al reiniciar el bot';
      setStatus(prev => ({ ...prev, status: 'error', error: errorMessage }));
      showToast(
        'Error al reiniciar bot',
        errorMessage,
        'destructive'
      );
      throw error;
    }
  }, [refreshStatus, toast]);

  useEffect(() => {
    // Load initial status
    refreshStatus();

    // Load initial logs
    fetch('/api/bot/logs')
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        if (data.logs) {
          setLogs(data.logs.map((log: any) => {
            // Handle both string logs (from API) and object logs (from WebSocket)
            if (typeof log === 'string') {
              const [timestamp, type, ...message] = log.split('] ');
              const timestampStr = timestamp.replace('[', '').trim();

              // Validar timestamp válido antes de usarlo
              const isValidTimestamp = (ts: string) => {
                try {
                  const date = new Date(ts);
                  return !isNaN(date.getTime());
                } catch {
                  return false;
                }
              };

              // Usar timestamp si es válido, sino usar hora actual
              const finalTimestamp = isValidTimestamp(timestampStr)
                ? timestampStr
                : new Date().toISOString();

              return {
                message: message.join('] ').trim(),
                type: type.replace('[', '').toLowerCase() as 'info' | 'error' | 'success',
                timestamp: finalTimestamp
              };
            } else {
              return log as LogEntry;
            }
          }));
        }
      })
      .catch(error => {
        console.error('Failed to load logs:', error);
        showToast(
          'Error al cargar logs',
          'No se pudieron cargar los logs del bot',
          'destructive'
        );
      });

    // Setup WebSocket connection
    if (typeof window !== 'undefined' && !socketRef.current) {
      const socket = io('/?XTransformPort=3002');

      socket.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        showToast(
          'Conexión establecida',
          'Conectado al bot service en tiempo real',
          'default'
        );
      });

      socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        showToast(
          'Conexión perdida',
          'Se ha perdido la conexión con el bot service',
          'destructive'
        );
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

      socket.on('connect_error', (error: Error) => {
        console.error('WebSocket connection error:', error);
        setIsConnected(false);
        showToast(
          'Error de conexión WebSocket',
          error.message || 'No se pudo conectar al bot service',
          'destructive'
        );
      });

      socketRef.current = socket;
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, [refreshStatus, toast]);

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
