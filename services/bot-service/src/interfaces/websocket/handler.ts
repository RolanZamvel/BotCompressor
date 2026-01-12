import { Server as SocketIOServer, Socket } from "socket.io";
import { BotManager } from "@/core/bot-manager";
import { Logger } from "@/utils/logger";

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
}

export class WebSocketHandler {
  private io: SocketIOServer;
  private botManager: BotManager;
  private logger: Logger;
  private connectedClients: Map<string, Socket> = new Map();

  constructor(io: SocketIOServer, botManager: BotManager, logger: Logger) {
    this.io = io;
    this.botManager = botManager;
    this.logger = logger.child({ component: "WebSocketHandler" });
    
    this.setupSocketHandlers();
    this.setupBotManagerHandlers();
  }

  private setupSocketHandlers(): void {
    this.io.on("connection", (socket: Socket) => {
      this.handleClientConnection(socket);
    });
  }

  private setupBotManagerHandlers(): void {
    // Bot status changes
    this.botManager.on("statusChange", (newStatus: string, oldStatus: string) => {
      this.broadcast("status", {
        status: newStatus,
        previousStatus: oldStatus,
        timestamp: new Date().toISOString(),
      });
    });

    // Bot state updates
    this.botManager.on("stateUpdate", (state) => {
      this.broadcast("state", state);
    });

    // Bot events
    this.botManager.on("started", () => {
      this.broadcast("event", {
        type: "started",
        message: "Bot started successfully",
        timestamp: new Date().toISOString(),
      });
    });

    this.botManager.on("stopped", () => {
      this.broadcast("event", {
        type: "stopped",
        message: "Bot stopped",
        timestamp: new Date().toISOString(),
      });
    });

    this.botManager.on("restarted", () => {
      this.broadcast("event", {
        type: "restarted",
        message: "Bot restarted successfully",
        timestamp: new Date().toISOString(),
      });
    });

    this.botManager.on("error", (error: Error) => {
      this.broadcast("event", {
        type: "error",
        message: "Bot encountered an error",
        error: {
          name: error.name,
          message: error.message,
        },
        timestamp: new Date().toISOString(),
      });
    });

    // Bot output
    this.botManager.on("stdout", (message: string) => {
      this.broadcast("log", {
        level: "info",
        message,
        timestamp: new Date().toISOString(),
      });
    });

    this.botManager.on("stderr", (message: string) => {
      this.broadcast("log", {
        level: "error",
        message,
        timestamp: new Date().toISOString(),
      });
    });

    this.botManager.on("maxRestartAttemptsReached", () => {
      this.broadcast("event", {
        type: "maxRestartAttemptsReached",
        message: "Maximum restart attempts reached",
        timestamp: new Date().toISOString(),
      });
    });
  }

  private handleClientConnection(socket: Socket): void {
    const clientId = socket.id;
    this.connectedClients.set(clientId, socket);

    this.logger.logWebSocketEvent("connection", clientId, {
      ip: socket.handshake.address,
      userAgent: socket.handshake.headers["user-agent"],
    });

    // Send initial data to the newly connected client
    this.sendInitialState(socket);

    // Handle client messages
    socket.on("message", (data: WebSocketMessage) => {
      this.handleClientMessage(socket, data);
    });

    // Handle specific events
    socket.on("get_status", () => {
      this.sendStatus(socket);
    });

    socket.on("get_logs", (data: { limit?: number }) => {
      this.sendLogs(socket, data?.limit || 100);
    });

    socket.on("start_bot", async () => {
      await this.handleBotAction(socket, "start");
    });

    socket.on("stop_bot", async () => {
      await this.handleBotAction(socket, "stop");
    });

    socket.on("restart_bot", async () => {
      await this.handleBotAction(socket, "restart");
    });

    // Handle disconnection
    socket.on("disconnect", (reason: string) => {
      this.handleClientDisconnection(socket, reason);
    });

    // Handle errors
    socket.on("error", (error: Error) => {
      this.logger.error("Socket error:", error);
    });
  }

  private sendInitialState(socket: Socket): void {
    try {
      const state = this.botManager.getState();
      
      socket.emit("status", state);
      socket.emit("connected", {
        message: "Connected to BotCompressor service",
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      this.logger.error("Error sending initial state:", error);
    }
  }

  private sendStatus(socket: Socket): void {
    try {
      const state = this.botManager.getState();
      socket.emit("status", state);
    } catch (error) {
      this.logger.error("Error sending status:", error);
      socket.emit("error", {
        message: "Failed to get bot status",
        timestamp: new Date().toISOString(),
      });
    }
  }

  private sendLogs(socket: Socket, limit: number): void {
    try {
      // This would integrate with a log storage system
      // For now, send empty logs
      socket.emit("logs", {
        logs: [],
        total: 0,
        limit,
      });
    } catch (error) {
      this.logger.error("Error sending logs:", error);
      socket.emit("error", {
        message: "Failed to get logs",
        timestamp: new Date().toISOString(),
      });
    }
  }

  private async handleBotAction(socket: Socket, action: "start" | "stop" | "restart"): Promise<void> {
    try {
      switch (action) {
        case "start":
          await this.botManager.start();
          socket.emit("action_result", {
            action,
            success: true,
            message: "Bot started successfully",
            timestamp: new Date().toISOString(),
          });
          break;

        case "stop":
          await this.botManager.stop();
          socket.emit("action_result", {
            action,
            success: true,
            message: "Bot stopped successfully",
            timestamp: new Date().toISOString(),
          });
          break;

        case "restart":
          await this.botManager.restart();
          socket.emit("action_result", {
            action,
            success: true,
            message: "Bot restarted successfully",
            timestamp: new Date().toISOString(),
          });
          break;
      }
    } catch (error) {
      this.logger.error(`Error handling bot action ${action}:`, error);
      socket.emit("action_result", {
        action,
        success: false,
        message: `Failed to ${action} bot`,
        error: error instanceof Error ? error.message : "Unknown error",
        timestamp: new Date().toISOString(),
      });
    }
  }

  private handleClientMessage(socket: Socket, message: WebSocketMessage): void {
    this.logger.logWebSocketEvent("message", socket.id, {
      type: message.type,
      timestamp: message.timestamp,
    });

    // Handle different message types
    switch (message.type) {
      case "ping":
        socket.emit("pong", {
          timestamp: new Date().toISOString(),
        });
        break;

      default:
        this.logger.warn("Unknown message type:", message.type);
    }
  }

  private handleClientDisconnection(socket: Socket, reason: string): void {
    const clientId = socket.id;
    this.connectedClients.delete(clientId);

    this.logger.logWebSocketEvent("disconnection", clientId, {
      reason,
      remainingClients: this.connectedClients.size,
    });
  }

  private broadcast(event: string, data: any): void {
    this.io.emit(event, data);
    this.logger.debug(`Broadcasted event: ${event}`, { data });
  }

  // Public methods for external use
  public broadcastLog(level: string, message: string): void {
    this.broadcast("log", {
      level,
      message,
      timestamp: new Date().toISOString(),
    });
  }

  public broadcastNotification(message: string, type: "info" | "success" | "warning" | "error" = "info"): void {
    this.broadcast("notification", {
      type,
      message,
      timestamp: new Date().toISOString(),
    });
  }

  public getConnectedClientsCount(): number {
    return this.connectedClients.size;
  }

  public cleanup(): void {
    this.logger.info("Cleaning up WebSocketHandler...");
    
    // Disconnect all clients
    this.connectedClients.forEach((socket) => {
      socket.disconnect(true);
    });
    this.connectedClients.clear();
    
    // Remove all event listeners
    this.botManager.removeAllListeners();
    
    this.logger.info("WebSocketHandler cleanup completed");
  }
}