'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Info, MessageCircle, Video, Music } from 'lucide-react';

interface InfoCardProps {
  className?: string;
}

export function InfoCard({ className }: InfoCardProps) {
  const features = [
    {
      icon: MessageCircle,
      title: 'Telegram Bot',
      description: 'Automatically compresses media files sent via Telegram'
    },
    {
      icon: Video,
      title: 'Video Compression',
      description: 'Reduces video file size using FFmpeg with configurable quality settings'
    },
    {
      icon: Music,
      title: 'Audio Compression',
      description: 'Compresses audio files while maintaining good quality using Pydub'
    }
  ];

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Info className="h-5 w-5" />
          <CardTitle>About BotCompressor</CardTitle>
        </div>
        <CardDescription>Information about the bot and its capabilities</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            BotCompressor is a Telegram bot that helps users reduce the size of their audio and video files
            while maintaining acceptable quality. The bot processes files sent to it and returns compressed versions.
          </p>
          <div className="space-y-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="flex items-start gap-3">
                  <Icon className="h-5 w-5 mt-0.5 text-primary shrink-0" />
                  <div>
                    <p className="font-medium text-sm">{feature.title}</p>
                    <p className="text-xs text-muted-foreground">{feature.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
