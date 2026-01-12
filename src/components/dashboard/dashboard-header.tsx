"use client";

import { Button } from "@/components/ui/button";
import { useBotMonitor } from "@/hooks/use-bot-monitor";
import { useAuth } from "@/components/auth/auth-provider";
import { 
  Play, 
  Square, 
  RotateCcw, 
  Settings, 
  LogOut, 
  User,
  Moon,
  Sun
} from "lucide-react";
import { useTheme } from "next-themes";

export function DashboardHeader() {
  const { status, startBot, stopBot, restartBot, isConnected } = useBotMonitor();
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();

  const handleStart = async () => {
    try {
      await startBot();
    } catch (error) {
      console.error("Failed to start bot:", error);
    }
  };

  const handleStop = async () => {
    try {
      await stopBot();
    } catch (error) {
      console.error("Failed to stop bot:", error);
    }
  };

  const handleRestart = async () => {
    try {
      await restartBot();
    } catch (error) {
      console.error("Failed to restart bot:", error);
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "running":
        return "text-green-600";
      case "starting":
      case "restarting":
        return "text-yellow-600";
      case "stopped":
        return "text-gray-600";
      case "error":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "running":
        return "Bot Activo";
      case "starting":
        return "Iniciando...";
      case "restarting":
        return "Reiniciando...";
      case "stopped":
        return "Bot Detenido";
      case "error":
        return "Error";
      default:
        return "Desconocido";
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`h-3 w-3 rounded-full ${getStatusColor()}`} />
            <span className="font-semibold">{getStatusText()}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleStart}
              disabled={status === "running" || status === "starting"}
            >
              <Play className="h-4 w-4 mr-1" />
              Iniciar
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleStop}
              disabled={status === "stopped"}
            >
              <Square className="h-4 w-4 mr-1" />
              Detener
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleRestart}
              disabled={status === "starting" || status === "restarting"}
            >
              <RotateCcw className="h-4 w-4 mr-1" />
              Reiniciar
            </Button>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>

          <Button variant="ghost" size="sm">
            <Settings className="h-4 w-4" />
          </Button>

          {user && (
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="sm">
                <User className="h-4 w-4 mr-2" />
                {user.username || user.firstName}
              </Button>
              
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}