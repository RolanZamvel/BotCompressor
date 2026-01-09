import express from 'express';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const httpServer = createServer(app);
const io = new SocketIOServer(httpServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

const PORT = 3002;

// Bot state
let botProcess: ChildProcess | null = null;
let botStatus: 'stopped' | 'starting' | 'running' | 'error' = 'stopped';
let logs: string[] = [];
const MAX_LOGS = 500;

// Middleware
app.use(express.json());

// Store logs in memory
function addLog(message: string, type: 'info' | 'error' | 'success' = 'info') {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] [${type.toUpperCase()}] ${message}`;
  logs.push(logEntry);

  if (logs.length > MAX_LOGS) {
    logs = logs.slice(-MAX_LOGS);
  }

  // Emit to all connected clients
  io.emit('log', { message: logEntry, type, timestamp });
}

// Start the bot
function startBot(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (botStatus === 'running' || botStatus === 'starting') {
      reject(new Error('Bot is already running'));
      return;
    }

    botStatus = 'starting';
    addLog('Starting bot...', 'info');
    io.emit('status', { status: botStatus });

    const botPath = path.join(__dirname, 'src/bot.py');
    const pythonPath = path.join(__dirname, 'venv/bin/python');

    botProcess = spawn(pythonPath, [botPath], {
      cwd: path.join(__dirname, 'src'),
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1'
      }
    });

    botProcess.stdout?.on('data', (data) => {
      const message = data.toString().trim();
      if (message) {
        addLog(message, 'info');
      }
    });

    botProcess.stderr?.on('data', (data) => {
      const message = data.toString().trim();
      if (message) {
        addLog(message, 'error');
      }
    });

    botProcess.on('error', (error) => {
      botStatus = 'error';
      addLog(`Bot process error: ${error.message}`, 'error');
      io.emit('status', { status: botStatus, error: error.message });
      reject(error);
    });

    botProcess.on('exit', (code, signal) => {
      if (botStatus !== 'stopped') {
        const errorMsg = code !== 0 ? `Bot exited with code ${code}` : 'Bot exited unexpectedly';
        botStatus = code === 0 ? 'stopped' : 'error';
        addLog(errorMsg, 'error');
        io.emit('status', { status: botStatus, error: errorMsg });
      }
      botProcess = null;
    });

    // Wait a bit and check if it's still running
    setTimeout(() => {
      if (botProcess && !botProcess.killed) {
        botStatus = 'running';
        addLog('Bot started successfully', 'success');
        io.emit('status', { status: botStatus });
        resolve();
      } else {
        botStatus = 'error';
        addLog('Failed to start bot', 'error');
        io.emit('status', { status: botStatus, error: 'Failed to start bot' });
        reject(new Error('Failed to start bot'));
      }
    }, 2000);
  });
}

// Stop the bot
function stopBot(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!botProcess || botStatus === 'stopped') {
      botStatus = 'stopped';
      addLog('Bot is already stopped', 'info');
      io.emit('status', { status: botStatus });
      resolve();
      return;
    }

    botStatus = 'stopped';
    addLog('Stopping bot...', 'info');
    io.emit('status', { status: botStatus });

    // Try graceful shutdown first
    botProcess.kill('SIGTERM');

    // Force kill after 5 seconds if it doesn't stop
    setTimeout(() => {
      if (botProcess && !botProcess.killed) {
        botProcess.kill('SIGKILL');
      }
      resolve();
    }, 5000);
  });
}

// API Routes
app.get('/status', (req, res) => {
  res.json({
    status: botStatus,
    pid: botProcess?.pid || null,
    uptime: botProcess && botStatus === 'running'
      ? Math.floor((Date.now() - (botProcess.spawnargs?.length > 0 ? Date.now() : 0)) / 1000)
      : 0
  });
});

app.post('/start', async (req, res) => {
  try {
    await startBot();
    res.json({ success: true, status: botStatus });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to start bot'
    });
  }
});

app.post('/stop', async (req, res) => {
  try {
    await stopBot();
    res.json({ success: true, status: botStatus });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to stop bot'
    });
  }
});

app.get('/logs', (req, res) => {
  const limit = parseInt(req.query.limit as string) || 100;
  res.json({
    logs: logs.slice(-limit),
    total: logs.length
  });
});

app.post('/restart', async (req, res) => {
  try {
    await stopBot();
    await new Promise((resolve) => setTimeout(resolve, 1000));
    await startBot();
    res.json({ success: true, status: botStatus });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to restart bot'
    });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    service: 'bot-service',
    status: 'healthy',
    botStatus,
    timestamp: new Date().toISOString()
  });
});

// Socket.io connection handling
io.on('connection', (socket) => {
  console.log(`Client connected: ${socket.id}`);

  // Send current status and recent logs
  socket.emit('status', { status: botStatus });
  socket.emit('logs', { logs: logs.slice(-100) });

  socket.on('disconnect', () => {
    console.log(`Client disconnected: ${socket.id}`);
  });
});

// Start server
httpServer.listen(PORT, () => {
  console.log(`Bot Service running on port ${PORT}`);
  console.log(`API: http://localhost:${PORT}`);
  console.log(`WebSocket: ws://localhost:${PORT}`);

  // Auto-start bot on service start (optional)
  // startBot().catch(console.error);
});
