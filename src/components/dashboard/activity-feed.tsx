"use client";

import { Activity } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Activity as ActivityIcon, 
  FileAudio, 
  FileVideo, 
  Download,
  AlertTriangle,
  Settings,
  Clock
} from "lucide-react";

interface ActivityFeedProps {
  activities?: Activity[];
  limit?: number;
  className?: string;
}

export function ActivityFeed({ 
  activities = [], 
  limit = 10, 
  className 
}: ActivityFeedProps) {
  // Generate sample activities if none provided
  const sampleActivities: Activity[] = [
    {
      id: "1",
      type: "compression",
      title: "Audio Comprimido",
      description: "Archivo de audio comprimido exitosamente (15.2 MB → 2.1 MB)",
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      userId: "user123",
      metadata: { originalSize: "15.2 MB", compressedSize: "2.1 MB", ratio: "86%" },
    },
    {
      id: "2",
      type: "download",
      title: "Video Descargado",
      description: "Video de YouTube descargado y procesado",
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      userId: "user456",
      metadata: { source: "YouTube", duration: "3:45" },
    },
    {
      id: "3",
      type: "system",
      title: "Sistema Reiniciado",
      description: "Bot reiniciado exitosamente",
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      metadata: { reason: "maintenance" },
    },
    {
      id: "4",
      type: "compression",
      title: "Video Comprimido",
      description: "Video de 1080p comprimido a 720p",
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      userId: "user789",
      metadata: { originalQuality: "1080p", compressedQuality: "720p" },
    },
    {
      id: "5",
      type: "error",
      title: "Error de Compresión",
      description: "Falló la compresión de un archivo corrupto",
      timestamp: new Date(Date.now() - 60 * 60 * 1000),
      userId: "user101",
      metadata: { error: "Corrupted file" },
    },
  ];

  const displayActivities = activities.length > 0 ? activities : sampleActivities;
  const limitedActivities = displayActivities.slice(0, limit);

  const getActivityIcon = (type: Activity["type"]) => {
    switch (type) {
      case "compression":
        return <FileAudio className="h-4 w-4" />;
      case "download":
        return <Download className="h-4 w-4" />;
      case "error":
        return <AlertTriangle className="h-4 w-4" />;
      case "system":
        return <Settings className="h-4 w-4" />;
      default:
        return <ActivityIcon className="h-4 w-4" />;
    }
  };

  const getActivityColor = (type: Activity["type"]) => {
    switch (type) {
      case "compression":
        return "text-blue-600 bg-blue-50 border-blue-200";
      case "download":
        return "text-green-600 bg-green-50 border-green-200";
      case "error":
        return "text-red-600 bg-red-50 border-red-200";
      case "system":
        return "text-purple-600 bg-purple-50 border-purple-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const formatRelativeTime = (date: Date) => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) {
      return "Ahora mismo";
    } else if (diffInMinutes < 60) {
      return `Hace ${diffInMinutes} minuto${diffInMinutes > 1 ? "s" : ""}`;
    } else if (diffInMinutes < 1440) {
      const hours = Math.floor(diffInMinutes / 60);
      return `Hace ${hours} hora${hours > 1 ? "s" : ""}`;
    } else {
      const days = Math.floor(diffInMinutes / 1440);
      return `Hace ${days} día${days > 1 ? "s" : ""}`;
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ActivityIcon className="h-5 w-5" />
          Actividad Reciente
        </CardTitle>
        <CardDescription>
          Últimas actividades del sistema
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        {limitedActivities.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            No hay actividades recientes
          </div>
        ) : (
          <div className="space-y-4">
            {limitedActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg border bg-background/50 hover:bg-background transition-colors"
              >
                <div className={`p-2 rounded-full ${getActivityColor(activity.type)}`}>
                  {getActivityIcon(activity.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-sm">{activity.title}</h4>
                    <Badge variant="outline" className="text-xs">
                      {activity.type}
                    </Badge>
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-2">
                    {activity.description}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatRelativeTime(activity.timestamp)}
                    </div>
                    
                    {activity.userId && (
                      <div>
                        Usuario: {activity.userId}
                      </div>
                    )}
                  </div>
                  
                  {/* Metadata */}
                  {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(activity.metadata).map(([key, value]) => (
                        <Badge
                          key={key}
                          variant="secondary"
                          className="text-xs"
                        >
                          {key}: {String(value)}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}