#!/usr/bin/env bash

# BotCompressor 2.0 - Script de Parada
# Detiene todos los servicios del sistema

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_DIR="/home/z/my-project/BotCompressor-2.0"

echo -e "${YELLOW}🛑 Deteniendo BotCompressor 2.0...${NC}"
echo "=================================="

# Función para detener proceso por PID
stop_by_pid() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Deteniendo $service_name (PID: $pid)..."
            kill "$pid"
            sleep 2
            
            # Forzar si no se detiene
            if kill -0 "$pid" 2>/dev/null; then
                echo "Forzando detención de $service_name..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            
            echo -e "${GREEN}✅ $service_name detenido${NC}"
        else
            echo -e "${YELLOW}⚠️ $service_name no estaba corriendo${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️ No se encontró PID para $service_name${NC}"
    fi
}

# Detener servicios por PID
stop_by_pid "$BASE_DIR/.frontend.pid" "Frontend"
stop_by_pid "$BASE_DIR/.bot-service.pid" "Bot Service"
stop_by_pid "$BASE_DIR/.telegram-bot.pid" "Telegram Bot"

# Limpiar procesos restantes en los puertos
echo -e "${YELLOW}🧹 Limpiando procesos restantes...${NC}"

for port in 3000 3002; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Deteniendo proceso en puerto $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

echo -e "${GREEN}✅ Todos los servicios han sido detenidos${NC}"