#!/bin/bash

# Script para iniciar el bot y monitorear su estado

cd /home/z/BotCompressor

echo "🤖 Iniciando BotCompressor..."
echo "================================"
echo ""

# Limpiar cualquier proceso previo
pkill -9 -f "venv/bin/python bot.py" 2>/dev/null
sleep 2

# Limpiar sesiones
rm -f *.session*

# Iniciar el bot
./venv/bin/python bot.py > logs/bot.log 2>&1 &
BOT_PID=$!
echo "Bot iniciado con PID: $BOT_PID"
echo ""

# Esperar un poco y verificar estado
sleep 10

if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "✅ Bot está corriendo correctamente"
    echo ""
    echo "Estado del bot:"
    ps aux | grep $BOT_PID | grep -v grep
else
    echo "⚠️  El bot se detuvo. Revisando logs..."
    echo ""
    tail -50 logs/bot.log
fi

echo ""
echo "📊 Actualizaciones pendientes:"
curl -s "https://api.telegram.org/bot$(grep API_TOKEN config.py | cut -d'"' -f2)/getWebhookInfo" | python -c "import sys, json; data = json.load(sys.stdin); print(f'Pending updates: {data[\"result\"][\"pending_update_count\"]}')"

echo ""
echo "Para ver logs en tiempo real:"
echo "  tail -f /home/z/BotCompressor/logs/bot.log"
