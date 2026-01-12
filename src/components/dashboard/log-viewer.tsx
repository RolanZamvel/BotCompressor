"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LogEntry, LogLevel } from "@/types";
import { 
  Terminal, 
  Download, 
  Trash2, 
  Search,
  Filter,
  Info,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Bug
} from "lucide-react";

interface LogViewerProps {
  logs: LogEntry[];
  className?: string;
}

export function LogViewer({ logs, className }: LogViewerProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [levelFilter, setLevelFilter] = useState<LogLevel | "all">("all");
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLevel = levelFilter === "all" || log.level === levelFilter;
    return matchesSearch && matchesLevel;
  });

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScroll]);

  const getLogLevelIcon = (level: LogLevel) => {
    switch (level) {
      case "info":
        return <Info className="h-3 w-3" />;
      case "success":
        return <CheckCircle className="h-3 w-3" />;
      case "warning":
        return <AlertTriangle className="h-3 w-3" />;
      case "error":
        return <XCircle className="h-3 w-3" />;
      case "debug":
        return <Bug className="h-3 w-3" />;
      default:
        return <Terminal className="h-3 w-3" />;
    }
  };

  const getLogLevelColor = (level: LogLevel) => {
    switch (level) {
      case "info":
        return "text-blue-600 bg-blue-50 border-blue-200";
      case "success":
        return "text-green-600 bg-green-50 border-green-200";
      case "warning":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "error":
        return "text-red-600 bg-red-50 border-red-200";
      case "debug":
        return "text-gray-600 bg-gray-50 border-gray-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const exportLogs = () => {
    const logsText = filteredLogs
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
  };

  const clearLogs = () => {
    // This would typically call an API to clear logs
    console.log("Clear logs requested");
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Terminal className="h-5 w-5" />
              Logs del Sistema
            </CardTitle>
            <CardDescription>
              Mostrando {filteredLogs.length} de {logs.length} logs
            </CardDescription>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={exportLogs}>
              <Download className="h-4 w-4 mr-2" />
              Exportar
            </Button>
            <Button variant="outline" size="sm" onClick={clearLogs}>
              <Trash2 className="h-4 w-4 mr-2" />
              Limpiar
            </Button>
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 pt-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Buscar logs..."
              className="w-full pl-10 pr-4 py-2 border rounded-md bg-background"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <select
              className="px-3 py-2 border rounded-md bg-background"
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value as LogLevel | "all")}
            >
              <option value="all">Todos los niveles</option>
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="success">Success</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoScroll(!autoScroll)}
            className={autoScroll ? "bg-primary text-primary-foreground" : ""}
          >
            Auto-scroll
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        <div
          ref={logContainerRef}
          className="h-96 overflow-y-auto border rounded-md bg-black/5 dark:bg-white/5 p-4 font-mono text-sm custom-scrollbar"
        >
          {filteredLogs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              No hay logs que mostrar
            </div>
          ) : (
            <div className="space-y-2">
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start gap-3 p-2 rounded border bg-background/50 hover:bg-background/80 transition-colors"
                >
                  <div className="flex items-center gap-2 mt-0.5">
                    {getLogLevelIcon(log.level)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${getLogLevelColor(log.level)}`}
                      >
                        {log.level.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {log.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm break-all">{log.message}</p>
                    {log.source && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Fuente: {log.source}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}