// Bot Status Types
export type BotStatus = 'stopped' | 'starting' | 'running' | 'error' | 'restarting';

export interface BotState {
  status: BotStatus;
  pid: number | null;
  uptime: number;
  lastUpdate: Date;
  error?: string;
}

// Log Types
export type LogLevel = 'info' | 'error' | 'success' | 'warning' | 'debug';

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: LogLevel;
  message: string;
  source?: string;
  metadata?: Record<string, any>;
}

// Statistics Types
export interface BotStats {
  processedToday: number;
  processedTodayIncrease: number;
  uptime: string;
  totalProcessed: number;
  averageCompressionTime: number;
  successRate: number;
  compressionMetrics: MetricData[];
  resourceUsage: MetricData[];
}

export interface MetricData {
  timestamp: string;
  value: number;
  label?: string;
}

// Activity Types
export interface Activity {
  id: string;
  type: 'compression' | 'download' | 'error' | 'system';
  title: string;
  description: string;
  timestamp: Date;
  userId?: string;
  metadata?: Record<string, any>;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface BotStatusResponse extends ApiResponse<BotState> {}

export interface LogsResponse extends ApiResponse<{
  logs: LogEntry[];
  total: number;
}> {}

// WebSocket Events
export interface WebSocketEvents {
  'status': (data: BotState) => void;
  'log': (data: LogEntry) => void;
  'logs': (data: LogEntry[]) => void;
  'connect': () => void;
  'disconnect': () => void;
  'error': (error: string) => void;
}

// Configuration Types
export interface CompressionConfig {
  audio: {
    bitrate: string;
    format: string;
    channels: number;
    sampleRate: number;
  };
  video: {
    scale: string;
    fps: number;
    codec: string;
    bitrate: string;
    crf: number;
    preset: string;
  };
}

export interface BotConfig {
  telegram: {
    apiId: number;
    apiHash: string;
    token: string;
    forwardToUserId: string;
  };
  compression: CompressionConfig;
  performance: {
    maxConcurrent: number;
    timeout: number;
    cleanupInterval: number;
  };
}

// User Types (for future authentication)
export interface User {
  id: string;
  username: string;
  firstName: string;
  lastName?: string;
  role: 'admin' | 'user';
  permissions: string[];
  createdAt: Date;
  lastLogin?: Date;
}

// Component Props Types
export interface DashboardProps {
  className?: string;
}

export interface CardProps extends DashboardProps {
  title: string;
  description?: string;
  children: React.ReactNode;
}

// Error Types
export interface BotError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
}

// Progress Types
export interface ProgressState {
  downloading?: {
    current: number;
    total: number;
    percentage: number;
  };
  compressing?: {
    current: number;
    total: number;
    percentage: number;
  };
  uploading?: {
    current: number;
    total: number;
    percentage: number;
  };
}