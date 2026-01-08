"""
BotCompressor - Bot de Telegram para comprimir archivos de audio y video

Arquitectura Modular basada en principios SOLID:
- SRP (Single Responsibility Principle): Cada módulo tiene una única responsabilidad
- DIP (Dependency Inversion): Depender de abstracciones, no implementaciones concretas
- OCP (Open/Closed): Abierto a extensión, cerrado a modificación

Módulos:
- modules/file_downloader.py: Responsable de descargar archivos
- modules/audio_compressor.py: Responsable de comprimir audio
- modules/video_compressor.py: Responsable de comprimir video
- modules/bot_state_manager.py: Responsable de gestionar estado del bot
- progress_tracker.py: Responsable de tracking de progreso
"""

import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import API_ID, API_HASH, API_TOKEN
from modules import FileDownloader, AudioCompressor, VideoCompressor, BotStateManager
from progress_tracker import ProgressTracker


# Inicializar cliente de Pyrogram
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=API_TOKEN)

# Inicializar gestor de estado
state = BotStateManager()

# Inicializar componentes
downloader = FileDownloader(app)
audio_compressor = AudioCompressor()
video_compressor = VideoCompressor()


@app.on_message(filters.command("start"))
def start(client, message):
    """Handler del comando /start"""
    try:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Compress Audio 🎧", callback_data="compress_audio"),
             InlineKeyboardButton("Compress Video 🎥", callback_data="compress_video")]
        ])
        message.reply_text("Choose what you want to compress:", reply_markup=markup)
    except Exception as e:
        message.reply_text(f"❌ Error: {str(e)}")


@app.on_callback_query(filters.regex(r'^(compress_audio|compress_video)$'))
def file_type_callback(client, callback_query: CallbackQuery):
    """
    Handler para callbacks de selección de tipo de archivo
    Solicita al usuario enviar el archivo correspondiente
    """
    try:
        callback_data = callback_query.data
        file_type_text = "audio" if callback_data == "compress_audio" else "video"
        callback_query.message.reply_text(f"Send me a {file_type} file.")
    except Exception as e:
        callback_query.message.reply_text(f"❌ Error: {str(e)}")


@app.on_callback_query(filters.regex(r'^quality_(compress|maintain)$'))
def quality_callback(client, callback_query: CallbackQuery):
    """
    Handler para callbacks de selección de calidad de video

    CORRECCIÓN DEL BUG:
    - Usa el mensaje pendiente guardado (state.get_pending_video)
    - Limpia el estado después de procesar
    - Ya no hay bucle infinito
    """
    try:
        # Extraer la opción elegida
        quality_option = callback_query.data.replace('quality_', '')

        # Guardar la preferencia del usuario
        user_id = callback_query.from_user.id
        state.set_quality_preference(user_id, quality_option)

        # Obtener el mensaje de video pendiente (CORRECCIÓN AQUÍ)
        original_message = state.get_pending_video(user_id)

        if not original_message:
            # Si no hay mensaje pendiente, informar al usuario
            callback_query.message.edit_text(
                "❌ Error: No se encontró el video pendiente.\n\n"
                "Por favor envía el video de nuevo."
            )
            return

        # Obtener el status_message del callback (es el mensaje que muestra las opciones)
        status_message = callback_query.message

        # Procesar el video con la opción de calidad elegida
        process_video_compression(client, original_message, status_message, quality_option)

        # Limpia el mensaje pendiente después de procesar (IMPORTANTE)
        state.clear_pending_video(user_id)

    except Exception as e:
        error_message = f"❌ **Error al procesar calidad:** {str(e)}\n\n📤 Ocurrió un error inesperado."
        try:
            callback_query.message.edit_text(error_message)
        except:
            pass


@app.on_message(filters.voice | filters.audio)
def handle_audio(client, message):
    """Handler para compresión de audio"""
    # Evitar procesar el mismo mensaje múltiples veces
    if state.is_message_processed(message.id):
        return

    try:
        # Marcar mensaje como procesado
        state.mark_message_as_processed(message.id)

        # Enviar notificación inicial
        status_message = message.reply_text("📥 **Descargando archivo**...\n\nEsto puede tomar unos segundos.")

        # Obtener file_id
        file_id = message.voice.file_id if message.voice else message.audio.file_id

        # Descargar archivo con backup
        downloaded_file, backup_file = downloader.download(file_id, create_backup=True)

        # Comprimir audio
        compressed_file, error_message = audio_compressor.compress(downloaded_file, status_message)

        if error_message:
            raise Exception(error_message)

        # Actualizar estado: Enviando
        status_message.edit_text("📤 **Enviando archivo comprimido**...")

        # Verificar que el archivo comprimido tenga tamaño > 0
        if os.path.exists(compressed_file) and os.path.getsize(compressed_file) > 0:
            # Enviar archivo comprimido
            message.reply_document(compressed_file)

            # Actualizar estado: Completado
            status_message.edit_text("✅ **¡Listo!**\n\n🎉 Tu archivo de audio ha sido comprimido exitosamente.")

            # Solo eliminar el original después de éxito
            downloader.cleanup(downloaded_file, compressed_file, backup_file)
        else:
            raise Exception("El archivo comprimido tiene 0 bytes")

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló la compresión
        error_message = f"❌ **Error durante compresión de audio:** {str(e)}\n\n📤 Te envío tu archivo original."
        if status_message:
            status_message.edit_text(error_message)
        else:
            message.reply_text(error_message)

        # Enviar backup si existe
        if 'backup_file' in locals() and backup_file and os.path.exists(backup_file):
            try:
                message.reply_document(backup_file)
            except:
                pass

    finally:
        # Limpiar archivos temporales restantes
        if 'downloaded_file' in locals():
            downloader.cleanup(downloaded_file, compressed_file if 'compressed_file' in locals() else None)


@app.on_message(filters.video | filters.animation)
def handle_video(client, message):
    """
    Handler para compresión de video

    CORRECCIÓN DEL BUG:
    - Guarda el mensaje en state.set_pending_video
    - Muestra opciones de calidad
    - El callback quality_callback usa el mensaje guardado
    """
    # Evitar procesar el mismo mensaje múltiples veces
    if state.is_message_processed(message.id):
        return

    try:
        # Marcar mensaje como procesado
        state.mark_message_as_processed(message.id)

        # Enviar notificación inicial
        status_message = message.reply_text("📥 **Descargando archivo**...\n\nEsto puede tomar unos segundos.")

        # Obtener file_id
        file_id = message.video.file_id if message.video else message.animation.file_id

        # Descargar archivo con backup
        downloaded_file, backup_file = downloader.download(file_id, create_backup=True)

        # Obtener información del archivo
        file_info = downloader.get_file_info(downloaded_file)
        file_size_mb = file_info['size_mb']

        # Calcular tiempo estimado
        estimated_time_seconds = max(10, int(file_size_mb * 1.5))
        estimated_time_minutes = estimated_time_seconds // 60
        estimated_time_seconds_remainder = estimated_time_seconds % 60

        if estimated_time_minutes > 0:
            time_str = f"~{estimated_time_minutes}m {estimated_time_seconds_remainder}s"
        else:
            time_str = f"~{estimated_time_seconds}s"

        # CORRECCIÓN DEL BUG: Guardar mensaje en estado pendiente
        user_id = message.from_user.id
        state.set_pending_video(user_id, message)

        # Actualizar estado: Mostrando opciones de calidad
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 **Comprimir** (menor tamaño)", callback_data="quality_compress")],
            [InlineKeyboardButton("🎬 **Mantener calidad** (mayor tamaño)", callback_data="quality_maintain")]
        ])

        status_message.edit_text(
            f"📥 **Archivo descargado** ({file_size_mb:.1f} MB)\n\n"
            f"⏱️ Tiempo estimado: {time_str}\n\n"
            f"🎯 **Elige la opción de calidad:**",
            reply_markup=markup
        )

        # NOTA: No se limpia aquí porque el callback lo hará

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló el proceso
        error_message = f"❌ **Error durante preparación del video:** {str(e)}\n\n📤 Te envío tu archivo original."
        message.reply_text(error_message)

        # Limpiar estado pendiente si hay error
        user_id = message.from_user.id
        state.clear_pending_video(user_id)

        # Enviar backup si existe
        if 'backup_file' in locals() and backup_file and os.path.exists(backup_file):
            try:
                message.reply_document(backup_file)
            except:
                pass


def process_video_compression(client, message, status_message, quality_option):
    """
    Procesa la compresión de video con la opción de calidad elegida

    Args:
        client: Cliente de Pyrogram
        message: Mensaje original con el video
        status_message: Mensaje donde mostrar progreso (el que muestra opciones)
        quality_option: "compress" o "maintain"
    """
    downloaded_file = None
    compressed_file = None
    backup_file = None

    try:
        # Descargar archivo original
        file_id = message.video.file_id if message.video else message.animation.file_id
        downloaded_file, backup_file = downloader.download(file_id, create_backup=True)

        # Comprimir video
        is_animation = bool(message.animation)
        compressed_file, error_message = video_compressor.compress(
            downloaded_file,
            quality_option,
            status_message,
            is_animation=is_animation
        )

        if error_message:
            raise Exception(error_message)

        # Actualizar estado: Enviando
        status_message.edit_text("📤 **Enviando archivo comprimido**...")

        # Verificar que el archivo comprimido tenga tamaño > 0
        if os.path.exists(compressed_file) and os.path.getsize(compressed_file) > 0:
            # Calcular estadísticas
            compressed_size_mb = os.path.getsize(compressed_file) / 1024 / 1024
            original_size_mb = os.path.getsize(downloaded_file) / 1024 / 1024
            compression_ratio = (1 - compressed_size_mb / original_size_mb) * 100

            # Enviar video comprimido
            message.reply_video(compressed_file)

            # Actualizar estado: Completado
            if quality_option == "compress":
                completion_message = (
                    f"✅ **¡Listo!**\n\n🎉 Tu video ha sido comprimido exitosamente.\n\n"
                    f"📊 **Estadísticas:**\n   • Tamaño original: {original_size_mb:.1f} MB\n"
                    f"   • Tamaño comprimido: {compressed_size_mb:.1f} MB\n"
                    f"   • Reducción de tamaño: {compression_ratio:.1f}%"
                )
            elif quality_option == "maintain":
                params = video_compressor.get_quality_params(quality_option)
                completion_message = (
                    f"✅ **¡Listo!**\n\n🎉 Tu video ha sido comprimido manteniendo alta calidad.\n\n"
                    f"📊 **Estadísticas:**\n   • Tamaño original: {original_size_mb:.1f} MB\n"
                    f"   • Tamaño comprimido: {compressed_size_mb:.1f} MB\n"
                    f"   • Reducción de tamaño: {compression_ratio:.1f}%\n"
                    f"   • Calidad: CRF {params['crf']}, {params['preset']}"
                )
            else:
                completion_message = (
                    f"✅ **¡Listo!**\n\n🎉 Tu video ha sido comprimido exitosamente "
                    f"manteniendo la proporción original."
                )

            status_message.edit_text(completion_message)

            # Solo eliminar el original después de éxito
            downloader.cleanup(downloaded_file, compressed_file, backup_file)
        else:
            raise Exception("El archivo comprimido tiene 0 bytes")

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló el proceso
        error_message = f"❌ **Error durante compresión de video:** {str(e)}\n\n📤 Te envío tu archivo original."
        try:
            status_message.edit_text(error_message)
        except:
            message.reply_text(error_message)

        # Enviar backup si existe
        if backup_file and os.path.exists(backup_file):
            try:
                message.reply_document(backup_file)
            except:
                pass

    finally:
        # Limpiar archivos temporales restantes
        for file_path in [downloaded_file, compressed_file, backup_file]:
            if file_path:
                downloader.cleanup(file_path)


if __name__ == "__main__":
    print("🚀 Iniciando BotCompressor...")
    print("📦 Arquitectura Modular basada en principios SOLID")
    print("   - SRP: Single Responsibility Principle")
    print("   - DIP: Dependency Inversion Principle")
    print("   - OCP: Open/Closed Principle")
    app.run()
