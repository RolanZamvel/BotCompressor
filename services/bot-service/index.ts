import express from "express";
import { createServer } from "http";
import { Server as SocketIOServer } from "socket.io";
import cors from "cors";
import helmet from "helmet";
import compression from "compression";
import morgan from "morgan";
import dotenv from "dotenv";
import { v4 as uuidv4 } from "uuid";

import { BotManager } from "@/core/bot-manager";
import { Logger } from "@/utils/logger";
import { HealthCheckRouter } from "@/interfaces/routes/health";
import { BotRouter } from "@/interfaces/routes/bot";
import { WebSocketHandler } from "@/interfaces/websocket/handler";

// Load environment variables
dotenv.config();

const app = express();
const httpServer = createServer(app);

// Configuration
const PORT = parseInt(process.env.PORT || "3002", 10);
const NODE_ENV = process.env.NODE_ENV || "development";
const CORS_ORIGIN = process.env.CORS_ORIGIN || "http://localhost:3000";

// Initialize logger
const logger = new Logger("BotService");

// Middleware
app.use(helmet({
  contentSecurityPolicy: false, // Disable for WebSocket compatibility
}));

app.use(compression());
app.use(cors({
  origin: CORS_ORIGIN,
  methods: ["GET", "POST", "PUT", "DELETE"],
  credentials: true,
}));

app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// Logging middleware
if (NODE_ENV === "development") {
  app.use(morgan("dev"));
} else {
  app.use(morgan("combined", {
    stream: {
      write: (message: string) => logger.info(message.trim()),
    },
  }));
}

// Request ID middleware
app.use((req, res, next) => {
  req.headers["x-request-id"] = req.headers["x-request-id"] || uuidv4();
  res.setHeader("X-Request-ID", req.headers["x-request-id"]);
  next();
});

// Initialize Socket.IO
const io = new SocketIOServer(httpServer, {
  cors: {
    origin: CORS_ORIGIN,
    methods: ["GET", "POST"],
    credentials: true,
  },
  transports: ["websocket", "polling"],
  pingTimeout: 60000,
  pingInterval: 25000,
});

// Initialize core components
const botManager = new BotManager(logger);
const wsHandler = new WebSocketHandler(io, botManager, logger);

// Initialize routes
const healthRouter = new HealthCheckRouter(botManager);
const botRouter = new BotRouter(botManager, logger);

// Register routes
app.use("/health", healthRouter.getRouter());
app.use("/bot", botRouter.getRouter());

// Root endpoint
app.get("/", (req, res) => {
  res.json({
    service: "BotCompressor Bot Service",
    version: "2.0.0",
    status: "running",
    timestamp: new Date().toISOString(),
    endpoints: {
      health: "/health",
      bot: "/bot",
      websocket: "/socket.io/",
    },
  });
});

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  logger.error("Unhandled error:", err);
  
  const requestId = req.headers["x-request-id"] as string;
  const statusCode = err.statusCode || err.status || 500;
  
  res.status(statusCode).json({
    success: false,
    error: {
      message: err.message || "Internal Server Error",
      code: err.code || "INTERNAL_ERROR",
      requestId,
    },
    timestamp: new Date().toISOString(),
  });
});

// 404 handler
app.use("*", (req, res) => {
  res.status(404).json({
    success: false,
    error: {
      message: "Endpoint not found",
      code: "NOT_FOUND",
      path: req.originalUrl,
    },
    timestamp: new Date().toISOString(),
  });
});

// Graceful shutdown
const gracefulShutdown = (signal: string) => {
  logger.info(`Received ${signal}, starting graceful shutdown...`);
  
  // Stop accepting new connections
  httpServer.close(async () => {
    logger.info("HTTP server closed");
    
    try {
      // Stop the bot
      await botManager.stop();
      logger.info("Bot manager stopped");
      
      // Close database connections, cleanup, etc.
      logger.info("Graceful shutdown completed");
      process.exit(0);
    } catch (error) {
      logger.error("Error during shutdown:", error);
      process.exit(1);
    }
  });
  
  // Force shutdown after 30 seconds
  setTimeout(() => {
    logger.error("Forced shutdown after timeout");
    process.exit(1);
  }, 30000);
};

// Handle process signals
process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));

// Handle uncaught exceptions
process.on("uncaughtException", (error) => {
  logger.error("Uncaught Exception:", error);
  gracefulShutdown("uncaughtException");
});

process.on("unhandledRejection", (reason, promise) => {
  logger.error("Unhandled Rejection at:", promise, "reason:", reason);
  gracefulShutdown("unhandledRejection");
});

// Start server
const startServer = async () => {
  try {
    logger.info("Starting BotCompressor Bot Service v2.0.0");
    
    // Start the server
    httpServer.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`);
      logger.info(`Environment: ${NODE_ENV}`);
      logger.info(`CORS origin: ${CORS_ORIGIN}`);
      
      // Auto-start bot after 2 seconds (configurable)
      const autoStartDelay = parseInt(process.env.BOT_AUTO_START_DELAY || "2000", 10);
      
      if (process.env.BOT_AUTO_START !== "false") {
        setTimeout(async () => {
          try {
            logger.info("Auto-starting bot...");
            await botManager.start();
            logger.info("Bot started successfully");
          } catch (error) {
            logger.error("Failed to auto-start bot:", error);
            // Don't fail the service if bot fails to start
          }
        }, autoStartDelay);
      } else {
        logger.info("Bot auto-start is disabled");
      }
    });
    
  } catch (error) {
    logger.error("Failed to start server:", error);
    process.exit(1);
  }
};

// Start the service
startServer();