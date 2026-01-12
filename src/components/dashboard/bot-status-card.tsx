"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BotStatus } from "@/types";
import { 
  Bot, 
  Play, 
  Square, 
  RotateCcw, 
  Activity,
  Clock,
  AlertCircle,
  CheckCircle
} from "lucide-react";

interface BotStatusCardProps {
  status: BotStatus;
  pid?: number | null;
  uptime?: number;
}

export function BotStatusCard({ status, pid, uptime = 0 }: BotStatusCardProps) {
  const getStatusInfo = () => {
    switch (status) {
      case "running":
        return {
          color: "default",
          icon: CheckCircle,
          text: "Activo",
          description: "Bot funcionando correctamente",
        };
      case "starting":
        return {
          color: "secondary",
          icon: Play,
          text: "Iniciando",
          description: "Bot está iniciando...",
        };
      case "stopping":
        return {
          color: "secondary",
          icon: Square,
          text: "Deteniendo",
          description: "Bot está deteniendo...",
        };
      case "restarting":
        return {
          color: "secondary",
          icon: RotateCcw,
          text: "Reiniciando",
          description: "Bot está reiniciando...",
        };
      case "stopped":
        return {
          color: "outline",
          icon: Square,
          text: "Detenido",
          description: "Bot no está en ejecución",
        };
      case "error":
        return {
          color: "destructive",
          icon: AlertCircle,
          text: "Error",
          description: "Bot encontró un error",
        };
      default:
        return {
          color: "outline",
          icon: Activity,
          text: "Desconocido",
          description: "Estado desconocido",
        };
    }
  };

  const statusInfo = getStatusInfo();
  const StatusIcon = statusInfo.icon;

  const formatUptime = (seconds: number) => {
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
  };

  return (
    <Card className="relative">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="h-5 w-5" />
            <CardTitle className="text-lg">Estado del Bot</CardTitle>
          </div>
          <Badge variant={statusInfo.color as any} className="flex items-center gap-1">
            <StatusIcon className="h-3 w-3" />
            {statusInfo.text}
          </Badge>
        </div>
        <CardDescription>{statusInfo.description}</CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Process Info */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          {pid && (
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">PID:</span>
              <span className="font-medium">{pid}</span>
            </div>
          )}
          
          {uptime > 0 && (
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Uptime:</span>
              <span className="font-medium">{formatUptime(uptime)}</span>
            </div>
          )}
        </div>

        {/* Status Indicator */}
        <div className="flex items-center justify-center p-4 bg-muted/50 rounded-lg">
          <div className="text-center">
            <StatusIcon className={`h-12 w-12 mx-auto mb-2 ${
              status === "running" ? "text-green-500" :
              status === "error" ? "text-red-500" :
              status === "starting" || status === "restarting" ? "text-yellow-500" :
              "text-gray-500"
            }`} />
            <p className="text-sm font-medium">{statusInfo.text}</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2">
          {status === "stopped" && (
            <Button size="sm" className="flex-1">
              <Play className="h-4 w-4 mr-2" />
              Iniciar
            </Button>
          )}
          
          {(status === "running" || status === "starting") && (
            <Button size="sm" variant="outline" className="flex-1">
              <Square className="h-4 w-4 mr-2" />
              Detener
            </Button>
          )}
          
          <Button size="sm" variant="outline" className="flex-1">
            <RotateCcw className="h-4 w-4 mr-2" />
            Reiniciar
          </Button>
        </div>
      </CardContent>

      {/* Animated border for active status */}
      {status === "running" && (
        <div className="absolute inset-0 rounded-lg border-2 border-green-500/20 animate-pulse" />
      )}
    </Card>
  );
}