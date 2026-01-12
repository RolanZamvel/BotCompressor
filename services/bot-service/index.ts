import express from 'express';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import dotenv from 'dotenv';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { createLogger, transports, format } from 'winston';
import { RateLimiterMemory } from 'rate-limiter-flexible';

// Configuration
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();

const PORT = parseInt(process.env.PORT || '3002');
const NODE_ENV = process.env.NODE_ENV || 'development';

// Logger setup
const logger = createLogger({
  level: NODE_ENV === 'production' ? 'info' : 'debug',
  format: format.combine(
    format.timestamp(),
    format.errors({ stack: true }),
    format.json()
  ),
  defaultMeta: { service: 'bot-service' },
  transports: [
    new transports.File({ filename: 'logs/error.log', level: 'error' }),
    new transports.File({ filename: 'logs/combined.log' }),
  ],
});

if (NODE_ENV !== 'production') {
  logger.add(new transports.Console({
    format: format.simple()
  }));
}

// Rate limiting
const rateLimiter = new RateLimiterMemory({
  keyGenerator: (req) => req.ip,
  points: 100, // Number of requests
  duration: 60, // Per 60 seconds
});

// Express app setup
const app = express();
const httpServer = createServer(app);

// Socket.IO setup
const io = new SocketIOServer(httpServer, {
  cors: {
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ["http://localhost:3000"],
    methods: ["GET", "POST"],
    credentials: true
  },
  transports: ['websocket', 'polling']
});

// Middleware
app.use(helmet({
  contentSecurityPolicy: NODE_ENV === 'production' ? undefined : false
}));
app.use(compression());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ["http://localhost:3000"],
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging middleware
if (NODE_ENV !== 'test') {
  app.use(morgan('combined', {
    stream: {
      write: (message: string) => logger.info(message.trim())
    }
  }));
}

// Rate limiting middleware
app.use(async (req, res, next) => {
  try {
    await rateLimiter.consume(req.ip);
    next();
  } catch (rejRes) {
    res.status(429).json({
      success: false,
      error: 'Too many requests',
      retryAfter: rejRes.msBeforeNext
    });
  }
});

// Bot state management
interface BotState {
  status: 'stopped' | 'starting' | 'running' | 'error' | 'restarting';
  pid: number | null;
  uptime: number;
  startTime: Date | null;
  lastUpdate: Date;
  error?: string;
  stats: {
    processed: number;
    errors: number;
    startTime: Date;
  };
}

class BotManager {
  private process: ChildProcess | null = null;
  private state: BotState;
  private logs: string[] = [];
  private maxLogs = 1000;
  private startTime: Date | null = null;

  constructor() {
    this.state = {
      status: 'stopped',
      pid: null,
      uptime: 0,
      startTime: null,
      lastUpdate: new Date(),
      stats: {
        processed: 0,
        errors: 0,
        startTime: new Date()
      }
    };
  }

  getState(): BotState {
    return { ...this.state };
  }

  getLogs(limit: number = 100): string[] {
    return this.logs.slice(-limit);
  }

  addLog(message: string, level: 'info' | 'error' | 'success' | 'warning' = 'info'): void {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    
    this.logs.push(logEntry);
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Update stats
    if (level === 'error') {
      this.state.stats.errors++;
    }

    // Emit to all connected clients
    io.emit('log', { 
      message: logEntry, 
      type: level, 
      timestamp,
      id: `${timestamp}-${Math.random()}`
    });

    logger.info(logEntry);
  }

  async start(): Promise<void> {
    if (this.state.status === 'running' || this.state.status === 'starting') {
      throw new Error('Bot is already running or starting');
    }

    this.state.status = 'starting';
    this.state.lastUpdate = new Date();
    this.addLog('Starting bot...', 'info');
    io.emit('status', this.getState());

    try {
      const botPath = path.join(__dirname, 'bot_wrapper.py');
      const pythonPath = process.env.PYTHON_PATH || 'python3';

      this.process = spawn(pythonPath, [botPath], {
        cwd: __dirname,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
          BOT_SERVICE_MODE: 'true'
        },
        stdio: ['pipe', 'pipe', 'pipe']
      });

      this.startTime = new Date();
      this.state.startTime = this.startTime;

      // Handle stdout
      this.process.stdout?.on('data', (data) => {
        const message = data.toString().trim();
        if (message) {
          this.addLog(message, 'info');
          
          // Update stats if processing
          if (message.includes('compressed') || message.includes('processed')) {
            this.state.stats.processed++;
          }
        }
      });

      // Handle stderr
      this.process.stderr?.on('data', (data) => {
        const message = data.toString().trim();
        if (message) {
          this.addLog(message, 'error');
        }
      });

      // Handle process error
      this.process.on('error', (error) => {
        this.state.status = 'error';
        this.state.error = error.message;
        this.state.lastUpdate = new Date();
        this.addLog(`Bot process error: ${error.message}`, 'error');
        io.emit('status', this.getState());
      });

      // Handle process exit
      this.process.on('exit', (code, signal) => {
        if (this.state.status !== 'stopped') {
          const errorMsg = code !== 0 
            ? `Bot exited with code ${code}` 
            : `Bot exited with signal ${signal}`;
          
          this.state.status = code === 0 ? 'stopped' : 'error';
          this.state.error = errorMsg;
          this.state.lastUpdate = new Date();
          this.addLog(errorMsg, 'error');
          io.emit('status', this.getState());
        }
        
        this.process = null;
        this.state.pid = null;
      });

      // Set PID
      if (this.process.pid) {
        this.state.pid = this.process.pid;
      }

      // Wait and check if it's still running
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          if (this.process && !this.process.killed) {
            this.state.status = 'running';
            this.state.lastUpdate = new Date();
            this.addLog('Bot started successfully', 'success');
            io.emit('status', this.getState());
            resolve(void 0);
          } else {
            this.state.status = 'error';
            this.state.error = 'Failed to start bot';
            this.state.lastUpdate = new Date();
            this.addLog('Failed to start bot', 'error');
            io.emit('status', this.getState());
            reject(new Error('Failed to start bot'));
          }
        }, 3000);
      });

    } catch (error) {
      this.state.status = 'error';
      this.state.error = error instanceof Error ? error.message : 'Unknown error';
      this.state.lastUpdate = new Date();
      this.addLog(`Failed to start bot: ${this.state.error}`, 'error');
      io.emit('status', this.getState());
      throw error;
    }
  }

  async stop(): Promise<void> {
    if (!this.process || this.state.status === 'stopped') {
      this.state.status = 'stopped';
      this.state.lastUpdate = new Date();
      this.addLog('Bot is already stopped', 'info');
      io.emit('status', this.getState());
      return;
    }

    this.state.status = 'stopped';
    this.state.lastUpdate = new Date();
    this.addLog('Stopping bot...', 'info');
    io.emit('status', this.getState());

    try {
      // Try graceful shutdown first
      this.process.kill('SIGTERM');

      // Wait for graceful shutdown
      await new Promise((resolve) => setTimeout(resolve, 5000));

      // Force kill if still running
      if (this.process && !this.process.killed) {
        this.process.kill('SIGKILL');
        this.addLog('Force killed bot process', 'warning');
      }

      this.process = null;
      this.state.pid = null;
      this.addLog('Bot stopped successfully', 'success');
      io.emit('status', this.getState());

    } catch (error) {
      this.addLog(`Error stopping bot: ${error}`, 'error');
      throw error;
    }
  }

  async restart(): Promise<void> {
    this.addLog('Restarting bot...', 'info');
    this.state.status = 'restarting';
    io.emit('status', this.getState());

    try {
      await this.stop();
      await new Promise(resolve => setTimeout(resolve, 2000));
      await this.start();
    } catch (error) {
      this.state.status = 'error';
      this.state.error = error instanceof Error ? error.message : 'Restart failed';
      this.addLog(`Restart failed: ${this.state.error}`, 'error');
      io.emit('status', this.getState());
      throw error;
    }
  }

  updateUptime(): void {
    if (this.startTime && this.state.status === 'running') {
      this.state.uptime = Math.floor((Date.now() - this.startTime.getTime()) / 1000);
      this.state.lastUpdate = new Date();
    }
  }
}

// Create bot manager instance
const botManager = new BotManager();

// Update uptime periodically
setInterval(() => {
  botManager.updateUptime();
}, 1000);

// API Routes
app.get('/health', (req, res) => {
  res.json({
    service: 'bot-service',
    status: 'healthy',
    version: '2.0.0',
    timestamp: new Date().toISOString(),
    bot: botManager.getState()
  });
});

app.get('/status', (req, res) => {
  const state = botManager.getState();
  res.json({
    success: true,
    data: state,
    timestamp: new Date().toISOString()
  });
});

app.post('/start', async (req, res) => {
  try {
    await botManager.start();
    res.json({
      success: true,
      data: botManager.getState(),
      message: 'Bot started successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to start bot',
      timestamp: new Date().toISOString()
    });
  }
});

app.post('/stop', async (req, res) => {
  try {
    await botManager.stop();
    res.json({
      success: true,
      data: botManager.getState(),
      message: 'Bot stopped successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to stop bot',
      timestamp: new Date().toISOString()
    });
  }
});

app.post('/restart', async (req, res) => {
  try {
    await botManager.restart();
    res.json({
      success: true,
      data: botManager.getState(),
      message: 'Bot restarted successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to restart bot',
      timestamp: new Date().toISOString()
    });
  }
});

app.get('/logs', (req, res) => {
  const limit = parseInt(req.query.limit as string) || 100;
  const logs = botManager.getLogs(limit);
  
  res.json({
    success: true,
    data: {
      logs: logs.map(log => ({
        message: log,
        timestamp: new Date().toISOString()
      })),
      total: botManager.getLogs().length,
      limit
    },
    timestamp: new Date().toISOString()
  });
});

// Socket.IO connection handling
io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`);

  // Send current state and recent logs
  socket.emit('status', botManager.getState());
  socket.emit('logs', { 
    logs: botManager.getLogs(100).map(log => ({
      message: log,
      timestamp: new Date().toISOString(),
      type: 'info'
    }))
  });

  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
  });

  socket.on('get_status', () => {
    socket.emit('status', botManager.getState());
  });

  socket.on('get_logs', (data) => {
    const limit = data?.limit || 100;
    socket.emit('logs', {
      logs: botManager.getLogs(limit).map(log => ({
        message: log,
        timestamp: new Date().toISOString(),
        type: 'info'
      }))
    });
  });
});

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found',
    timestamp: new Date().toISOString()
  });
});

// Start server
httpServer.listen(PORT, () => {
  logger.info(`Bot Service v2.0.0 running on port ${PORT}`);
  logger.info(`Environment: ${NODE_ENV}`);
  logger.info(`API: http://localhost:${PORT}`);
  logger.info(`WebSocket: ws://localhost:${PORT}`);

  // Auto-start bot in production
  if (NODE_ENV === 'production') {
    setTimeout(() => {
      botManager.start().catch(err => {
        logger.error('Auto-start failed:', err);
      });
    }, 2000);
  }
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  botManager.stop().then(() => {
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  botManager.stop().then(() => {
    process.exit(0);
  });
});

export { app, botManager };