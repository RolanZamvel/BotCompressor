#!/bin/bash
# Script de inicio unificado para BotCompressor
# Combina las mejores funcionalidades de start_bot.sh, start_bot_fixed.sh y auto_start_bot.sh

set -e  # Exit on error

# Configuración
PID_FILE=".bot.pid"
LOG_DIR="logs"
BOT_SCRIPT="bot.py"
MAX_RETRIES=20
RETRY_DELAY=120  # 2 minutos entre intentos (para FLOOD_WAIT)

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para matar instancia anterior si existe
kill_old_instance() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            log_warning "Bot ya corriendo (PID: $OLD_PID). Matando instancia anterior..."
            kill -9 $OLD_PID 2>/dev/null || true

            # Esperar y verificar que el proceso realmente se terminó
            log_info "Esperando que el proceso se termine..."
            for i in {1..10}; do
                if ! ps -p $OLD_PID > /dev/null 2>&1; then
                    log_success "Proceso terminado (espera: ${i}s)"
                    sleep 1
                    break
                fi
                sleep 1
            done

            # Verificación final
            if ps -p $OLD_PID > /dev/null 2>&1; then
                log_warning "El proceso sigue corriendo después de 10 segundos"
            else
                log_success "Proceso confirmado terminado"
            fi
        else
            log_info "PID file existe pero no hay proceso activo. Continuando..."
        fi
    else
        log_info "No hay PID file anterior. Es primer inicio."
    fi
}

# Función para guardar PID actual
save_pid() {
    echo $1 > "$PID_FILE"
    log_info "PID guardado en $PID_FILE: $1"
}

# Función para limpiar sesiones
cleanup_sessions() {
    log_info "Limpiando sesiones de Telegram..."
    rm -f *.session* 2>/dev/null || true
}

# Función para iniciar el bot con manejo de FLOOD_WAIT
start_bot_with_retry() {
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        retry_count=$((retry_count + 1))
        log_info "Intento $retry_count/$MAX_RETRIES - $(date '+%H:%M:%S')"

        # Limpiar sesiones antes de cada intento
        cleanup_sessions

        # Iniciar bot
        if [ ! -d "venv" ]; then
            log_error "Virtual environment no encontrado. Ejecuta 'python3 -m venv venv' primero."
            exit 1
        fi

        mkdir -p "$LOG_DIR"
        nohup ./venv/bin/python $BOT_SCRIPT > "$LOG_DIR/bot.log" 2>&1 &
        BOT_PID=$!
        log_success "Bot iniciado con PID: $BOT_PID"

        # Guardar PID
        save_pid $BOT_PID

        # Esperar para verificar estado
        sleep 10

        # Verificar si el bot sigue corriendo
        if ps -p $BOT_PID > /dev/null 2>&1; then
            log_success "✅✅✅ Bot iniciado exitosamente! ✅✅✅"
            log_info "PID: $BOT_PID"
            log_info "Para ver logs: tail -f $LOG_DIR/bot.log"
            log_info "Para detener: kill $(cat $PID_FILE)"

            # Monitoreo del bot
            while ps -p $BOT_PID > /dev/null 2>&1; do
                sleep 60
            done

            log_warning "El bot se detuvo inesperadamente."
            log_info "Revisando logs..."
            tail -30 "$LOG_DIR/bot.log"
            exit 1
        else
            # Verificar si es FLOOD_WAIT
            if tail -5 "$LOG_DIR/bot.log" 2>/dev/null | grep -q "FLOOD_WAIT"; then
                log_warning "⏳ FLOOD_WAIT activo"

                # Verificar tiempo restante
                FLOOD_WAIT=$(tail -1 "$LOG_DIR/bot.log" 2>/dev/null | grep -oP 'wait of \K[0-9]+(?= seconds)' || echo "")
                if [ ! -z "$FLOOD_WAIT" ]; then
                    MINUTES=$((FLOOD_WAIT / 60))
                    log_info "Tiempo estimado restante: ~$MINUTES minutos"
                fi
            fi
        fi

        # Preparar para el siguiente intento
        if [ $retry_count -lt $MAX_RETRIES ]; then
            log_warning "⏱️ Esperando $RETRY_DELAY segundos antes del próximo intento..."
            sleep $RETRY_DELAY
        fi
    done

    log_error "❌ No se pudo iniciar el bot después de $MAX_RETRIES intentos."
    log_info "Por favor, verifica:"
    log_info "  1. El token del bot es correcto"
    log_info "  2. Las credenciales API_ID y API_HASH son correctas"
    log_info "  3. No hay bloqueos adicionales en Telegram"
    log_info "Revisando últimos errores:"
    tail -50 "$LOG_DIR/bot.log"
    exit 1
}

# Función para verificar instancias únicas
verify_single_instance() {
    sleep 2
    INSTANCES=$(ps aux | grep "venv/bin/python.*bot.py" | grep -v grep | wc -l)
    if [ "$INSTANCES" -gt 1 ]; then
        log_warning "⚠️  ADVERTENCIA: Se detectaron $INSTANCES instancias del bot."
        log_info "   Procesos activos:"
        ps aux | grep "venv/bin/python.*bot.py" | grep -v grep | awk '{print "   - PID: "$2", CPU: "$3"%, MEM: "$4"%}'
    else
        log_success "Verificación de instancias: Solo 1 instancia corriendo"
    fi
}

# Ejecutar verificación y matar instancia anterior
log_info "🚀 Iniciando BotCompressor..."
log_info "================================"
echo ""

kill_old_instance
cleanup_sessions

# Iniciar bot con reintentos
start_bot_with_retry

# Este punto no debería alcanzarse si todo sale bien
log_error "El script terminó de forma inesperada"
exit 1
