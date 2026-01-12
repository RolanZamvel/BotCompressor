"use client";

import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { DashboardStats } from "@/components/dashboard/dashboard-stats";
import { BotStatusCard } from "@/components/dashboard/bot-status-card";
import { LogViewer } from "@/components/dashboard/log-viewer";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { useBotMonitor } from "@/hooks/use-bot-monitor";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Activity, BarChart3, Terminal, Zap } from "lucide-react";

export default function HomePage() {
  const { status, logs, stats, isConnected } = useBotMonitor();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
      <DashboardHeader />
      
      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Status Overview */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">
              Monitoreo y control del sistema BotCompressor 2.0
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={isConnected ? "default" : "destructive"}>
              {isConnected ? "Conectado" : "Desconectado"}
            </Badge>
            <Badge variant="outline">{status}</Badge>
          </div>
        </div>

        {/* Quick Stats */}
        <DashboardStats stats={stats} />

        {/* Main Content Tabs */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Vista General
            </TabsTrigger>
            <TabsTrigger value="logs" className="flex items-center gap-2">
              <Terminal className="h-4 w-4" />
              Logs
            </TabsTrigger>
            <TabsTrigger value="metrics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Métricas
            </TabsTrigger>
            <TabsTrigger value="activity" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Actividad
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <BotStatusCard status={status} />
              
              <Card>
                <CardHeader>
                  <CardTitle>Procesamiento</CardTitle>
                  <CardDescription>
                    Archivos procesados hoy
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.processedToday}</div>
                  <p className="text-xs text-muted-foreground">
                    +{stats.processedTodayIncrease}% desde ayer
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Tiempo Activo</CardTitle>
                  <CardDescription>
                    Uptime del sistema
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.uptime}</div>
                  <p className="text-xs text-muted-foreground">
                    Sin interrupciones
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Actividad Reciente</CardTitle>
                <CardDescription>
                  Últimas actividades del sistema
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ActivityFeed limit={5} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="logs">
            <LogViewer logs={logs} />
          </TabsContent>

          <TabsContent value="metrics">
            <div className="grid gap-4 md:grid-cols-2">
              <MetricsChart 
                title="Rendimiento de Compresión"
                data={stats.compressionMetrics}
                type="line"
              />
              <MetricsChart 
                title="Uso de Recursos"
                data={stats.resourceUsage}
                type="bar"
              />
            </div>
          </TabsContent>

          <TabsContent value="activity">
            <ActivityFeed />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}