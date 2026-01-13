"""
Enhanced Bot for BotCompressor 2.0
With remote management commands via Telegram
"""

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import os
import re
import sys
import requests
import json
from datetime import datetime
from typing import Optional

# Import existing services
try:
    from src.services import (
        AudioCompressor,
        VideoCompressor,
        FileManager,
        ProgressNotifier,
        CompressionOrchestrator,
        YouTubeDownloader,
        YouTubeProgressNotifier
    )
    from src.repositories import MessageTracker
    from src.strategies import (
        QualityPreservationStrategy,
        SizeReductionStrategy,
        BestQualityStrategy,
        OptimalQualityStrategy,
        EfficientQualityStrategy
    )
except ImportError:
    # Fallback for development
    AudioCompressor = None
    VideoCompressor = None
    FileManager = None
    ProgressNotifier = None
    CompressionOrchestrator = None
    YouTubeDownloader = None
    YouTubeProgressNotifier = None
    MessageTracker = None
    QualityPreservationStrategy = None
    SizeReductionStrategy = None
    BestQualityStrategy = None
    OptimalQualityStrategy = None
    EfficientQualityStrategy = None

# Configuration
API_ID = int(os.getenv("API_ID", "39532396"))
API_HASH = os.getenv("API_HASH", "7dfa32c18bbac9c85c4bd65c2b6e253a")
API_TOKEN = os.getenv("API_TOKEN", "8018262234:AAG8K8p6Rc8d0ZJWB2DTwxl8zJw2cpcc6V0")
FORWARD_TO_USER_ID = os.getenv("FORWARD_TO_USER_ID", "RSmuel")
BOT_SERVICE_URL = os.getenv("BOT_SERVICE_URL", "http://localhost:3002")

# Authorized users for remote management (you can add more)
AUTHORIZED_USERS = [
    FORWARD_TO_USER_ID,  # RSmuel
    # Add more user IDs here
]

app = Client("bot_compressor_v2", api_id=API_ID, api_hash=API_HASH, bot_token=API_TOKEN, in_memory=True)

# Global state
message_tracker = MessageTracker() if MessageTracker else None
file_manager = FileManager() if FileManager else None
user_quality_preferences = {}
current_compression_context = {}
youtube_download_context = {}

# YouTube regex
YOUTUBE_REGEX = re.compile(
    r'(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]+'
)

def is_authorized(user_id: str) -> bool:
    """Check if user is authorized for remote management"""
    return user_id in AUTHORIZED_USERS

async def send_bot_status(message):
    """Send current bot status to user"""
    try:
        # Get status from bot service
        response = requests.get(f"{BOT_SERVICE_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get('data', {})
            
            status_text = f"🤖 **Estado del Bot**\n\n"
            status_text += f"📊 **Estado:** {status.get('status', 'unknown')}\n"
            status_text += f"🆔 **PID:** {status.get('pid', 'N/A')}\n"
            status_text += f"⏱️ **Uptime:** {status.get('uptime', 0)} segundos\n"
            status_text += f"📈 **Procesados:** {status.get('stats', {}).get('processed', 0)}\n"
            status_text += f"❌ **Errores:** {status.get('stats', {}).get('errors', 0)}\n"
            status_text += f"🕐 **Última actualización:** {status.get('lastUpdate', 'N/A')}\n"
            
            if status.get('error'):
                status_text += f"\n⚠️ **Error:** {status['error']}"
        else:
            status_text = "❌ No se pudo obtener el estado del bot"
            
    except Exception as e:
        status_text = f"❌ Error obteniendo estado: {str(e)}"
    
    await message.reply_text(status_text)

async def control_bot_service(action: str, message) -> bool:
    """Send control command to bot service"""
    try:
        response = requests.post(f"{BOT_SERVICE_URL}/{action}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                await message.reply_text(f"✅ Comando '{action}' ejecutado exitosamente")
                return True
            else:
                await message.reply_text(f"❌ Error en comando '{action}': {data.get('error', 'Unknown error')}")
                return False
        else:
            await message.reply_text(f"❌ Error HTTP {response.status_code} en comando '{action}'")
            return False
    except Exception as e:
        await message.reply_text(f"❌ Error de conexión: {str(e)}")
        return False

@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Handle /start command"""
    try:
        user_id = str(message.from_user.id)
        username = message.from_user.username or f"id_{user_id}"
        
        # Create main menu
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🎧 Comprimir Audio", callback_data="compress_audio"),
            InlineKeyboardButton("🎥 Comprimir Video", callback_data="compress_video")
        ], [
            InlineKeyboardButton("📊 Estado del Bot", callback_data="bot_status"),
            InlineKeyboardButton("🔗 YouTube", callback_data="youtube_help")
        ]])
        
        # Add management buttons for authorized users
        if is_authorized(username):
            management_buttons = [
                InlineKeyboardButton("⏹️ Detener Bot", callback_data="stop_bot"),
                InlineKeyboardButton("🔄 Reiniciar Bot", callback_data="restart_bot"),
                InlineKeyboardButton("▶️ Iniciar Bot", callback_data="start_bot")
            ]
            markup.inline_keyboard.append(management_buttons)
        
        welcome_text = (
            f"👋 ¡Hola {message.from_user.first_name}!\n\n"
            f"🤖 **BotCompressor 2.0**\n"
            f"Sistema avanzado de compresión de medios\n\n"
            f"🎯 **¿Qué quieres hacer?**"
        )
        
        await message.reply_text(welcome_text, reply_markup=markup)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("stop"))
async def stop_command(client, message):
    """Handle /stop command - Stop the bot"""
    try:
        user_id = str(message.from_user.id)
        username = message.from_user.username or f"id_{user_id}"
        
        if not is_authorized(username):
            await message.reply_text("❌ No tienes permisos para ejecutar este comando")
            return
        
        # Confirm before stopping
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Sí, detener", callback_data="confirm_stop"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancel_stop")
        ]])
        
        await message.reply_text(
            "⚠️ **¿Estás seguro de detener el bot?**\n\n"
            "Esto detendrá el servicio completo y nadie podrá usar el bot hasta que se reinicie.",
            reply_markup=markup
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("restart"))
async def restart_command(client, message):
    """Handle /restart command - Restart the bot"""
    try:
        user_id = str(message.from_user.id)
        username = message.from_user.username or f"id_{user_id}"
        
        if not is_authorized(username):
            await message.reply_text("❌ No tienes permisos para ejecutar este comando")
            return
        
        # Confirm before restarting
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Sí, reiniciar", callback_data="confirm_restart"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancel_restart")
        ]])
        
        await message.reply_text(
            "🔄 **¿Estás seguro de reiniciar el bot?**\n\n"
            "El bot se detendrá y se iniciará automáticamente. Esto puede tardar unos segundos.",
            reply_markup=markup
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("status"))
async def status_command(client, message):
    """Handle /status command - Show bot status"""
    try:
        user_id = str(message.from_user.id)
        username = message.from_user.username or f"id_{user_id}"
        
        if not is_authorized(username):
            await message.reply_text("❌ No tienes permisos para ejecutar este comando")
            return
        
        await send_bot_status(message)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("startbot"))
async def startbot_command(client, message):
    """Handle /startbot command - Start the bot"""
    try:
        user_id = str(message.from_user.id)
        username = message.from_user.username or f"id_{user_id}"
        
        if not is_authorized(username):
            await message.reply_text("❌ No tienes permisos para ejecutar este comando")
            return
        
        success = await control_bot_service("start", message)
        if success:
            # Wait a moment and check status
            await message.reply_text("⏳ Verificando estado...")
            import asyncio
            await asyncio.sleep(3)
            await send_bot_status(message)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("log"))
async def log_command(client, message):
    """Handle /log command - Send bot logs to user"""
    try:
        user_id = str(message.from_user.id)
        username = message.from_user.username or f"id_{user_id}"
        
        if not is_authorized(username):
            await message.reply_text("❌ No tienes permisos para ejecutar este comando")
            return
        
        await message.reply_text("📋 **Recuperando logs del bot...**")
        
        # Buscar archivos de log
        log_files = []
        log_dirs = ['logs', '.']
        
        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log') and ('bot' in filename.lower() or 'telegram' in filename.lower()):
                        log_path = os.path.join(log_dir, filename)
                        if os.path.getsize(log_path) > 0:
                            log_files.append(log_path)
        
        # Buscar también logs específicos
        specific_logs = [
            'telegram-bot.log',
            'bot.log',
            'combined.log',
            'error.log'
        ]
        
        for log_name in specific_logs:
            log_path = os.path.join('.', log_name)
            if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
                log_files.append(log_path)
        
        # Obtener el archivo de log más reciente con contenido
        most_recent_log = None
        most_recent_time = 0
        
        for log_file in log_files:
            try:
                mtime = os.path.getmtime(log_file)
                if mtime > most_recent_time:
                    most_recent_time = mtime
                    most_recent_log = log_file
            except Exception:
                pass
        
        if not most_recent_log:
            # Si no hay archivos de log, crear un log temporal con información del sistema
            import subprocess
            try:
                # Obtener información del sistema
                result = subprocess.run(
                    ['ps', 'aux', '|', 'grep', 'python.*bot', '|', 'head', '-5'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                system_info = result.stdout if result.stdout else "No hay procesos del bot activos"
                
                # Obtener información del proceso del bot
                bot_pid = os.environ.get('BOT_PID', 'N/A')
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                logs_text = f"📋 **Logs del Bot - {timestamp}**\n\n"
                logs_text += f"🔧 **Información del Sistema:**\n"
                logs_text += f"PID del Bot: {bot_pid}\n"
                logs_text += f"Directorio: {os.getcwd()}\n"
                logs_text += f"Python Path: {os.environ.get('PYTHONPATH', 'No configurado')}\n\n"
                logs_text += f"🖥️ **Procesos Activos:**\n{system_info}\n\n"
                logs_text += "ℹ️ No se encontraron archivos de log específicos del bot."
                
                # Enviar como un solo mensaje si no es muy largo
                if len(logs_text) <= 3500:
                    await message.reply_text(logs_text)
                else:
                    # Dividir en partes si es muy largo
                    parts = [logs_text[i:i+3500] for i in range(0, len(logs_text), 3500)]
                    for i, part in enumerate(parts):
                        prefix = f"📋 **Logs del Bot ({i+1}/{len(parts)})**\n\n" if len(parts) > 1 else "📋 **Logs del Bot**\n\n"
                        await message.reply_text(prefix + part)
                        if i < len(parts) - 1:
                            await asyncio.sleep(1)  # Peque no se sature el rate limit
                
            except Exception as e:
                logs_text = f"❌ Error obteniendo información del sistema: {str(e)}"
                await message.reply_text(logs_text)
        else:
            # Leer el archivo de log
            try:
                with open(most_recent_log, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    # Analizar los logs para categorizarlos
                    log_entries = []
                    for line in lines[-100:]:  # Últimas 100 líneas
                        line = line.strip()
                        if line:
                            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if timestamp_match:
                                timestamp = timestamp_match.group(1)
                                message_part = line[len(timestamp):].strip()
                                
                                # Categorizar el nivel de log
                                if '[ERROR]' in message_part:
                                    level = 'ERROR'
                                elif '[WARNING]' in message_part:
                                    level = 'WARNING'
                                elif '[SUCCESS]' in message_part or '✅' in message_part:
                                    level = 'SUCCESS'
                                else:
                                    level = 'INFO'
                                
                                log_entries.append({
                                    'timestamp': timestamp,
                                    'level': level,
                                    'message': message_part
                                })
                            else:
                                # Línea sin timestamp, tratar como INFO
                                log_entries.append({
                                    'timestamp': '',
                                    'level': 'INFO',
                                    'message': line
                                })
                    
                    # Formatear logs para Telegram
                    formatted_logs = []
                    for entry in log_entries[-50:]:  # Últimas 50 entradas
                        if entry['timestamp']:
                            timestamp_formatted = entry['timestamp']
                        else:
                            timestamp_formatted = "Sin timestamp"
                        
                        # Añadir emoji según el nivel
                        level_emoji = {
                            'ERROR': '❌',
                            'WARNING': '⚠️',
                            'SUCCESS': '✅',
                            'INFO': 'ℹ️'
                        }.get(entry['level'], 'ℹ️')
                        
                        formatted_logs.append(
                            f"{level_emoji} `{timestamp_formatted}` {entry['message']}"
                        )
                    
                    # Preparar el mensaje
                    log_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    file_name = os.path.basename(most_recent_log)
                    
                    intro_text = (
                        f"📋 **Logs del Bot**\n\n"
                        f"🕐 *{log_timestamp}*\n"
                        f"📁 Archivo: `{file_name}`\n"
                        f"📊 Total entradas: {len(log_entries)}\n\n"
                    )
                    
                    # Dividir en partes si es muy largo
                    max_message_length = 3500  # Límite seguro para Telegram
                    current_part = intro_text
                    parts = []
                    
                    for log_line in formatted_logs:
                        test_part = current_part + log_line + "\n"
                        if len(test_part) > max_message_length:
                            parts.append(current_part)
                            current_part = f"📋 **Logs del Bot** ({len(parts)+1}/?)\n\n"
                            current_part += log_line + "\n"
                        else:
                            current_part = test_part
                    
                    if current_part.strip():
                        parts.append(current_part)
                    
                    # Enviar cada parte
                    for i, part in enumerate(parts):
                        if i == len(parts) - 1:
                            # Última parte
                            part = part.replace("({len(parts)+1}/?)", f"({len(parts)}/{len(parts)})")
                        await message.reply_text(part)
                        
                        if i < len(parts) - 1:
                            await asyncio.sleep(1)  # Evitar rate limiting
                
                # Estadísticas finales
                stats_text = f"\n\n📈 **Estadísticas:**\n"
                stats_text += f"• Archivo: `{file_name}`\n"
                stats_text += f"• Entradas mostradas: {len(formatted_logs)}\n"
                stats_text += f"• Última actualización: {log_timestamp}"
                
                if len(parts) > 1:
                    await message.reply_text(stats_text)
                
            except Exception as e:
                error_message = f"❌ **Error leyendo logs:** {str(e)}\n\n📤 Por favor, revisa el archivo manualmente."
                await message.reply_text(error_message)
        
        await message.reply_text(f"✅ **Logs enviados exitosamente**")
        
    except Exception as e:
        error_message = f"❌ **Error obteniendo logs:** {str(e)}\n\n📤 Por favor, contacta al administrador."
        await message.reply_text(error_message)

@app.on_message(filters.command("help"))
async def help_command(client, message):
    """Handle /help command"""
    try:
        user_id = str(message.from_user.id)
        username = message.from_user.username or f"id_{user_id}"
        
        help_text = (
            "🤖 **BotCompressor 2.0 - Ayuda**\n\n"
            "📱 **Comandos de Usuario:**\n"
            "• `/start` - Menú principal\n"
            "• `/help` - Esta ayuda\n\n"
        )
        
        if is_authorized(username):
            help_text += (
                "🔧 **Comandos de Administración:**\n"
                "• `/stop` - Detener el bot\n"
                "• `/startbot` - Iniciar el bot\n"
                "• `/restart` - Reiniciar el bot\n"
                "• `/status` - Ver estado del bot\n\n"
            )
        
        help_text += (
            "🎵 **Para comprimir:**\n"
            "• Envía un archivo de audio o voz\n"
            "• Envía un video y selecciona calidad\n"
            "• Envía una URL de YouTube\n\n"
            "❓ **Soporte:** @RSmuel"
        )
        
        await message.reply_text(help_text)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    """Handle callback queries"""
    try:
        data = callback_query.data
        user_id = str(callback_query.from_user.id)
        username = callback_query.from_user.username or f"id_{user_id}"
        
        # Management callbacks (authorized users only)
        if data in ["stop_bot", "restart_bot", "start_bot", "confirm_stop", "cancel_stop", 
                   "confirm_restart", "cancel_restart", "bot_status"]:
            
            if not is_authorized(username):
                await callback_query.message.edit_text("❌ No tienes permisos para esta acción")
                return
            
            if data == "bot_status":
                await send_bot_status(callback_query.message)
                
            elif data == "stop_bot":
                markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Sí, detener", callback_data="confirm_stop"),
                    InlineKeyboardButton("❌ Cancelar", callback_data="cancel_stop")
                ]])
                await callback_query.message.edit_text(
                    "⚠️ **¿Estás seguro de detener el bot?**\n\n"
                    "Esto detendrá el servicio completo.",
                    reply_markup=markup
                )
                
            elif data == "confirm_stop":
                await callback_query.message.edit_text("⏹️ Deteniendo bot...")
                success = await control_bot_service("stop", callback_query.message)
                if success:
                    await callback_query.message.edit_text("✅ Bot detenido exitosamente")
                    
            elif data == "cancel_stop":
                await callback_query.message.edit_text("❌ Acción cancelada")
                
            elif data == "restart_bot":
                markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Sí, reiniciar", callback_data="confirm_restart"),
                    InlineKeyboardButton("❌ Cancelar", callback_data="cancel_restart")
                ]])
                await callback_query.message.edit_text(
                    "🔄 **¿Estás seguro de reiniciar el bot?**\n\n"
                    "El bot se detendrá y se iniciará automáticamente.",
                    reply_markup=markup
                )
                
            elif data == "confirm_restart":
                await callback_query.message.edit_text("🔄 Reiniciando bot...")
                success = await control_bot_service("restart", callback_query.message)
                if success:
                    import asyncio
                    await asyncio.sleep(5)
                    await callback_query.message.edit_text("✅ Bot reiniciado exitosamente")
                    await send_bot_status(callback_query.message)
                    
            elif data == "cancel_restart":
                await callback_query.message.edit_text("❌ Acción cancelada")
                
            elif data == "start_bot":
                await callback_query.message.edit_text("▶️ Iniciando bot...")
                success = await control_bot_service("start", callback_query.message)
                if success:
                    import asyncio
                    await asyncio.sleep(3)
                    await callback_query.message.edit_text("✅ Bot iniciado exitosamente")
                    await send_bot_status(callback_query.message)
        
        # Original compression callbacks
        elif data == "compress_audio":
            await callback_query.message.edit_text(
                "🎧 **Envía un archivo de audio o nota de voz**\n\n"
                "Lo comprimiré automáticamente al formato óptimo."
            )
            
        elif data == "compress_video":
            await callback_query.message.edit_text(
                "🎥 **Envía un video o GIF**\n\n"
                "Podrás elegir la calidad de compresión."
            )
            
        elif data == "youtube_help":
            await callback_query.message.edit_text(
                "🔗 **YouTube Downloader**\n\n"
                "Simplemente envía una URL de YouTube y te daré opciones para descargar y comprimir.\n\n"
                "Formatos soportados:\n"
                "• youtube.com/watch?v=...\n"
                "• youtu.be/...\n"
                "• youtube.com/shorts/..."
            )
            
        else:
            await callback_query.message.reply_text("Por favor usa los botones del menú.")
            
    except Exception as e:
        try:
            await callback_query.message.edit_text(f"❌ Error: {str(e)}")
        except:
            await callback_query.message.reply_text(f"❌ Error: {str(e)}")

# Original handlers (simplified for now)
@app.on_message(filters.voice | filters.audio)
async def handle_audio(client, message):
    """Handle audio messages"""
    try:
        if not AudioCompressor or not CompressionOrchestrator:
            await message.reply_text("❌ Servicios de compresión no disponibles")
            return
            
        # Create compression setup
        compressor = AudioCompressor()
        notifier = ProgressNotifier(message)
        orchestrator = CompressionOrchestrator(
            compressor=compressor,
            file_manager=file_manager,
            message_tracker=message_tracker,
            notifier=notifier
        )
        
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        await orchestrator.process(message, file_id, is_animation=False, file_size_bytes=0)
        
    except Exception as e:
        await message.reply_text(f"❌ Error procesando audio: {str(e)}")

@app.on_message(filters.video | filters.animation)
async def handle_media(client, message):
    """Handle video messages"""
    try:
        if not VideoCompressor or not CompressionOrchestrator:
            await message.reply_text("❌ Servicios de compresión no disponibles")
            return
            
        file_id = message.video.file_id if message.video else message.animation.file_id
        
        if message.video:
            file_size_bytes = message.video.file_size
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Comprimir (menor tamaño)", callback_data="quality_compress")],
                [InlineKeyboardButton("🎬 Mantener calidad (mayor tamaño)", callback_data="quality_maintain")]
            ])
            
            await message.reply_text(
                f"📥 **Video recibido** ({file_size_mb:.1f} MB)\n\n"
                f"🎯 **Elije la opción de calidad:**",
                reply_markup=markup
            )
        else:
            # Handle animation
            await message.reply_text("🎬 Procesando animación...")
            
    except Exception as e:
        await message.reply_text(f"❌ Error procesando video: {str(e)}")

@app.on_message(filters.text)
async def handle_text(client, message):
    """Handle text messages for YouTube URLs"""
    try:
        text = message.text
        youtube_match = YOUTUBE_REGEX.search(text)
        
        if youtube_match:
            if not YouTubeDownloader:
                await message.reply_text("❌ Servicio de YouTube no disponible")
                return
                
            youtube_url = youtube_match.group(0)
            
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎥 Descargar y comprimir", callback_data="youtube_download")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="youtube_cancel")]
            ])
            
            await message.reply_text(
                "🔗 **Enlace de YouTube detectado**\n\n"
                "¿Quieres descargar y comprimir este video?",
                reply_markup=markup
            )
            
    except Exception:
        pass  # Don't interrupt other handlers

if __name__ == "__main__":
    print("🚀 Starting BotCompressor 2.0 Enhanced Bot...")
    print(f"🤖 Bot Service URL: {BOT_SERVICE_URL}")
    print(f"👤 Authorized Users: {AUTHORIZED_USERS}")
    app.run()