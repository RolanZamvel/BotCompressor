#!/usr/bin/env bun

import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('🚀 Starting BotCompressor 2.0 Services...\n');

// Service configuration
const services = {
  frontend: {
    name: 'Next.js Dashboard',
    command: 'bun',
    args: ['run', 'dev'],
    cwd: path.join(__dirname),
    port: 3000,
    color: '📱',
    healthCheck: async () => {
      try {
        const response = await fetch('http://localhost:3000');
        return response.ok;
      } catch {
        return false;
      }
    }
  },
  botService: {
    name: 'Bot Service',
    command: 'bun',
    args: ['run', 'dev'],
    cwd: path.join(__dirname, 'services/bot-service'),
    port: 3002,
    color: '🤖',
    healthCheck: async () => {
      try {
        const response = await fetch('http://localhost:3002/health');
        return response.ok;
      } catch {
        return false;
      }
    }
  }
};

// Process management
const processes: Record<string, ChildProcess> = {};
const startupOrder = ['frontend', 'botService'];
const startupDelays = {
  frontend: 0,
  botService: 2000
};

// Graceful shutdown
function stopAllServices() {
  console.log('\n\n🛑 Stopping all services...\n');

  Object.keys(processes).forEach((key) => {
    const proc = processes[key];
    if (proc && !proc.killed) {
      console.log(`${services[key as keyof typeof services].color} Stopping ${services[key as keyof typeof services].name}...`);
      proc.kill('SIGTERM');
    }
  });

  // Force kill after 10 seconds
  setTimeout(() => {
    Object.keys(processes).forEach((key) => {
      const proc = processes[key];
      if (proc && !proc.killed) {
        console.log(`${services[key as keyof typeof services].color} Force killing ${services[key as keyof typeof services].name}...`);
        proc.kill('SIGKILL');
      }
    });
    process.exit(0);
  }, 10000);
}

// Start a service
async function startService(key: string) {
  const service = services[key as keyof typeof services];
  console.log(`${service.color} Starting ${service.name}...`);

  const proc = spawn(service.command, service.args, {
    cwd: service.cwd,
    stdio: 'inherit',
    shell: true,
    env: {
      ...process.env,
      NODE_ENV: process.env.NODE_ENV || 'development',
      PORT: service.port.toString()
    }
  });

  processes[key] = proc;

  // Handle process exit
  proc.on('close', (code) => {
    console.log(`\n${service.color} ${service.name} exited with code ${code}`);
    if (code !== 0) {
      console.log('🚨 Service crashed, stopping all services...\n');
      stopAllServices();
    }
  });

  // Handle process error
  proc.on('error', (err) => {
    console.error(`\n❌ Error starting ${service.name}:`, err);
    stopAllServices();
  });

  // Wait for service to be ready
  if (service.healthCheck) {
    console.log(`${service.color} Waiting for ${service.name} to be ready...`);
    let attempts = 0;
    const maxAttempts = 30;
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      attempts++;
      
      try {
        const isReady = await service.healthCheck();
        if (isReady) {
          console.log(`${service.color} ✅ ${service.name} is ready!`);
          break;
        }
      } catch {
        // Service not ready yet
      }
      
      if (attempts === maxAttempts) {
        console.log(`${service.color} ⚠️ ${service.name} health check failed after ${maxAttempts} attempts`);
      }
    }
  }

  return proc;
}

// Start services in order
async function startAllServices() {
  for (const serviceName of startupOrder) {
    await startService(serviceName);
    
    // Wait before starting next service
    const delay = startupDelays[serviceName as keyof typeof startupDelays];
    if (delay > 0) {
      console.log(`⏳ Waiting ${delay}ms before starting next service...\n`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  console.log('\n\n✅ All services started!\n');
  console.log('─'.repeat(60));
  console.log('📱 Frontend (Next.js): http://localhost:3000');
  console.log('🤖 Bot Service:       http://localhost:3002');
  console.log('📊 Bot Service Health: http://localhost:3002/health');
  console.log('─'.repeat(60));
  console.log('\n💡 To stop all services, press Ctrl+C\n');
  console.log('📝 Service logs will be displayed above\n\n');
}

// Handle signals
process.on('SIGINT', () => {
  console.log('\n\n⚠️  SIGINT received');
  stopAllServices();
});

process.on('SIGTERM', () => {
  console.log('\n\n⚠️  SIGTERM received');
  stopAllServices();
});

// Handle uncaught exceptions
process.on('uncaughtException', (err) => {
  console.error('\n\n❌ Uncaught Exception:', err);
  stopAllServices();
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('\n\n❌ Unhandled Rejection at:', promise, 'reason:', reason);
  stopAllServices();
});

// Start everything
startAllServices().catch((err) => {
  console.error('Failed to start services:', err);
  stopAllServices();
});