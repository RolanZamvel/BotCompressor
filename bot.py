import os
import tempfile
import subprocess
import shutil
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pydub import AudioSegment
from config import *

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_detailed.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Track mensajes procesados para evitar duplicados
processed_messages = set()

@app.on_message(filters.command("start"))
def start(client, message):
    try:
        logger.info(f"Usuario {message.chat.id} inició el bot")
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Compress Audio 🎧", callback_data="compress_audio"),
                                        InlineKeyboardButton("Compress Video 🎥", callback_data="compress_video")]])
        message.reply_text("Choose what you want to compress:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error en comando /start: {str(e)}")
        message.reply_text(f"❌ Error: {str(e)}")

@app.on_callback_query()
def callback(client, callback_query: CallbackQuery):
    try:
        logger.info(f"Usuario {callback_query.message.chat.id} hizo click en botón")
        callback_query.message.reply_text("Send me a file.")
    except Exception as e:
        logger.error(f"Error en callback query: {str(e)}")
        callback_query.message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.voice | filters.audio)
def handle_audio(client, message):
    downloaded_file = None
    compressed_file = None
    backup_file = None
    status_message = None

    # Evitar procesar el mismo mensaje múltiples veces
    if message.id in processed_messages:
        logger.info(f"Mensaje {message.id} ya procesado, ignorando")
        return
    
    try:
        logger.info(f"[AUDIO] Usuario {message.chat.id} - Mensaje {message.id} - Iniciando procesamiento")
        
        # Marcar mensaje como procesado
        processed_messages.add(message.id)
        
        # Enviar notificación inicial
        logger.info(f"[AUDIO] Enviando notificación inicial")
        status_message = message.reply_text("📥 **Descargando archivo**...\n\nEsto puede tomar unos segundos.")

        # Descargar archivo original
        logger.info(f"[AUDIO] Iniciando descarga del archivo")
        file_id = message.voice.file_id if message.chat.type == "voice" else message.audio.file_id
        downloaded_file = client.download_media(file_id)
        logger.info(f"[AUDIO] Archivo descargado: {downloaded_file}")
        logger.info(f"[AUDIO] Tamaño del archivo: {os.path.getsize(downloaded_file) / 1024 / 1024:.2f} MB")

        # Crear copia de seguridad del archivo original para rollback
        logger.info(f"[AUDIO] Creando copia de seguridad (backup)")
        with tempfile.NamedTemporaryFile(delete=False, suffix="_backup") as backup_temp:
            backup_file = backup_temp.name
        shutil.copy2(downloaded_file, backup_file)
        logger.info(f"[AUDIO] Backup creado: {backup_file}")

        # Actualizar estado: Comprimiendo
        logger.info(f"[AUDIO] Iniciando compresión de audio")
        status_message.edit_text("🔄 **Comprimiendo audio**...\n\n⏱️ Esto puede tomar un momento dependiendo del tamaño del archivo.")

        # Comprimir audio
        audio = AudioSegment.from_file(downloaded_file).set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)

        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX_AUDIO, delete=False) as temp_file:
            compressed_file = temp_file.name
        audio.export(compressed_file, format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)
        logger.info(f"[AUDIO] Audio comprimido: {compressed_file}")
        logger.info(f"[AUDIO] Tamaño del archivo comprimido: {os.path.getsize(compressed_file) / 1024 / 1024:.2f} MB")

        # Actualizar estado: Enviando
        logger.info(f"[AUDIO] Enviando archivo comprimido al usuario")
        status_message.edit_text("📤 **Enviando archivo comprimido**...")

        # Verificar que el archivo comprimido tenga tamaño > 0
        if os.path.exists(compressed_file) and os.path.getsize(compressed_file) > 0:
            # Enviar archivo comprimido
            message.reply_document(compressed_file)
            logger.info(f"[AUDIO] Archivo comprimido enviado exitosamente")

            # Actualizar estado: Completado
            status_message.edit_text("✅ **¡Listo!**\n\n🎉 Tu archivo de audio ha sido comprimido exitosamente.")
            logger.info(f"[AUDIO] Procesamiento completado exitosamente")

            # Solo eliminar el original después de éxito
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
                logger.info(f"[AUDIO] Archivo original eliminado")
            if os.path.exists(backup_file):
                os.remove(backup_file)
                logger.info(f"[AUDIO] Backup eliminado")
        else:
            error_msg = "El archivo comprimido tiene 0 bytes"
            logger.error(f"[AUDIO] {error_msg}")
            raise Exception(error_msg)

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló la compresión
        logger.error(f"[AUDIO] Error durante compresión: {str(e)}")
        error_message = f"❌ **Error durante compresión de audio:** {str(e)}\n\n📤 Te envío tu archivo original."
        
        try:
            if status_message:
                status_message.edit_text(error_message)
            else:
                message.reply_text(error_message)
        except Exception as edit_error:
            logger.error(f"[AUDIO] Error al editar mensaje: {str(edit_error)}")
        
        if backup_file and os.path.exists(backup_file):
            try:
                logger.info(f"[AUDIO] Enviando archivo original (rollback)")
                message.reply_document(backup_file)
            except:
                logger.error(f"[AUDIO] Error al enviar backup: {str(e)}")

    finally:
        # Limpiar archivos temporales restantes
        logger.info(f"[AUDIO] Limpiando archivos temporales")
        for file_path in [downloaded_file, compressed_file, backup_file]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    logger.error(f"[AUDIO] Error al eliminar archivo {file_path}")
        logger.info(f"[AUDIO] Procesamiento finalizado")

@app.on_message(filters.video | filters.animation)
def handle_media(client, message):
    downloaded_file = None
    compressed_file = None
    backup_file = None
    status_message = None

    # Evitar procesar el mismo mensaje múltiples veces
    if message.id in processed_messages:
        logger.info(f"Mensaje {message.id} ya procesado, ignorando")
        return
    
    try:
        logger.info(f"[VIDEO] Usuario {message.chat.id} - Mensaje {message.id} - Iniciando procesamiento")
        
        # Marcar mensaje como procesado
        processed_messages.add(message.id)
        
        # Enviar notificación inicial
        logger.info(f"[VIDEO] Enviando notificación inicial")
        status_message = message.reply_text("📥 **Descargando archivo**...\n\nEsto puede tomar unos segundos.")

        # Descargar archivo original
        logger.info(f"[VIDEO] Iniciando descarga del archivo")
        file_id = message.video.file_id if message.video else message.animation.file_id
        downloaded_file = client.download_media(file_id)
        logger.info(f"[VIDEO] Archivo descargado: {downloaded_file}")
        logger.info(f"[VIDEO] Tamaño del archivo: {os.path.getsize(downloaded_file) / 1024 / 1024:.2f} MB")

        # Crear copia de seguridad del archivo original para rollback
        logger.info(f"[VIDEO] Creando copia de seguridad (backup)")
        with tempfile.NamedTemporaryFile(delete=False, suffix="_backup") as backup_temp:
            backup_file = backup_temp.name
        shutil.copy2(downloaded_file, backup_file)
        logger.info(f"[VIDEO] Backup creado: {backup_file}")

        # Crear archivo temporal para salida comprimida
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            compressed_file = temp_file.name

        # Eliminar archivo temporal si existe para evitar conflicto de FFmpeg
        if os.path.exists(compressed_file):
            os.remove(compressed_file)

        # Actualizar estado: Comprimiendo
        logger.info(f"[VIDEO] Iniciando compresión de video")
        status_message.edit_text("🔄 **Comprimiendo video**...\n\n⏱️ Esto puede tomar varios minutos para archivos grandes.")

        # Comprimir video (con -y para forzar sobrescrita sin confirmación)
        # Filtro de escala que mantiene el aspect ratio original
        scale_filter = "scale='if(gt(iw,ih),640,-2):if(gt(iw,ih),-2,360)'"

        if message.animation:
            logger.info(f"[VIDEO] Procesando animación con FFmpeg")
            subprocess.run(f'ffmpeg -y -i "{downloaded_file}" "{compressed_file}"', shell=True, check=True)
        else:
            logger.info(f"[VIDEO] Procesando video con FFmpeg y filtro de escala")
            subprocess.run(f'ffmpeg -y -i "{downloaded_file}" -vf "{scale_filter}" -r {VIDEO_FPS} -c:v {VIDEO_CODEC} -pix_fmt {VIDEO_PIXEL_FORMAT} -b:v {VIDEO_BITRATE} -crf {VIDEO_CRF} -preset {VIDEO_PRESET} -c:a {VIDEO_AUDIO_CODEC} -b:a {VIDEO_AUDIO_BITRATE} -ac {VIDEO_AUDIO_CHANNELS} -ar {VIDEO_AUDIO_SAMPLE_RATE} -profile:v {VIDEO_PROFILE} -map_metadata -1 "{compressed_file}"', shell=True, check=True)
        
        logger.info(f"[VIDEO] Video comprimido: {compressed_file}")
        logger.info(f"[VIDEO] Tamaño del archivo comprimido: {os.path.getsize(compressed_file) / 1024 / 1024:.2f} MB")

        # Actualizar estado: Enviando
        logger.info(f"[VIDEO] Enviando archivo comprimido al usuario")
        status_message.edit_text("📤 **Enviando archivo comprimido**...")

        # Verificar que el archivo comprimido tenga tamaño > 0
        if os.path.exists(compressed_file) and os.path.getsize(compressed_file) > 0:
            # Enviar video comprimido
            message.reply_video(compressed_file)
            logger.info(f"[VIDEO] Archivo comprimido enviado exitosamente")

            # Actualizar estado: Completado
            status_message.edit_text("✅ **¡Listo!**\n\n🎉 Tu video ha sido comprimido exitosamente manteniendo la proporción original.")
            logger.info(f"[VIDEO] Procesamiento completado exitosamente")

            # Solo eliminar el original después de éxito
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
                logger.info(f"[VIDEO] Archivo original eliminado")
            if os.path.exists(backup_file):
                os.remove(backup_file)
                logger.info(f"[VIDEO] Backup eliminado")
        else:
            error_msg = "El archivo comprimido tiene 0 bytes"
            logger.error(f"[VIDEO] {error_msg}")
            raise Exception(error_msg)

    except subprocess.CalledProcessError as e:
        # ROLLBACK: Enviar archivo original si falló FFmpeg
        logger.error(f"[VIDEO] Error de FFmpeg: {str(e)}")
        error_message = f"❌ **Error de FFmpeg:** {str(e)}\n\n📤 Te envío tu archivo original."
        
        try:
            if status_message:
                status_message.edit_text(error_message)
            else:
                message.reply_text(error_message)
        except Exception as edit_error:
            logger.error(f"[VIDEO] Error al editar mensaje: {str(edit_error)}")
        
        if backup_file and os.path.exists(backup_file):
            try:
                logger.info(f"[VIDEO] Enviando archivo original (rollback)")
                message.reply_document(backup_file)
            except:
                logger.error(f"[VIDEO] Error al enviar backup: {str(e)}")

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló el proceso
        logger.error(f"[VIDEO] Error durante compresión de video: {str(e)}")
        error_message = f"❌ **Error durante compresión de video:** {str(e)}\n\n📤 Te envío tu archivo original."
        
        try:
            if status_message:
                status_message.edit_text(error_message)
            else:
                message.reply_text(error_message)
        except Exception as edit_error:
            logger.error(f"[VIDEO] Error al editar mensaje: {str(edit_error)}")
        
        if backup_file and os.path.exists(backup_file):
            try:
                logger.info(f"[VIDEO] Enviando archivo original (rollback)")
                message.reply_document(backup_file)
            except:
                logger.error(f"[VIDEO] Error al enviar backup: {str(e)}")

    finally:
        # Limpiar archivos temporales restantes
        logger.info(f"[VIDEO] Limpiando archivos temporales")
        for file_path in [downloaded_file, compressed_file, backup_file]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    logger.error(f"[VIDEO] Error al eliminar archivo {file_path}")
        logger.info(f"[VIDEO] Procesamiento finalizado")

app.run()
