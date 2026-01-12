"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BotStats } from "@/types";
import { 
  Bot, 
  FileAudio, 
  FileVideo, 
  Clock, 
  TrendingUp, 
  CheckCircle,
  Zap,
  HardDrive
} from "lucide-react";

interface DashboardStatsProps {
  stats: BotStats;
}

export function DashboardStats({ stats }: DashboardStatsProps) {
  const statCards = [
    {
      title: "Procesados Hoy",
      value: stats.processedToday,
      description: `${stats.processedTodayIncrease}% más que ayer`,
      icon: FileAudio,
      trend: stats.processedTodayIncrease > 0 ? "up" : "down",
      color: "text-blue-600",
    },
    {
      title: "Tiempo Activo",
      value: stats.uptime,
      description: "Sin interrupciones",
      icon: Clock,
      trend: "stable",
      color: "text-green-600",
    },
    {
      title: "Total Procesados",
      value: stats.totalProcessed.toLocaleString(),
      description: "Archivos totales",
      icon: Bot,
      trend: "up",
      color: "text-purple-600",
    },
    {
      title: "Tasa de Éxito",
      value: `${stats.successRate}%`,
      description: "Procesamientos exitosos",
      icon: CheckCircle,
      trend: stats.successRate > 95 ? "up" : "stable",
      color: "text-emerald-600",
    },
    {
      title: "Tiempo Promedio",
      value: `${stats.averageCompressionTime}s`,
      description: "Por archivo",
      icon: Zap,
      trend: "stable",
      color: "text-orange-600",
    },
    {
      title: "Uso de CPU",
      value: "45%",
      description: "Uso actual",
      icon: HardDrive,
      trend: "stable",
      color: "text-cyan-600",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {statCards.map((card, index) => {
        const Icon = card.icon;
        return (
          <Card key={index} className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {card.title}
              </CardTitle>
              <Icon className={`h-4 w-4 ${card.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.value}</div>
              <p className="text-xs text-muted-foreground">
                {card.description}
              </p>
              {card.trend === "up" && (
                <Badge variant="secondary" className="mt-2 text-xs">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  En aumento
                </Badge>
              )}
              {card.trend === "down" && (
                <Badge variant="destructive" className="mt-2 text-xs">
                  <TrendingUp className="h-3 w-3 mr-1 rotate-180" />
                  En descenso
                </Badge>
              )}
            </CardContent>
            
            {/* Subtle gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-transparent to-muted/5 pointer-events-none" />
          </Card>
        );
      })}
    </div>
  );
}