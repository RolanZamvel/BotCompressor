#!/bin/bash

# Script para verificar y gestionar instancias del bot
# Detecta automáticamente el directorio del proyecto

# Detectar directorio del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "🤖 BotCompressor - Estado del Bot"
echo "=================================="
echo ""
echo "📂 Directorio del proyecto: $PROJECT_ROOT"
echo ""

# Verificar instancias corriendo
BOT_PROCESSES=$(ps aux | grep "python.*bot.py" | grep -v grep)
BOT_COUNT=$(echo "$BOT_PROCESSES" | wc -l)

if [ -z "$BOT_PROCESSES" ]; then
    echo "❌ No hay instancias del bot corriendo"
    echo ""
    echo "Para iniciar el bot:"
    echo "  cd $PROJECT_ROOT"
    echo "  ./start_bot_unified.sh"
    echo ""
    echo "O usar el dashboard web:"
    echo "  bun run dev:services"
else
    echo "✅ Instancias encontradas: $BOT_COUNT"
    echo ""
    echo "$BOT_PROCESSES"
fi

echo ""
echo "=== Archivos de sesión ==="
find "$PROJECT_ROOT" -name "*.session*" -type f 2>/dev/null | grep -v venv | grep -v __pycache__ | grep -v node_modules || echo "No hay archivos de sesión"

echo ""
echo "=== Información del bot ==="
if [ $BOT_COUNT -gt 0 ]; then
    echo "✅ El bot está activo y funcionando"
    echo "   Puedes probarlo enviando /start en Telegram"
else
    echo "❌ El bot no está corriendo"
fi

echo ""
echo "=== Comandos útiles ==="
echo "Detener el bot:"
echo "  kill -9 \$(ps aux | grep 'python.*bot.py' | grep -v grep | awk '{print \$2}')"
echo ""
echo "Reiniciar el bot:"
echo "  cd $PROJECT_ROOT"
echo "  ./start_bot_unified.sh"
echo ""
echo "Verificar logs:"
echo "  tail -f $PROJECT_ROOT/logs/bot.log"
