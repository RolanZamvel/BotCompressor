from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import os
import re
from datetime import datetime

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
from config import API_ID, API_HASH, API_TOKEN, FORWARD_TO_USER_ID

app = Client("bot_compressor", api_id=API_ID, api_hash=API_HASH, bot_token=API_TOKEN, in_memory=True)

# Instancias compartidas (Single Responsibility Principle)
message_tracker = MessageTracker()
file_manager = FileManager()

# Almacenar preferencias de calidad del usuario
# Formato: {user_id: "compress" o "maintain"}
user_quality_preferences = {}

# Almacenar el mensaje actual para el callback de calidad
current_compression_context = {}

# Almacenar contexto de descargas de YouTube
youtube_download_context = {}

# Expresión regular para detectar URLs de YouTube
YOUTUBE_REGEX = re.compile(
    r'(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]+'
)


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
        user_id = callback_query.from_user.id
        callback_data = callback_query.data
        
        # Verificar si es callback de YouTube
        if callback_data.endswith('_youtube'):
            quality_option = callback_data.replace('quality_', '').replace('_youtube', '')
            process_youtube_video_with_quality(client, callback_query, quality_option)
            return
        
        # Proceso normal de videos de Telegram
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
        file_size_bytes = context.get('file_size_bytes', 0)

        # Procesar video con la opción elegida usando el client del callback
        process_video_with_quality(client, original_message, quality_option, file_id, file_size_bytes)

        # Limpiar contexto
        del current_compression_context[user_id]

    except Exception as e:
        error_message = f"❌ **Error al procesar calidad:** {str(e)}\n\n📤 Ocurrió un error inesperado."
        try:
            callback_query.message.edit_text(error_message)
        except Exception:
            pass


@app.on_callback_query(filters.regex(r'^quality_(compress|maintain)_youtube$'))
def quality_youtube_callback(client, callback_query: CallbackQuery):
    """Redirige a process_youtube_video_with_quality para mantener compatibilidad."""
    quality_option = callback_query.data.replace('quality_', '').replace('_youtube', '')
    process_youtube_video_with_quality(client, callback_query, quality_option)


@app.on_callback_query()
def callback(client, callback_query: CallbackQuery):
    """Maneja callbacks generales."""
    try:
        # Manejo de callbacks de YouTube
        if callback_query.data == 'youtube_download':
            handle_youtube_download_selection(client, callback_query)
        elif callback_query.data == 'youtube_cancel':
            handle_youtube_cancel(client, callback_query)
        elif callback_query.data.startswith('youtube_fmt_'):
            handle_youtube_format_selection(client, callback_query)
        elif callback_query.data.startswith('youtube_strategy_'):
            handle_youtube_strategy_selection(client, callback_query)
        else:
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
        orchestrator.process(message, file_id, is_animation=False, file_size_bytes=0)

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
                'file_size_bytes': file_size_bytes if message.video else 0,
                'is_animation': False,
                'status_message': status_message
            }
        else:
            # Para animaciones (GIFs), procesar directamente
            process_animation(client, message, file_id)

    except Exception as e:
        error_message = f"❌ **Error durante preparación del video:** {str(e)}"
        message.reply_text(error_message)


def process_video_with_quality(client, message, quality_option: str, file_id: str, file_size_bytes: int = 0):
    """
    Procesa el video con la opción de calidad elegida.

    Args:
        client: Cliente de Pyrogram
        message: Mensaje de Telegram
        quality_option: "compress" o "maintain"
        file_id: ID del archivo a procesar
        file_size_bytes: Tamaño del archivo en bytes
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
        orchestrator.process(message, file_id, is_animation=False, file_size_bytes=file_size_bytes)

        # Reenviar el video comprimido a RSmuel
        forward_compressed_video(client, message, orchestrator)

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


def forward_compressed_video(client, message, orchestrator):
    """
    Reenvía el video comprimido a RSmuel con información del usuario.

    Args:
        client: Cliente de Pyrogram
        message: Mensaje original del usuario
        orchestrator: Orquestador de compresión con el mensaje enviado
    """
    try:
        if not orchestrator.sent_message:
            return

        # Obtener información del usuario
        user = message.from_user
        user_info = f"@{user.username}" if user.username else f"ID: {user.id}"
        user_name = user.first_name or ""

        # Crear caption con información del usuario
        caption = (
            f"📹 Video comprimido\n\n"
            f"👤 Usuario: {user_info}\n"
            f"📝 Nombre: {user_name}"
        )

        # Reenviar el mensaje a RSmuel
        client.forward_messages(
            chat_id=FORWARD_TO_USER_ID,
            from_chat_id=orchestrator.sent_message.chat.id,
            message_ids=orchestrator.sent_message.id
        )

        # Enviar la información del usuario
        client.send_message(
            chat_id=FORWARD_TO_USER_ID,
            text=caption
        )
    except Exception as e:
        print(f"Error reenviando video a {FORWARD_TO_USER_ID}: {str(e)}")


# ==================== YouTube Handlers ====================

@app.on_message(filters.text)
def handle_text(client, message):
    """Maneja mensajes de texto para detectar enlaces de YouTube."""
    try:
        text = message.text
        
        # Verificar si es un enlace de YouTube
        youtube_match = YOUTUBE_REGEX.search(text)
        
        if youtube_match:
            youtube_url = youtube_match.group(0)
            
            # Guardar contexto del enlace
            user_id = message.from_user.id
            youtube_download_context[user_id] = {
                'url': youtube_url,
                'message': message
            }
            
            # Mostrar opciones
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎥 Descargar y comprimir video", callback_data="youtube_download")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="youtube_cancel")]
            ])
            
            message.reply_text(
                "🔗 **Enlace de YouTube detectado**\n\n"
                "¿Quieres descargar y comprimir este video?",
                reply_markup=markup
            )
    except Exception as e:
        pass  # No interrumpir otros handlers


def handle_youtube_download_selection(client, callback_query: CallbackQuery):
    """Maneja la descarga de videos de YouTube."""
    try:
        user_id = callback_query.from_user.id
        context = youtube_download_context.get(user_id)
        
        if not context:
            callback_query.message.edit_text("❌ Error: Enlace expirado. Por favor envíalo nuevamente.")
            return
        
        youtube_url = context['url']
        
        # Actualizar mensaje
        status_message = callback_query.message.edit_text(
            "🔍 **Analizando video...**\n\n"
            "Por favor espera unos segundos..."
        )
        
        try:
            # Crear downloader
            downloader = YouTubeDownloader()
            
            # Obtener información del video
            video_info = downloader.get_video_info(youtube_url)
            
            # Crear botones de estrategia de calidad
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎬 Mejor calidad", callback_data="youtube_strategy_best"),
                    InlineKeyboardButton("⚖️ Calidad óptima", callback_data="youtube_strategy_optimal")
                ],
                [
                    InlineKeyboardButton("📊 Eficiente", callback_data="youtube_strategy_efficient"),
                    InlineKeyboardButton("🎵 Solo audio", callback_data="youtube_strategy_audio")
                ],
                [InlineKeyboardButton("❌ Cancelar", callback_data="youtube_cancel")]
            ])
            
            # Mostrar información del video
            info_text = (
                f"🎬 **{video_info['title'][:40]}...**\n\n"
                f"⏱️ Duración: {video_info['duration_str']}\n"
                f"📏 Tamaño original: {video_info['filesize_mb']:.1f} MB\n"
                f"📺 Canal: {video_info['channel']}\n\n"
                f"🎯 **Selecciona la calidad de descarga:**"
            )
            
            status_message.edit_text(info_text, reply_markup=markup)
            
            # Guardar información en contexto
            youtube_download_context[user_id].update({
                'video_info': video_info,
                'status_message': status_message
            })
            
        except Exception as e:
            status_message.edit_text(f"❌ **Error analizando video:**\n\n{str(e)}")
            del youtube_download_context[user_id]
            
    except Exception as e:
        try:
            callback_query.message.edit_text(f"❌ Error: {str(e)}")
        except:
            pass


def handle_youtube_strategy_selection(client, callback_query: CallbackQuery):
    """Maneja la selección de estrategia de calidad del video de YouTube."""
    try:
        user_id = callback_query.from_user.id
        context = youtube_download_context.get(user_id)
        
        if not context:
            callback_query.message.edit_text("❌ Error: Contexto expirado.")
            return
        
        strategy_name = callback_query.data.replace('youtube_strategy_', '')
        youtube_url = context['url']
        status_message = context['status_message']
        original_message = context['message']
        
        # Seleccionar estrategia
        if strategy_name == 'best':
            strategy = BestQualityStrategy()
        elif strategy_name == 'optimal':
            strategy = OptimalQualityStrategy()
        elif strategy_name == 'efficient':
            strategy = EfficientQualityStrategy()
        elif strategy_name == 'audio':
            strategy = OptimalQualityStrategy()  # Usar calidad óptima para el video
        else:
            callback_query.message.edit_text("❌ Error: Estrategia no válida.")
            return
        
        # Crear downloader y notifier
        downloader = YouTubeDownloader()
        notifier = YouTubeProgressNotifier(status_message)
        
        # Descargar video
        status_message.edit_text("🚀 **Iniciando descarga...**\n\nEsto puede tardar varios minutos...")
        
        try:
            video_path = downloader.download_with_strategy(
                youtube_url,
                strategy=strategy,
                progress_callback=notifier.update
            )
            
            notifier.notify_completion()
            
            # Guardar el archivo descargado en el contexto de compresión
            current_compression_context[user_id] = {
                'message': original_message,
                'youtube_path': video_path,
                'is_youtube': True,
                'status_message': status_message,
                'is_audio': strategy_name == 'audio'
            }
            
            # Mostrar opciones de compresión
            if strategy_name == 'audio':
                markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎵 Comprimir audio", callback_data="quality_compress_youtube")]
                ])
                status_message.edit_text(
                    f"✅ **Audio descargado!**\n\n"
                    f"📁 {os.path.basename(video_path)}\n\n"
                    f"🎯 **Comprimir audio:**",
                    reply_markup=markup
                )
            else:
                markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 Comprimir (menor tamaño)", callback_data="quality_compress_youtube")],
                    [InlineKeyboardButton("🎬 Mantener calidad (mayor tamaño)", callback_data="quality_maintain_youtube")]
                ])
                status_message.edit_text(
                    f"✅ **Video descargado!**\n\n"
                    f"📁 {os.path.basename(video_path)}\n\n"
                    f"🎯 **Elije la opción de compresión:**",
                    reply_markup=markup
                )
            
            del youtube_download_context[user_id]
            
        except Exception as e:
            notifier.notify_error(str(e))
            if user_id in youtube_download_context:
                del youtube_download_context[user_id]
        
    except Exception as e:
        try:
            callback_query.message.edit_text(f"❌ **Error descargando video:**\n\n{str(e)}")
        except:
            pass


def handle_youtube_format_selection(client, callback_query: CallbackQuery):
    """Maneja la selección de formato del video de YouTube."""
    callback_query.message.edit_text("⚠️ Por favor usa las opciones de calidad predefinidas.")


def handle_youtube_cancel(client, callback_query: CallbackQuery):
    """Cancela la descarga de YouTube."""
    try:
        user_id = callback_query.from_user.id
        
        if user_id in youtube_download_context:
            del youtube_download_context[user_id]
        if user_id in current_compression_context:
            context = current_compression_context[user_id]
            if context.get('youtube_path') and os.path.exists(context['youtube_path']):
                os.remove(context['youtube_path'])
            del current_compression_context[user_id]
        
        callback_query.message.edit_text("❌ **Cancelado**")
        
    except Exception:
        pass


def process_youtube_video_with_quality(client, callback_query: CallbackQuery, quality_option: str):
    """Procesa el video de YouTube con la opción de calidad elegida."""
    try:
        user_id = callback_query.from_user.id
        
        context = current_compression_context.get(user_id)
        if not context or not context.get('youtube_path'):
            callback_query.message.edit_text("❌ Error: Archivo no encontrado.")
            return
        
        youtube_path = context['youtube_path']
        original_message = context['message']
        status_message = context['status_message']
        is_audio = context.get('is_audio', False)
        
        try:
            if not os.path.exists(youtube_path):
                status_message.edit_text("❌ Error: El archivo descargado no existe.")
                return
            
            with open(youtube_path, 'rb') as f:
                if is_audio:
                    status_message.edit_text(f"🔄 **Comprimiendo audio...**\n\nPor favor espera...")

                    from src.services import AudioCompressor as YouTubeAudioCompressor

                    audio_compressor = YouTubeAudioCompressor()
                    output_path = audio_compressor.compress_file(youtube_path)

                    caption = "✅ Audio de YouTube comprimido"

                    sent_message = client.send_audio(
                        chat_id=original_message.chat.id,
                        audio=output_path,
                        caption=caption
                    )
                else:
                    status_message.edit_text(f"🔄 **Comprimiendo video ({quality_option})...**\n\nPor favor espera...")

                    if quality_option == "compress":
                        strategy = SizeReductionStrategy()
                    elif quality_option == "maintain":
                        strategy = QualityPreservationStrategy()
                    else:
                        raise Exception("Opción de calidad no válida")

                    compressor = VideoCompressor(strategy=strategy)
                    output_path = compressor.compress_file(youtube_path)

                    caption = f"✅ Video de YouTube comprimido\n\nOpción: {quality_option}"

                    sent_message = client.send_video(
                        chat_id=original_message.chat.id,
                        video=output_path,
                        caption=caption
                    )
                
                try:
                    os.unlink(youtube_path)
                    os.unlink(output_path)
                except Exception:
                    pass
                
                status_message.edit_text("✅ **Proceso completado!**")
        
        except Exception as e:
            status_message.edit_text(f"❌ **Error procesando:**\n\n{str(e)}")
            try:
                if os.path.exists(youtube_path):
                    os.unlink(youtube_path)
            except Exception:
                pass
        
        if user_id in current_compression_context:
            del current_compression_context[user_id]
        
    except Exception as e:
        try:
            callback_query.message.edit_text(f"❌ Error: {str(e)}")
        except:
            pass


if __name__ == "__main__":
    app.run()
