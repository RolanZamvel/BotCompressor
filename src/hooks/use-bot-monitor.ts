"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { io, Socket } from "socket.io-client";
import { BotState, LogEntry, BotStats, Activity, LogLevel } from "@/types";

interface UseBotMonitorOptions {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export function useBotMonitor(options: UseBotMonitorOptions = {}) {
  const {
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectDelay = 3000,
  } = options;

  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<BotState['status']>('stopped');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [stats, setStats] = useState<BotStats>({
    processedToday: 0,
    processedTodayIncrease: 0,
    uptime: "0m 0s",
    totalProcessed: 0,
    averageCompressionTime: 0,
    successRate: 0,
    compressionMetrics: [],
    resourceUsage: [],
  });
  const [activities, setActivities] = useState<Activity[]>([]);

  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    if (socket?.connected) return;

    const newSocket = io(process.env.NEXT_PUBLIC_BOT_SERVICE_URL || "http://localhost:3002", {
      transports: ["websocket"],
      upgrade: false,
      rememberUpgrade: false,
      timeout: 5000,
    });

    newSocket.on("connect", () => {
      console.log("Connected to bot service");
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
      
      // Request initial data
      newSocket.emit("get_status");
      newSocket.emit("get_logs", { limit: 100 });
    });

    newSocket.on("disconnect", () => {
      console.log("Disconnected from bot service");
      setIsConnected(false);
      
      // Attempt to reconnect
      if (reconnectAttemptsRef.current < reconnectAttempts) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          console.log(`Reconnection attempt ${reconnectAttemptsRef.current}`);
          connect();
        }, reconnectDelay);
      }
    });

    newSocket.on("connect_error", (error) => {
      console.error("Connection error:", error);
      setIsConnected(false);
    });

    // Bot status events
    newSocket.on("status", (data: BotState) => {
      setStatus(data.status);
      updateStats(data);
    });

    // Log events
    newSocket.on("log", (data: any) => {
      const logEntry: LogEntry = {
        id: `${data.timestamp}-${Math.random()}`,
        timestamp: new Date(data.timestamp),
        level: data.type as LogLevel,
        message: data.message,
        source: "bot",
      };
      
      setLogs(prev => [logEntry, ...prev.slice(0, 999)]); // Keep last 1000 logs
      processActivity(logEntry);
    });

    newSocket.on("logs", (data: LogEntry[]) => {
      setLogs(data.reverse());
    });

    setSocket(newSocket);
  }, [socket, reconnectAttempts, reconnectDelay]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    socket?.disconnect();
    setSocket(null);
    setIsConnected(false);
  }, [socket]);

  const startBot = useCallback(async () => {
    try {
      const response = await fetch("/api/bot/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      
      if (!response.ok) {
        throw new Error("Failed to start bot");
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error starting bot:", error);
      throw error;
    }
  }, []);

  const stopBot = useCallback(async () => {
    try {
      const response = await fetch("/api/bot/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      
      if (!response.ok) {
        throw new Error("Failed to stop bot");
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error stopping bot:", error);
      throw error;
    }
  }, []);

  const restartBot = useCallback(async () => {
    try {
      const response = await fetch("/api/bot/restart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      
      if (!response.ok) {
        throw new Error("Failed to restart bot");
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error restarting bot:", error);
      throw error;
    }
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  const exportLogs = useCallback(() => {
    const logsText = logs
      .map(log => `[${log.timestamp.toISOString()}] [${log.level.toUpperCase()}] ${log.message}`)
      .join("\n");
    
    const blob = new Blob([logsText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bot-logs-${new Date().toISOString().split("T")[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [logs]);

  const updateStats = useCallback((botState: BotState) => {
    // Simulate stats updates - in real app, this would come from the bot
    setStats(prev => ({
      ...prev,
      uptime: formatUptime(botState.uptime),
    }));
  }, []);

  const processActivity = useCallback((log: LogEntry) => {
    // Convert logs to activities for the feed
    if (log.level === "error") {
      const activity: Activity = {
        id: log.id,
        type: "error",
        title: "Error del Sistema",
        description: log.message,
        timestamp: log.timestamp,
      };
      setActivities(prev => [activity, ...prev.slice(0, 49)]);
    } else if (log.message.includes("compressed") || log.message.includes("descargado")) {
      const activity: Activity = {
        id: log.id,
        type: log.message.includes("compressed") ? "compression" : "download",
        title: log.message.includes("compressed") ? "Archivo Comprimido" : "Archivo Descargado",
        description: log.message,
        timestamp: log.timestamp,
      };
      setActivities(prev => [activity, ...prev.slice(0, 49)]);
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    socket,
    isConnected,
    status,
    logs,
    stats,
    activities,
    startBot,
    stopBot,
    restartBot,
    clearLogs,
    exportLogs,
    connect,
    disconnect,
  };
}

// Helper function to format uptime
function formatUptime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
}