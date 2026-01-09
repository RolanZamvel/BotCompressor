'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Bot, Clock, Activity, Zap } from 'lucide-react';

interface StatsCardProps {
  className?: string;
}

export function StatsCard({ className }: StatsCardProps) {
  const stats = [
    {
      title: 'Total Logs',
      value: '0',
      icon: Activity,
      description: 'Messages processed'
    },
    {
      title: 'Active Sessions',
      value: '0',
      icon: Bot,
      description: 'Users using the bot'
    },
    {
      title: 'Uptime',
      value: '0s',
      icon: Clock,
      description: 'Since last restart'
    },
    {
      title: 'Status',
      value: 'Ready',
      icon: Zap,
      description: 'System operational'
    }
  ];

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Bot Statistics</CardTitle>
        <CardDescription>Real-time performance metrics</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div
                key={index}
                className="flex items-start gap-4 p-4 rounded-lg bg-muted/50"
              >
                <Icon className="h-5 w-5 mt-0.5 text-primary" />
                <div className="flex-1">
                  <p className="text-sm font-medium">{stat.title}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-xs text-muted-foreground">{stat.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
