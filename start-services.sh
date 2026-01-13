#!/usr/bin/env bash

# BotCompressor 2.0 - Script de Inicio Único
# Inicia todos los servicios del sistema

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio base
BASE_DIR="/home/z/my-project/BotCompressor-2.0"
BOT_SERVICE_DIR="$BASE_DIR/services/bot-service"

echo -e "${BLUE}🚀 Iniciando BotCompressor 2.0...${NC}"
echo "=================================="

# Función para verificar si un puerto está en uso
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Función para esperar a que un servicio esté listo
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Esperando a que $service_name esté listo...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name está listo!${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo -e "\n${RED}❌ $service_name no está listo después de $max_attempts intentos${NC}"
    return 1
}

# Función para detener servicios existentes
cleanup_services() {
    echo -e "${YELLOW}🧹 Limpiando servicios existentes...${NC}"
    
    # Matar procesos en puertos 3000 y 3002
    if check_port 3000; then
        echo "Deteniendo servicio en puerto 3000..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    fi
    
    if check_port 3002; then
        echo "Deteniendo servicio en puerto 3002..."
        lsof -ti:3002 | xargs kill -9 2>/dev/null || true
    fi
    
    sleep 2
}

# Función para iniciar frontend
start_frontend() {
    echo -e "${BLUE}📱 Iniciando Frontend (Next.js)...${NC}"
    cd "$BASE_DIR"
    
    # Verificar dependencias
    if [ ! -d "node_modules" ]; then
        echo "Instalando dependencias del frontend..."
        bun install
    fi
    
    # Iniciar en background
    bun run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend iniciado con PID: $FRONTEND_PID"
    
    # Esperar a que esté listo
    if wait_for_service "http://localhost:3000" "Frontend"; then
        echo -e "${GREEN}🌐 Frontend disponible en: http://localhost:3000${NC}"
    else
        echo -e "${RED}❌ Error al iniciar frontend${NC}"
        tail -10 frontend.log
        exit 1
    fi
}

# Función para iniciar bot service
start_bot_service() {
    echo -e "${BLUE}🤖 Iniciando Bot Service...${NC}"
    cd "$BOT_SERVICE_DIR"
    
    # Limpiar puerto 3002 si está ocupado
    if check_port 3002; then
        echo "Limpiando puerto 3002..."
        lsof -ti:3002 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # Verificar dependencias Node.js
    if [ ! -d "node_modules" ]; then
        echo "Instalando dependencias del bot service..."
        bun install
    fi
    
    # Verificar entorno Python
    if [ ! -d "venv" ]; then
        echo "Creando entorno virtual Python..."
        python3 -m venv venv
    fi
    
    # Instalar dependencias Python
    echo "Verificando dependencias Python..."
    ./venv/bin/pip install -r requirements.txt > /dev/null 2>&1
    
    # Crear directorio de logs
    mkdir -p logs
    
    # Iniciar en background
    bun run dev > bot-service.log 2>&1 &
    BOT_SERVICE_PID=$!
    echo "Bot Service iniciado con PID: $BOT_SERVICE_PID"
    
    # Esperar a que esté listo
    if wait_for_service "http://localhost:3002/health" "Bot Service"; then
        echo -e "${GREEN}🔧 Bot Service disponible en: http://localhost:3002${NC}"
    else
        echo -e "${RED}❌ Error al iniciar bot service${NC}"
        tail -10 bot-service.log
        exit 1
    fi
}

# Función para iniciar el bot de Telegram
start_telegram_bot() {
    echo -e "${BLUE}📱 Iniciando Bot de Telegram...${NC}"
    cd "$BOT_SERVICE_DIR"
    
    # Configurar variables de entorno
    export PYTHONPATH="$BOT_SERVICE_DIR/src"
    export API_ID="39532396"
    export API_HASH="7dfa32c18bbac9c85c4bd65c2b6e253a"
    export API_TOKEN="8018262234:AAHb3GdVJy_DolhKTHt0F9miSxYwhBljqv0"
    export FORWARD_TO_USER_ID="RSmuel"
    export BOT_SERVICE_URL="http://localhost:3002"
    
    # Verificar dependencias Python antes de iniciar
    echo "Verificando dependencias críticas..."
    if ! ./venv/bin/python -c "import pyrogram" 2>/dev/null; then
        echo "Instalando Pyrogram..."
        ./venv/bin/pip install pyrogram TgCrypto requests
    fi
    
    # Iniciar bot en background
    echo "Iniciando bot con token actualizado..."
    ./venv/bin/python bot_wrapper.py > telegram-bot.log 2>&1 &
    TELEGRAM_BOT_PID=$!
    echo "Bot de Telegram iniciado con PID: $TELEGRAM_BOT_PID"
    
    # Esperar un momento para que se inicie
    sleep 8
    
    # Verificar si el bot está corriendo
    if kill -0 $TELEGRAM_BOT_PID 2>/dev/null; then
        echo -e "${GREEN}🤖 Bot de Telegram iniciado correctamente${NC}"
        echo -e "${GREEN}📱 Comandos disponibles: /start, /stop, /restart, /status, /help${NC}"
        
        # Verificar logs de conexión
        if grep -q "Session started" telegram-bot.log; then
            echo -e "${GREEN}✅ Bot conectado a Telegram exitosamente${NC}"
        else
            echo -e "${YELLOW}⚠️ Bot iniciado pero verificando conexión...${NC}"
            tail -5 telegram-bot.log
        fi
    else
        echo -e "${RED}❌ Error al iniciar bot de Telegram${NC}"
        echo "Revisando logs..."
        tail -10 telegram-bot.log
        return 1
    fi
}

# Función para mostrar estado final
show_status() {
    echo ""
    echo "=================================="
    echo -e "${GREEN}🎉 BotCompressor 2.0 Iniciado Exitosamente!${NC}"
    echo "=================================="
    echo -e "${BLUE}📱 Dashboard Web:${NC}     http://localhost:3000"
    echo -e "${BLUE}🤖 Bot Service API:${NC}   http://localhost:3002"
    echo -e "${BLUE}📊 Health Check:${NC}      http://localhost:3002/health"
    echo -e "${BLUE}📱 Bot de Telegram:${NC}   @BotCompressorBot"
    echo ""
    echo -e "${YELLOW}📋 Comandos del Bot:${NC}"
    echo "  /start    - Menú principal"
    echo "  /stop     - Detener bot (solo admin)"
    echo "  /restart  - Reiniciar bot (solo admin)"
    echo "  /status   - Ver estado (solo admin)"
    echo "  /help     - Ayuda completa"
    echo ""
    echo -e "${YELLOW}📝 Logs:${NC}"
    echo "  Frontend:      $BASE_DIR/frontend.log"
    echo "  Bot Service:  $BOT_SERVICE_DIR/bot-service.log"
    echo "  Telegram Bot: $BOT_SERVICE_DIR/telegram-bot.log"
    echo ""
    echo -e "${YELLOW}🛑 Para detener todos los servicios:${NC}"
    echo "  Presiona Ctrl+C o ejecuta: ./stop-services.sh"
    echo ""
    
    # Guardar PIDs para poder detener después
    echo $FRONTEND_PID > "$BASE_DIR/.frontend.pid"
    echo $BOT_SERVICE_PID > "$BASE_DIR/.bot-service.pid"
    echo $TELEGRAM_BOT_PID > "$BASE_DIR/.telegram-bot.pid"
}

# Función de cleanup al salir
cleanup_on_exit() {
    echo -e "\n${YELLOW}🛑 Deteniendo servicios...${NC}"
    
    if [ -f "$BASE_DIR/.frontend.pid" ]; then
        kill $(cat "$BASE_DIR/.frontend.pid") 2>/dev/null || true
        rm -f "$BASE_DIR/.frontend.pid"
    fi
    
    if [ -f "$BASE_DIR/.bot-service.pid" ]; then
        kill $(cat "$BASE_DIR/.bot-service.pid") 2>/dev/null || true
        rm -f "$BASE_DIR/.bot-service.pid"
    fi
    
    if [ -f "$BASE_DIR/.telegram-bot.pid" ]; then
        kill $(cat "$BASE_DIR/.telegram-bot.pid") 2>/dev/null || true
        rm -f "$BASE_DIR/.telegram-bot.pid"
    fi
    
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
    exit 0
}

# Configurar traps para limpieza
trap cleanup_on_exit SIGINT SIGTERM

# Verificar directorio
if [ ! -d "$BASE_DIR" ]; then
    echo -e "${RED}❌ Error: No se encuentra el directorio $BASE_DIR${NC}"
    exit 1
fi

# Ejecutar flujo principal
cleanup_services
start_frontend
start_bot_service
start_telegram_bot
show_status

# Mantener el script corriendo
echo -e "${BLUE}🔄 Manteniendo servicios activos... (Ctrl+C para detener)${NC}"
while true; do
    sleep 10
    
    # Verificar que los servicios siguan corriendo
    if ! check_port 3000 || ! check_port 3002; then
        echo -e "${RED}❌ Uno de los servicios se ha detenido inesperadamente${NC}"
        cleanup_on_exit
    fi
done