#!/usr/bin/env python3
"""
BotCompressor - Wrapper script para mini-service.

Este script ejecuta el bot usando el código del repositorio principal
en lugar de tener una copia duplicada.
"""
import sys
import os

# Agregar el directorio del repositorio principal y src al path
# Estamos en: /home/z/BotCompressor/mini-services/bot-service/
# Necesitamos agregar: /home/z/BotCompressor/ (para bot.py y config.py)
# Necesitamos agregar: /home/z/BotCompressor/src/ (para servicios, interfaces, etc.)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
src_dir = os.path.join(project_root, 'src')

if project_root not in sys.path:
    sys.path.insert(0, project_root)

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Ahora importar y ejecutar el bot
import bot

if __name__ == "__main__":
    # Ejecutar el bot
    bot.app.run()
