#!/bin/bash

# Script para verificar y gestionar instancias del bot

echo "🤖 BotCompressor - Estado del Bot"
echo "=================================="
echo ""

# Verificar instancias corriendo
BOT_PROCESSES=$(ps aux | grep "venv/bin/python bot.py" | grep -v grep)
BOT_COUNT=$(echo "$BOT_PROCESSES" | wc -l)

if [ -z "$BOT_PROCESSES" ]; then
    echo "❌ No hay instancias del bot corriendo"
    echo ""
    echo "Para iniciar el bot:"
    echo "  cd /home/z/BotCompressor && ./venv/bin/python bot.py"
else
    echo "✅ Instancias encontradas: $BOT_COUNT"
    echo ""
    echo "$BOT_PROCESSES"
fi

echo ""
echo "=== Archivos de sesión ==="
find /home/z/BotCompressor -name "*.session*" -type f 2>/dev/null | grep -v venv | grep -v __pycache__ || echo "No hay archivos de sesión"

echo ""
echo "=== Información del bot ==="
if [ $BOT_COUNT -gt 0 ]; then
    echo "✅ El bot está activo y funcionando"
    echo "   Nombre: @conberterbot"
    echo "   Puedes probarlo enviando /start en Telegram"
else
    echo "❌ El bot no está corriendo"
fi

echo ""
echo "=== Comandos útiles ==="
echo "Detener el bot:"
echo "  kill -9 $(ps aux | grep 'venv/bin/python bot.py' | grep -v grep | awk '{print $2}')"
echo ""
echo "Reiniciar el bot:"
echo "  cd /home/z/BotCompressor"
echo "  pkill -9 -f 'venv/bin/python bot.py'"
echo "  rm -f *.session*"
echo "  ./venv/bin/python bot.py"
echo ""
echo "Verificar logs:"
echo "  tail -f /home/z/BotCompressor/logs/bot.log"
