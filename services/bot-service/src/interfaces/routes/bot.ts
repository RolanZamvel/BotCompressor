import { Router, Request, Response } from "express";
import { BotManager } from "@/core/bot-manager";
import { Logger } from "@/utils/logger";

export class BotRouter {
  private router: Router;
  private botManager: BotManager;
  private logger: Logger;

  constructor(botManager: BotManager, logger: Logger) {
    this.router = Router();
    this.botManager = botManager;
    this.logger = logger.child({ component: "BotRouter" });
    this.setupRoutes();
  }

  private setupRoutes(): void {
    // Get bot status
    this.router.get("/status", async (req: Request, res: Response) => {
      try {
        const state = this.botManager.getState();
        
        res.json({
          success: true,
          data: state,
          timestamp: new Date().toISOString(),
        });
      } catch (error) {
        this.logger.error("Error getting bot status:", error);
        res.status(500).json({
          success: false,
          error: {
            message: "Failed to get bot status",
            code: "STATUS_ERROR",
          },
          timestamp: new Date().toISOString(),
        });
      }
    });

    // Start bot
    this.router.post("/start", async (req: Request, res: Response) => {
      try {
        const state = this.botManager.getState();
        
        if (state.status === "running") {
          return res.status(400).json({
            success: false,
            error: {
              message: "Bot is already running",
              code: "ALREADY_RUNNING",
            },
            timestamp: new Date().toISOString(),
          });
        }

        if (state.status === "starting") {
          return res.status(400).json({
            success: false,
            error: {
              message: "Bot is already starting",
              code: "ALREADY_STARTING",
            },
            timestamp: new Date().toISOString(),
          });
        }

        await this.botManager.start();
        
        const newState = this.botManager.getState();
        
        res.json({
          success: true,
          data: newState,
          message: "Bot started successfully",
          timestamp: new Date().toISOString(),
        });

      } catch (error) {
        this.logger.error("Error starting bot:", error);
        res.status(500).json({
          success: false,
          error: {
            message: "Failed to start bot",
            code: "START_ERROR",
            details: error instanceof Error ? error.message : "Unknown error",
          },
          timestamp: new Date().toISOString(),
        });
      }
    });

    // Stop bot
    this.router.post("/stop", async (req: Request, res: Response) => {
      try {
        const state = this.botManager.getState();
        
        if (state.status === "stopped") {
          return res.status(400).json({
            success: false,
            error: {
              message: "Bot is already stopped",
              code: "ALREADY_STOPPED",
            },
            timestamp: new Date().toISOString(),
          });
        }

        await this.botManager.stop();
        
        const newState = this.botManager.getState();
        
        res.json({
          success: true,
          data: newState,
          message: "Bot stopped successfully",
          timestamp: new Date().toISOString(),
        });

      } catch (error) {
        this.logger.error("Error stopping bot:", error);
        res.status(500).json({
          success: false,
          error: {
            message: "Failed to stop bot",
            code: "STOP_ERROR",
            details: error instanceof Error ? error.message : "Unknown error",
          },
          timestamp: new Date().toISOString(),
        });
      }
    });

    // Restart bot
    this.router.post("/restart", async (req: Request, res: Response) => {
      try {
        const state = this.botManager.getState();
        
        if (state.status === "starting") {
          return res.status(400).json({
            success: false,
            error: {
              message: "Cannot restart bot while it's starting",
              code: "CANNOT_RESTART_STARTING",
            },
            timestamp: new Date().toISOString(),
          });
        }

        await this.botManager.restart();
        
        const newState = this.botManager.getState();
        
        res.json({
          success: true,
          data: newState,
          message: "Bot restarted successfully",
          timestamp: new Date().toISOString(),
        });

      } catch (error) {
        this.logger.error("Error restarting bot:", error);
        res.status(500).json({
          success: false,
          error: {
            message: "Failed to restart bot",
            code: "RESTART_ERROR",
            details: error instanceof Error ? error.message : "Unknown error",
          },
          timestamp: new Date().toISOString(),
        });
      }
    });

    // Get bot logs (if available)
    this.router.get("/logs", async (req: Request, res: Response) => {
      try {
        const limit = parseInt(req.query.limit as string) || 100;
        const level = req.query.level as string;
        
        // This would integrate with a log storage system
        // For now, return a placeholder response
        res.json({
          success: true,
          data: {
            logs: [],
            total: 0,
            limit,
            level: level || "all",
          },
          message: "Log integration not implemented yet",
          timestamp: new Date().toISOString(),
        });

      } catch (error) {
        this.logger.error("Error getting bot logs:", error);
        res.status(500).json({
          success: false,
          error: {
            message: "Failed to get bot logs",
            code: "LOGS_ERROR",
          },
          timestamp: new Date().toISOString(),
        });
      }
    });

    // Get bot metrics
    this.router.get("/metrics", async (req: Request, res: Response) => {
      try {
        const state = this.botManager.getState();
        
        // Calculate basic metrics
        const metrics = {
          uptime: state.uptime,
          status: state.status,
          pid: state.pid,
          timestamp: new Date().toISOString(),
          
          // Performance metrics (placeholder - would be calculated from actual data)
          performance: {
            averageResponseTime: 0,
            requestsPerMinute: 0,
            errorRate: 0,
            memoryUsage: process.memoryUsage(),
          },
          
          // Bot-specific metrics (placeholder)
          bot: {
            processedFiles: 0,
            compressionRatio: 0,
            activeConnections: 0,
          },
        };

        res.json({
          success: true,
          data: metrics,
          timestamp: new Date().toISOString(),
        });

      } catch (error) {
        this.logger.error("Error getting bot metrics:", error);
        res.status(500).json({
          success: false,
          error: {
            message: "Failed to get bot metrics",
            code: "METRICS_ERROR",
          },
          timestamp: new Date().toISOString(),
        });
      }
    });

    // Bot configuration endpoints
    this.router.get("/config", async (req: Request, res: Response) => {
      try {
        // Return current bot configuration (excluding sensitive data)
        const config = {
          autoRestart: process.env.BOT_AUTO_RESTART !== "false",
          maxRestartAttempts: parseInt(process.env.BOT_MAX_RESTART_ATTEMPTS || "3", 10),
          restartDelay: parseInt(process.env.BOT_RESTART_DELAY || "5000", 10),
          healthCheckInterval: parseInt(process.env.BOT_HEALTH_CHECK_INTERVAL || "30000", 10),
        };

        res.json({
          success: true,
          data: config,
          timestamp: new Date().toISOString(),
        });

      } catch (error) {
        this.logger.error("Error getting bot config:", error);
        res.status(500).json({
          success: false,
          error: {
            message: "Failed to get bot configuration",
            code: "CONFIG_ERROR",
          },
          timestamp: new Date().toISOString(),
        });
      }
    });
  }

  getRouter(): Router {
    return this.router;
  }
}