#!/bin/bash
# Script de inicio del bot con control de instancias

PID_FILE=".bot.pid"

# Función para matar instancia anterior si existe
kill_old_instance() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "🔴 Bot ya corriendo (PID: $OLD_PID). Matando instancia anterior..."
            kill -9 $OLD_PID 2>/dev/null
            sleep 2
        else
            echo "🟢 PID file existe pero no hay proceso activo. Continuando..."
        fi
    fi
}

# Función para guardar PID actual
save_pid() {
    echo $1 > "$PID_FILE"
    echo "📝 PID guardado en $PID_FILE: $1"
}

# Ejutar verificación y matar instancia anterior
kill_old_instance

# Iniciar bot en background
echo "🚀 Iniciando bot..."
nohup ./venv/bin/python bot.py > logs/bot.log 2>&1 &
BOT_PID=$!

# Guardar PID actual
save_pid $BOT_PID

# Verificar que el bot inició correctamente
sleep 3
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "✅ Bot iniciado correctamente (PID: $BOT_PID)"
    echo "📋 Logs: logs/bot.log"
    echo "🔗 Para detener el bot: kill $(cat .bot.pid)"
else
    echo "❌ Error al iniciar el bot. Verificando logs..."
    tail -20 logs/bot.log
    exit 1
fi
