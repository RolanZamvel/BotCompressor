import { Router } from "express";
import { BotManager } from "@/core/bot-manager";

export class HealthCheckRouter {
  private router: Router;
  private botManager: BotManager;

  constructor(botManager: BotManager) {
    this.router = Router();
    this.botManager = botManager;
    this.setupRoutes();
  }

  private setupRoutes(): void {
    // Basic health check
    this.router.get("/", (req, res) => {
      const botState = this.botManager.getState();
      
      res.json({
        status: "healthy",
        service: "botcompressor-bot-service",
        version: "2.0.0",
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        bot: botState,
      });
    });

    // Detailed health check
    this.router.get("/detailed", (req, res) => {
      const botState = this.botManager.getState();
      const memUsage = process.memoryUsage();
      const cpuUsage = process.cpuUsage();
      
      res.json({
        status: "healthy",
        service: "botcompressor-bot-service",
        version: "2.0.0",
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        environment: process.env.NODE_ENV || "development",
        bot: botState,
        system: {
          platform: process.platform,
          arch: process.arch,
          nodeVersion: process.version,
          pid: process.pid,
        },
        resources: {
          memory: {
            rss: `${Math.round(memUsage.rss / 1024 / 1024)}MB`,
            heapTotal: `${Math.round(memUsage.heapTotal / 1024 / 1024)}MB`,
            heapUsed: `${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`,
            external: `${Math.round(memUsage.external / 1024 / 1024)}MB`,
          },
          cpu: {
            user: cpuUsage.user,
            system: cpuUsage.system,
          },
        },
      });
    });

    // Readiness probe
    this.router.get("/ready", (req, res) => {
      const botState = this.botManager.getState();
      
      // Service is ready if it's not in an error state
      const isReady = botState.status !== "error";
      
      res.status(isReady ? 200 : 503).json({
        ready: isReady,
        status: botState.status,
        timestamp: new Date().toISOString(),
      });
    });

    // Liveness probe
    this.router.get("/live", (req, res) => {
      // Service is alive if the process is running
      const isLive = true;
      
      res.status(isLive ? 200 : 503).json({
        live: isLive,
        timestamp: new Date().toISOString(),
      });
    });
  }

  getRouter(): Router {
    return this.router;
  }
}