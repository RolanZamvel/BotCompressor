#!/usr/bin/env bun

import { spawn, ChildProcess } from 'child_process';
import path from 'path';

console.log('🚀 Starting BotCompressor Dashboard Services...\n');

// Configuración
const services = {
  frontend: {
    name: 'Next.js Dashboard',
    command: 'bun',
    args: ['run', 'dev'],
    cwd: path.join(process.cwd()),
    color: '📱'
  },
  botService: {
    name: 'Bot Service',
    command: 'bun',
    args: ['run', 'dev'],
    cwd: path.join(process.cwd(), 'mini-services/bot-service'),
    color: '🤖'
  }
};

// Almacenar procesos
const processes: Record<string, ChildProcess> = {};

// Manejo de señales para detener todos los servicios
function stopAllServices() {
  console.log('\n\n🛑 Stopping all services...\n');

  Object.keys(processes).forEach((key) => {
    const proc = processes[key];
    if (proc && !proc.killed) {
      console.log(`Stopping ${services[key as keyof typeof services].name}...`);
      proc.kill('SIGTERM');
    }
  });

  // Forzar cerrar después de 10 segundos
  setTimeout(() => {
    Object.keys(processes).forEach((key) => {
      const proc = processes[key];
      if (proc && !proc.killed) {
        proc.kill('SIGKILL');
      }
    });
    process.exit(0);
  }, 10000);
}

// Iniciar un servicio
function startService(key: string) {
  const service = services[key as keyof typeof services];
  console.log(`${service.color} Starting ${service.name}...`);

  const proc = spawn(service.command, service.args, {
    cwd: service.cwd,
    stdio: 'inherit',
    shell: true
  });

  processes[key] = proc;

  // Manejo de salida del proceso
  proc.on('close', (code) => {
    console.log(`\n${service.color} ${service.name} exited with code ${code}`);
    if (code !== 0) {
      console.log('Stopping all services due to error...\n');
      stopAllServices();
    }
  });

  proc.on('error', (err) => {
    console.error(`\n❌ Error starting ${service.name}:`, err);
    stopAllServices();
  });

  return proc;
}

// Iniciar frontend primero
setTimeout(() => {
  startService('frontend');

  // Iniciar bot service después de 2 segundos
  setTimeout(() => {
    const botProc = startService('botService');

    console.log('\n\n✅ All services started!\n');
    console.log('─────────────────────────────────────────────');
    console.log('📱 Frontend (Next.js): http://localhost:3000');
    console.log('🤖 Bot Service:       http://localhost:3002');
    console.log('─────────────────────────────────────────────');
    console.log('\n💡 To stop all services, press Ctrl+C\n');
    console.log('📝 Logs will be displayed above\n\n');

  }, 2000);
}, 500);

// Manejo de Ctrl+C
process.on('SIGINT', () => {
  console.log('\n\n⚠️  SIGINT received');
  stopAllServices();
});

process.on('SIGTERM', () => {
  console.log('\n\n⚠️  SIGTERM received');
  stopAllServices();
});

// Manejo de errores no capturados
process.on('uncaughtException', (err) => {
  console.error('\n\n❌ Uncaught Exception:', err);
  stopAllServices();
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('\n\n❌ Unhandled Rejection at:', promise, 'reason:', reason);
  stopAllServices();
});
