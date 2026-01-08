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
            
            # Esperar y verificar que el proceso realmente se terminó
            echo "⏱️ Esperando que el proceso se termine..."
            for i in {1..10}; do
                if ! ps -p $OLD_PID > /dev/null 2>&1; then
                    echo "✅ Proceso terminado (espera: ${i}s)"
                    sleep 1
                    break
                fi
                sleep 1
            done
            
            # Verificación final
            if ps -p $OLD_PID > /dev/null 2>&1; then
                echo "⚠️  Advertencia: El proceso sigue corriendo después de 10 segundos"
            else
                echo "✅ Proceso confirmado terminado"
            fi
        else
            echo "🟢 PID file existe pero no hay proceso activo. Continuando..."
        fi
    else
        echo "🟢 No hay PID file anterior. Es primer inicio."
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
    
    # Verificación final de instancias únicas
    sleep 2
    INSTANCES=$(ps aux | grep "python.*bot.py" | grep -v grep | wc -l)
    if [ "$INSTANCES" -gt 1 ]; then
        echo "⚠️  ADVERTENCIA: Se detectaron $INSTANCES instancias del bot. Esto no debería pasar."
        echo "   Procesos activos:"
        ps aux | grep "python.*bot.py" | grep -v grep | awk '{print "   - PID: "$2", CPU: "$3"%, MEM: "$4"%}'
    else
        echo "✅ Verificación de instancias: Solo 1 instancia corriendo"
    fi
else
    echo "❌ Error al iniciar el bot. Verificando logs..."
    tail -20 logs/bot.log
    exit 1
fi
