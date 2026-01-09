#!/usr/bin/env python3
"""
BotCompressor - Wrapper script para mini-service.

Este script ejecuta el bot usando el código del repositorio principal
en lugar de tener una copia duplicada.
"""
import sys
import os

# Agregar el directorio src del repositorio principal al path
# Estamos en: /home/z/my-project/mini-services/bot-service/
# Necesitamos agregar: /home/z/my-project/src/
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
src_dir = os.path.join(project_root, 'src')

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Ahora importar y ejecutar el bot
import bot

if __name__ == "__main__":
    # Ejecutar el bot
    bot.app.run()
