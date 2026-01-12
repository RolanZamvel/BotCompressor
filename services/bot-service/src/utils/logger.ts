import pino from "pino";

export interface LogContext {
  requestId?: string;
  userId?: string;
  [key: string]: any;
}

export class Logger {
  private logger: pino.Logger;

  constructor(name: string, context: LogContext = {}) {
    this.logger = pino({
      name,
      level: process.env.LOG_LEVEL || "info",
      formatters: {
        level: (label) => ({ level: label }),
      },
      timestamp: pino.stdTimeFunctions.isoTime,
      base: {
        pid: process.pid,
        hostname: process.env.HOSTNAME || "localhost",
        service: "botcompressor-bot-service",
        version: "2.0.0",
        ...context,
      },
    });
  }

  private formatMessage(message: string, context?: LogContext): any {
    return {
      message,
      ...context,
    };
  }

  debug(message: string, context?: LogContext): void {
    this.logger.debug(this.formatMessage(message, context));
  }

  info(message: string, context?: LogContext): void {
    this.logger.info(this.formatMessage(message, context));
  }

  warn(message: string, context?: LogContext): void {
    this.logger.warn(this.formatMessage(message, context));
  }

  error(message: string, error?: Error | LogContext): void {
    if (error instanceof Error) {
      this.logger.error({
        message,
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
      });
    } else {
      this.logger.error(this.formatMessage(message, error));
    }
  }

  fatal(message: string, error?: Error | LogContext): void {
    if (error instanceof Error) {
      this.logger.fatal({
        message,
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
      });
    } else {
      this.logger.fatal(this.formatMessage(message, error));
    }
  }

  child(context: LogContext): Logger {
    return new Logger(this.logger.name, context);
  }

  // Performance logging
  timer(label: string): () => void {
    const start = Date.now();
    return () => {
      const duration = Date.now() - start;
      this.debug(`Timer: ${label} took ${duration}ms`);
    };
  }

  // HTTP request logging
  logRequest(req: any, res: any, responseTime?: number): void {
    const context = {
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      responseTime,
      userAgent: req.headers["user-agent"],
      ip: req.ip || req.connection.remoteAddress,
      requestId: req.headers["x-request-id"],
    };

    if (res.statusCode >= 400) {
      this.warn(`HTTP ${req.method} ${req.url} ${res.statusCode}`, context);
    } else {
      this.info(`HTTP ${req.method} ${req.url} ${res.statusCode}`, context);
    }
  }

  // Bot operation logging
  logBotOperation(operation: string, success: boolean, context?: LogContext): void {
    const logContext = {
      operation,
      success,
      ...context,
    };

    if (success) {
      this.info(`Bot operation: ${operation} completed successfully`, logContext);
    } else {
      this.error(`Bot operation: ${operation} failed`, logContext);
    }
  }

  // WebSocket event logging
  logWebSocketEvent(event: string, socketId: string, context?: LogContext): void {
    this.debug(`WebSocket event: ${event}`, {
      socketId,
      ...context,
    });
  }
}

// Default logger instance
export const logger = new Logger("BotService");