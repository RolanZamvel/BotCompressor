import { spawn, ChildProcess } from "child_process";
import { EventEmitter } from "events";
import path from "path";
import fs from "fs/promises";

import { Logger } from "@/utils/logger";
import { BotState, BotStatus } from "@/types";

export interface BotManagerConfig {
  pythonPath: string;
  botScriptPath: string;
  workingDirectory: string;
  autoRestart: boolean;
  maxRestartAttempts: number;
  restartDelay: number;
  healthCheckInterval: number;
}

export class BotManager extends EventEmitter {
  private botProcess: ChildProcess | null = null;
  private status: BotStatus = "stopped";
  private pid: number | null = null;
  private startTime: Date | null = null;
  private restartAttempts = 0;
  private healthCheckTimer: NodeJS.Timeout | null = null;
  private isShuttingDown = false;

  private readonly config: BotManagerConfig;
  private readonly logger: Logger;

  constructor(logger: Logger, config?: Partial<BotManagerConfig>) {
    super();
    this.logger = logger.child({ component: "BotManager" });
    
    this.config = {
      pythonPath: process.env.PYTHON_PATH || "python3",
      botScriptPath: process.env.BOT_SCRIPT_PATH || path.join(__dirname, "../../../bot/src/bot.py"),
      workingDirectory: process.env.BOT_WORKING_DIR || path.join(__dirname, "../../../bot"),
      autoRestart: process.env.BOT_AUTO_RESTART !== "false",
      maxRestartAttempts: parseInt(process.env.BOT_MAX_RESTART_ATTEMPTS || "3", 10),
      restartDelay: parseInt(process.env.BOT_RESTART_DELAY || "5000", 10),
      healthCheckInterval: parseInt(process.env.BOT_HEALTH_CHECK_INTERVAL || "30000", 10),
      ...config,
    };

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    this.on("statusChange", (newStatus: BotStatus) => {
      this.logger.info(`Bot status changed to: ${newStatus}`);
    });
  }

  async start(): Promise<void> {
    if (this.status === "running" || this.status === "starting") {
      throw new Error("Bot is already running or starting");
    }

    if (this.isShuttingDown) {
      throw new Error("Cannot start bot during shutdown");
    }

    this.updateStatus("starting");
    this.logger.info("Starting bot process...");

    try {
      // Verify bot script exists
      await this.verifyBotScript();

      // Start the bot process
      this.botProcess = spawn(this.config.pythonPath, [this.config.botScriptPath], {
        cwd: this.config.workingDirectory,
        stdio: ["pipe", "pipe", "pipe"],
        env: {
          ...process.env,
          PYTHONUNBUFFERED: "1",
          BOT_SERVICE_MODE: "true",
        },
        detached: false,
      });

      this.pid = this.botProcess.pid;
      this.startTime = new Date();

      // Setup process event handlers
      this.setupProcessHandlers();

      // Wait for process to start
      await this.waitForStart();

      // Start health checks
      this.startHealthChecks();

      this.updateStatus("running");
      this.restartAttempts = 0;
      
      this.logger.info(`Bot started successfully with PID: ${this.pid}`);
      this.emit("started");

    } catch (error) {
      this.updateStatus("error");
      this.logger.error("Failed to start bot:", error);
      this.emit("error", error);
      throw error;
    }
  }

  async stop(): Promise<void> {
    if (this.status === "stopped") {
      return;
    }

    this.isShuttingDown = true;
    this.updateStatus("stopping");
    this.logger.info("Stopping bot process...");

    try {
      // Stop health checks
      this.stopHealthChecks();

      if (this.botProcess) {
        // Try graceful shutdown first
        this.botProcess.kill("SIGTERM");

        // Wait for graceful shutdown
        await Promise.race([
          this.waitForExit(),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error("Graceful shutdown timeout")), 10000)
          ),
        ]);

        // If still running, force kill
        if (this.botProcess && !this.botProcess.killed) {
          this.logger.warn("Force killing bot process");
          this.botProcess.kill("SIGKILL");
          await this.waitForExit();
        }
      }

      this.updateStatus("stopped");
      this.pid = null;
      this.startTime = null;
      this.isShuttingDown = false;

      this.logger.info("Bot stopped successfully");
      this.emit("stopped");

    } catch (error) {
      this.updateStatus("error");
      this.logger.error("Failed to stop bot:", error);
      this.emit("error", error);
      throw error;
    }
  }

  async restart(): Promise<void> {
    this.logger.info("Restarting bot...");
    
    try {
      await this.stop();
      await new Promise(resolve => setTimeout(resolve, this.config.restartDelay));
      await this.start();
      
      this.logger.info("Bot restarted successfully");
      this.emit("restarted");

    } catch (error) {
      this.logger.error("Failed to restart bot:", error);
      this.emit("error", error);
      throw error;
    }
  }

  getState(): BotState {
    return {
      status: this.status,
      pid: this.pid,
      uptime: this.getUptime(),
      lastUpdate: new Date(),
      error: this.status === "error" ? "Bot process error" : undefined,
    };
  }

  private async verifyBotScript(): Promise<void> {
    try {
      await fs.access(this.config.botScriptPath, fs.constants.F_OK);
    } catch (error) {
      throw new Error(`Bot script not found: ${this.config.botScriptPath}`);
    }
  }

  private setupProcessHandlers(): void {
    if (!this.botProcess) return;

    this.botProcess.stdout?.on("data", (data: Buffer) => {
      const message = data.toString().trim();
      if (message) {
        this.logger.info(`[BOT] ${message}`);
        this.emit("stdout", message);
      }
    });

    this.botProcess.stderr?.on("data", (data: Buffer) => {
      const message = data.toString().trim();
      if (message) {
        this.logger.error(`[BOT] ${message}`);
        this.emit("stderr", message);
      }
    });

    this.botProcess.on("error", (error: Error) => {
      this.logger.error("Bot process error:", error);
      this.updateStatus("error");
      this.emit("error", error);
      this.handleRestart();
    });

    this.botProcess.on("exit", (code: number | null, signal: string | null) => {
      this.logger.info(`Bot process exited with code: ${code}, signal: ${signal}`);
      
      if (!this.isShuttingDown) {
        this.updateStatus(code === 0 ? "stopped" : "error");
        
        if (code !== 0) {
          this.handleRestart();
        }
      }

      this.botProcess = null;
      this.pid = null;
      this.startTime = null;
    });
  }

  private async waitForStart(): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Bot start timeout"));
      }, 30000);

      const checkStarted = () => {
        if (this.status === "running") {
          clearTimeout(timeout);
          resolve();
          return;
        }

        if (this.status === "error") {
          clearTimeout(timeout);
          reject(new Error("Bot failed to start"));
          return;
        }

        setTimeout(checkStarted, 100);
      };

      setTimeout(checkStarted, 1000);
    });
  }

  private async waitForExit(): Promise<void> {
    return new Promise((resolve) => {
      if (!this.botProcess) {
        resolve();
        return;
      }

      this.botProcess.once("exit", () => {
        resolve();
      });
    });
  }

  private startHealthChecks(): void {
    this.healthCheckTimer = setInterval(() => {
      this.performHealthCheck();
    }, this.config.healthCheckInterval);
  }

  private stopHealthChecks(): void {
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
      this.healthCheckTimer = null;
    }
  }

  private async performHealthCheck(): Promise<void> {
    if (!this.botProcess || this.botProcess.killed) {
      this.logger.warn("Health check failed: Bot process not running");
      this.updateStatus("error");
      this.handleRestart();
      return;
    }

    // Additional health checks can be added here
    // For example, checking if the bot is responsive via IPC or HTTP
  }

  private handleRestart(): void {
    if (!this.config.autoRestart || this.isShuttingDown) {
      return;
    }

    if (this.restartAttempts >= this.config.maxRestartAttempts) {
      this.logger.error(`Max restart attempts (${this.config.maxRestartAttempts}) reached`);
      this.updateStatus("error");
      this.emit("maxRestartAttemptsReached");
      return;
    }

    this.restartAttempts++;
    this.logger.info(`Attempting to restart bot (attempt ${this.restartAttempts}/${this.config.maxRestartAttempts})`);

    setTimeout(async () => {
      try {
        await this.start();
      } catch (error) {
        this.logger.error(`Restart attempt ${this.restartAttempts} failed:`, error);
      }
    }, this.config.restartDelay);
  }

  private updateStatus(newStatus: BotStatus): void {
    if (this.status !== newStatus) {
      const oldStatus = this.status;
      this.status = newStatus;
      this.emit("statusChange", newStatus, oldStatus);
      this.emit("stateUpdate", this.getState());
    }
  }

  private getUptime(): number {
    if (!this.startTime) {
      return 0;
    }
    return Math.floor((Date.now() - this.startTime.getTime()) / 1000);
  }

  // Cleanup method
  async cleanup(): Promise<void> {
    this.logger.info("Cleaning up BotManager...");
    
    this.stopHealthChecks();
    this.removeAllListeners();
    
    if (this.status !== "stopped") {
      await this.stop();
    }
    
    this.logger.info("BotManager cleanup completed");
  }
}