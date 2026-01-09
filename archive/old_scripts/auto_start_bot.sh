#!/bin/bash

# Script para iniciar el bot automáticamente cuando expire el FLOOD_WAIT

cd /home/z/BotCompressor

echo "🤖 BotCompressor - Auto-Start"
echo "================================="
echo ""
echo "Este script intentará iniciar el bot automáticamente"
echo "cuando expire el FLOOD_WAIT de Telegram."
echo ""

MAX_RETRIES=20
RETRY_COUNT=0
WAIT_TIME=120  # 2 minutos entre intentos

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "🔄 Intento $((RETRY_COUNT + 1))/$MAX_RETRIES - $(date '+%H:%M:%S')"

    # Limpiar sesiones
    rm -f *.session* 2>/dev/null

    # Intentar iniciar el bot
    ./venv/bin/python bot.py > logs/bot.log 2>&1 &
    BOT_PID=$!

    # Esperar para verificar
    sleep 10

    # Verificar si el bot sigue corriendo
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo ""
        echo "✅✅✅ Bot iniciado exitosamente! ✅✅✅"
        echo ""
        echo "PID: $BOT_PID"
        echo "Nombre: @conberterbot"
        echo ""
        echo "El bot está listo para recibir comandos."
        echo ""
        echo "Para ver logs:"
        echo "  tail -f /home/z/BotCompressor/logs/bot.log"
        echo ""
        echo "Para detener:"
        echo "  kill -9 $BOT_PID"
        echo ""

        # Monitorear el bot
        while ps -p $BOT_PID > /dev/null 2>&1; do
            sleep 60
        done

        echo ""
        echo "⚠️  El bot se detuvo inesperadamente."
        echo "Revisando logs..."
        tail -30 logs/bot.log
        exit 1
    else
        echo "⏳  FLOOD_WAIT activo, esperando..."

        # Verificar el tiempo restante
        if tail -5 logs/bot.log 2>/dev/null | grep -q "FLOOD_WAIT"; then
            FLOOD_WAIT=$(tail -1 logs/bot.log | grep -oP 'wait of \K[0-9]+(?= seconds)')
            if [ ! -z "$FLOOD_WAIT" ]; then
                MINUTES=$((FLOOD_WAIT / 60))
                echo "   Tiempo estimado restante: ~$MINUTES minutos"
            fi
        fi
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))

    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo ""
        echo "⏱️  Esperando $WAIT_TIME segundos antes del próximo intento..."
        echo ""
        sleep $WAIT_TIME
    fi
done

echo ""
echo "❌ No se pudo iniciar el bot después de $MAX_RETRIES intentos."
echo "Por favor, verifica:"
echo "  1. El token del bot es correcto"
echo "  2. Las credenciales API_ID y API_HASH son correctas"
echo "  3. No hay bloqueos adicionales en Telegram"
echo ""
echo "Revisando últimos errores:"
tail -50 logs/bot.log
