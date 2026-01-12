from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import os
from datetime import datetime

from src.services import (
    AudioCompressor,
    VideoCompressor,
    FileManager,
    ProgressNotifier,
    CompressionOrchestrator
)
from src.repositories import MessageTracker
from src.strategies import QualityPreservationStrategy, SizeReductionStrategy
from config import API_ID, API_HASH, API_TOKEN

app = Client("bot_compressor", api_id=API_ID, api_hash=API_HASH, bot_token=API_TOKEN, in_memory=True)

# Instancias compartidas (Single Responsibility Principle)
message_tracker = MessageTracker()
file_manager = FileManager()

# Almacenar preferencias de calidad del usuario
# Formato: {user_id: "compress" o "maintain"}
user_quality_preferences = {}

# Almacenar el mensaje actual para el callback de calidad
current_compression_context = {}


@app.on_message(filters.command("start"))
def start(client, message):
    """Maneja el comando /start."""
    try:
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("Compress Audio 🎧", callback_data="compress_audio"),
            InlineKeyboardButton("Compress Video 🎥", callback_data="compress_video")
        ]])
        message.reply_text("Choose what you want to compress:", reply_markup=markup)
    except Exception as e:
        message.reply_text(f"❌ Error: {str(e)}")


@app.on_message(filters.command("log"))
def send_logs(client, message):
    """Envía los logs del bot como mensaje."""
    try:
        message.reply_text("📋 **Recuperando logs del bot...**")

        # Buscar archivos de log
        log_files = []
        log_dirs = ['logs', '.']

        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log') and 'bot' in filename.lower():
                        log_path = os.path.join(log_dir, filename)
                        log_files.append(log_path)

        # Obtener el archivo de log más reciente con contenido
        most_recent_log = None
        most_recent_time = 0

        for log_file in log_files:
            try:
                mtime = os.path.getmtime(log_file)
                if mtime > most_recent_time and os.path.getsize(log_file) > 0:
                    most_recent_time = mtime
                    most_recent_log = log_file
            except Exception:
                pass

        if not most_recent_log:
            # Leer de stdout/stderr si no hay archivo de log
            import subprocess
            try:
                result = subprocess.run(
                    ['tail', '-100', '/proc/self/fd/1'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                logs = result.stdout if result.stdout else "No hay logs recientes"
            except Exception:
                logs = "No se pudieron obtener los logs"
        else:
            # Leer el archivo de log
            try:
                with open(most_recent_log, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # Obtener últimas 100 líneas
                    logs = ''.join(lines[-100:])
            except Exception as e:
                logs = f"Error leyendo logs: {str(e)}"

        # Limitar tamaño del mensaje (Telegram máximo 4096 caracteres)
        max_length = 3800  # Margen de seguridad
        log_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if len(logs) <= max_length:
            # Enviar todo en un mensaje
            log_message = f"📋 **Logs del Bot**\n\n🕐 *{log_timestamp}*\n\n```\n{logs}\n```"
            message.reply_text(log_message)
        else:
            # Dividir en varios mensajes
            chunks = []
            current_chunk = f"📋 **Logs del Bot** ({1})\n\n🕐 *{log_timestamp}*\n\n```\n"
            chunk_num = 1

            for line in logs.split('\n'):
                test_chunk = current_chunk + line + '\n```\n'
                if len(test_chunk) > max_length:
                    chunks.append(current_chunk)
                    chunk_num += 1
                    current_chunk = f"📋 **Logs del Bot** ({chunk_num})\n\n```\n"
                else:
                    current_chunk = current_chunk + line + '\n'

            if current_chunk:
                chunks.append(current_chunk)

            # Enviar cada chunk
            for i, chunk in enumerate(chunks, 1):
                message.reply_text(chunk)

        message.reply_text(f"✅ **{len(chunks) if len(logs) > max_length else 1} mensaje(s) de logs enviados**")

    except Exception as e:
        message.reply_text(f"❌ **Error obteniendo logs:** {str(e)}")


@app.on_callback_query(filters.regex(r'^quality_(compress|maintain)$'))
def quality_callback(client, callback_query: CallbackQuery):
    """Maneja la selección de calidad del usuario."""
    try:
        quality_option = callback_query.data.replace('quality_', '')
        user_id = callback_query.from_user.id

        # Guardar preferencia
        user_quality_preferences[user_id] = quality_option

        # Obtener contexto del mensaje
        context = current_compression_context.get(user_id)
        if not context:
            callback_query.message.reply_text("❌ Error: No se encontró el archivo. Por favor envíalo nuevamente.")
            return

        # Obtener datos del contexto
        file_id = context.get('file_id')
        original_message = context.get('message')

        # Procesar video con la opción elegida usando el client del callback
        process_video_with_quality(client, original_message, quality_option, file_id)

        # Limpiar contexto
        del current_compression_context[user_id]

    except Exception as e:
        error_message = f"❌ **Error al procesar calidad:** {str(e)}\n\n📤 Ocurrió un error inesperado."
        try:
            callback_query.message.edit_text(error_message)
        except Exception:
            pass


@app.on_callback_query()
def callback(client, callback_query: CallbackQuery):
    """Maneja callbacks generales."""
    try:
        callback_query.message.reply_text("Send me a file.")
    except Exception as e:
        callback_query.message.reply_text(f"❌ Error: {str(e)}")


@app.on_message(filters.voice | filters.audio)
def handle_audio(client, message):
    """Maneja mensajes de audio y voz."""
    try:
        # Crear dependencias (Dependency Inversion Principle)
        compressor = AudioCompressor()
        notifier = ProgressNotifier(message)

        # Crear orquestador
        orchestrator = CompressionOrchestrator(
            compressor=compressor,
            file_manager=file_manager,
            message_tracker=message_tracker,
            notifier=notifier
        )

        # Obtener file_id
        file_id = message.voice.file_id if message.voice else message.audio.file_id

        # Procesar
        orchestrator.process(message, file_id, is_animation=False)

    except Exception as e:
        message.reply_text(f"❌ **Error al procesar audio:** {str(e)}")


@app.on_message(filters.video | filters.animation)
def handle_media(client, message):
    """Maneja mensajes de video y animaciones."""
    try:
        # Obtener file_id y tamaño del archivo
        file_id = message.video.file_id if message.video else message.animation.file_id

        # Para videos, mostrar opciones de calidad primero
        if message.video:
            # Obtener tamaño del archivo directamente del mensaje (sin descargar)
            file_size_bytes = message.video.file_size
            file_size_mb = file_size_bytes / (1024 * 1024)

            # Calcular tiempo estimado
            estimated_time_seconds = max(10, int(file_size_mb * 1.5))
            estimated_time_minutes = estimated_time_seconds // 60
            estimated_time_seconds_remainder = estimated_time_seconds % 60

            if estimated_time_minutes > 0:
                time_str = f"~{estimated_time_minutes}m {estimated_time_seconds_remainder}s"
            else:
                time_str = f"~{estimated_time_seconds}s"

            # Mostrar opciones de calidad
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Comprimir (menor tamaño)", callback_data="quality_compress")],
                [InlineKeyboardButton("🎬 Mantener calidad (mayor tamaño)", callback_data="quality_maintain")]
            ])

            status_message = message.reply_text(
                f"📥 **Archivo recibido** ({file_size_mb:.1f} MB)\n\n"
                f"⏱️ Tiempo estimado: {time_str}\n\n"
                f"🎯 **Elije la opción de calidad:**",
                reply_markup=markup
            )

            # Guardar contexto para el callback (solo file_id, sin descargar)
            user_id = message.from_user.id
            current_compression_context[user_id] = {
                'message': message,
                'file_id': file_id,
                'is_animation': False,
                'status_message': status_message
            }
        else:
            # Para animaciones (GIFs), procesar directamente
            process_animation(client, message, file_id)

    except Exception as e:
        error_message = f"❌ **Error durante preparación del video:** {str(e)}"
        message.reply_text(error_message)


def process_video_with_quality(client, message, quality_option: str, file_id: str):
    """
    Procesa el video con la opción de calidad elegida.

    Args:
        client: Cliente de Pyrogram
        message: Mensaje de Telegram
        quality_option: "compress" o "maintain"
        file_id: ID del archivo a procesar
    """
    try:
        # Crear estrategia según selección (Open/Closed Principle)
        if quality_option == "compress":
            strategy = SizeReductionStrategy()
        elif quality_option == "maintain":
            strategy = QualityPreservationStrategy()
        else:
            raise Exception("Opción de calidad no válida")

        # Crear dependencias
        compressor = VideoCompressor(strategy=strategy)
        notifier = ProgressNotifier(message)

        # Crear orquestador
        orchestrator = CompressionOrchestrator(
            compressor=compressor,
            file_manager=file_manager,
            message_tracker=message_tracker,
            notifier=notifier
        )

        # Verificar file_id
        if not file_id:
            # Fallback: obtener del mensaje actual
            file_id = message.video.file_id if message.video else message.animation.file_id

        # Procesar
        orchestrator.process(message, file_id, is_animation=False)

    except Exception as e:
        error_message = f"❌ **Error al procesar video:** {str(e)}"
        try:
            message.reply_text(error_message)
        except Exception:
            pass


def process_animation(client, message, file_id: str):
    """
    Procesa animaciones (GIFs) sin opciones de calidad.

    Args:
        client: Cliente de Pyrogram
        message: Mensaje de Telegram
        file_id: ID del archivo
    """
    try:
        # Crear dependencias
        compressor = VideoCompressor()
        notifier = ProgressNotifier(message)

        # Crear orquestador
        orchestrator = CompressionOrchestrator(
            compressor=compressor,
            file_manager=file_manager,
            message_tracker=message_tracker,
            notifier=notifier
        )

        # Procesar como animación
        orchestrator.process(message, file_id, is_animation=True)

    except Exception as e:
        error_message = f"❌ **Error al procesar animación:** {str(e)}"
        message.reply_text(error_message)


if __name__ == "__main__":
    app.run()
