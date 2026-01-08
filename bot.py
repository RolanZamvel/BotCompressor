import os
import tempfile
import subprocess
import shutil
import threading
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pydub import AudioSegment
from config import *
from progress_tracker import ProgressTracker

# Track mensajes procesados para evitar duplicados
processed_messages = set()

# Almacenar preferencias de calidad del usuario
# Formato: {user_id: "compress" o "maintain"}
user_quality_preferences = {}

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=API_TOKEN)

@app.on_message(filters.command("start"))
def start(client, message):
    try:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Compress Audio 🎧", callback_data="compress_audio"),
                                        InlineKeyboardButton("Compress Video 🎥", callback_data="compress_video")]])
        message.reply_text("Choose what you want to compress:", reply_markup=markup)
    except Exception as e:
        message.reply_text(f"❌ Error: {str(e)}")

@app.on_callback_query()
def callback(client, callback_query: CallbackQuery):
    try:
        callback_query.message.reply_text("Send me a file.")
    except Exception as e:
        callback_query.message.reply_text(f"❌ Error: {str(e)}")

# Handler de callback para opciones de calidad
@app.on_callback_query(filters.regex(r'^quality_(compress|maintain)$'))
def quality_callback(client, callback_query: CallbackQuery):
    try:
        # Extraer la opción elegida
        quality_option = callback_query.data.replace('quality_', '')
        
        # Guardar la preferencia del usuario
        user_id = callback_query.from_user.id
        user_quality_preferences[user_id] = quality_option
        
        # Obtener el mensaje original
        original_message = callback_query.message
        
        # Procesar el video con la opción de calidad elegida
        process_video_with_quality(client, original_message, quality_option)
        
    except Exception as e:
        error_message = f"❌ **Error al procesar calidad:** {str(e)}\n\n📤 Ocurrió un error inesperado."
        try:
            callback_query.message.edit_text(error_message)
        except:
            pass

@app.on_message(filters.voice | filters.audio)
def handle_audio(client, message):
    downloaded_file = None
    compressed_file = None
    backup_file = None
    status_message = None

    # Evitar procesar el mismo mensaje múltiples veces
    if message.id in processed_messages:
        return
    
    try:
        # Marcar mensaje como procesado
        processed_messages.add(message.id)
        
        # Enviar notificación inicial
        status_message = message.reply_text("📥 **Descargando archivo**...\n\nEsto puede tomar unos segundos.")

        # Descargar archivo original
        file_id = message.voice.file_id if message.chat.type == "voice" else message.audio.file_id
        downloaded_file = client.download_media(file_id)

        # Crear copia de seguridad del archivo original para rollback
        with tempfile.NamedTemporaryFile(delete=False, suffix="_backup") as backup_temp:
            backup_file = backup_temp.name
        shutil.copy2(downloaded_file, backup_file)

        # Calcular tamaño del archivo para estimar tiempo
        file_size_mb = os.path.getsize(downloaded_file) / 1024 / 1024
        file_size_bytes = os.path.getsize(downloaded_file)

        # Estimar tiempo de compresión basado en tamaño
        # Audio: ~0.5 segundos por MB
        estimated_time_seconds = max(5, int(file_size_mb * 0.5))

        # Crear tracker de progreso
        tracker = ProgressTracker(
            total_size_bytes=file_size_bytes,
            task_name="Comprimiendo audio",
            status_message=status_message,
            initial_message=f"🔄 **Comprimiendo audio**...\n\n⏱️ Tiempo estimado: ~{estimated_time_seconds}s\n\nEl procesamiento continuá. Por favor espera..."
        )

        # Iniciar tracker en background
        tracker.start()

        # Comprimir audio en un hilo separado para permitir actualizaciones de progreso
        compression_complete = threading.Event()
        compression_error = [None]
        compressed_file_result = [None]

        def compress_audio():
            try:
                audio = AudioSegment.from_file(downloaded_file).set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)

                with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX_AUDIO, delete=False) as temp_file:
                    compressed_file_result[0] = temp_file.name
                audio.export(compressed_file_result[0], format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)
            except Exception as e:
                compression_error[0] = e
            finally:
                compression_complete.set()

        # Iniciar compresión en background
        compress_thread = threading.Thread(target=compress_audio)
        compress_thread.start()

        # Actualizar progreso basado en tiempo estimado
        start_time = time.time()
        while not compression_complete.is_set():
            elapsed = time.time() - start_time
            # Estimar progreso basado en tiempo transcurrido
            estimated_progress = min((elapsed / estimated_time_seconds) * 100, 100)
            # Convertir a tamaño procesado estimado
            processed_size = int((estimated_progress / 100) * file_size_bytes)
            tracker.update(processed_size)
            time.sleep(0.5)

        # Esperar que termine el hilo de compresión
        compress_thread.join(timeout=5)

        # Detener tracker
        tracker.stop()

        # Verificar si hubo error en compresión
        if compression_error[0]:
            raise compression_error[0]

        # Obtener archivo comprimido del resultado
        compressed_file = compressed_file_result[0]

        # Actualizar estado: Enviando
        status_message.edit_text("📤 **Enviando archivo comprimido**...")

        # Verificar que el archivo comprimido tenga tamaño > 0
        if os.path.exists(compressed_file) and os.path.getsize(compressed_file) > 0:
            # Enviar archivo comprimido
            message.reply_document(compressed_file)

            # Actualizar estado: Completado
            status_message.edit_text("✅ **¡Listo!**\n\n🎉 Tu archivo de audio ha sido comprimido exitosamente.")

            # Solo eliminar el original después de éxito
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            if os.path.exists(backup_file):
                os.remove(backup_file)
        else:
            raise Exception("El archivo comprimido tiene 0 bytes")

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló la compresión
        error_message = f"❌ **Error durante compresión de audio:** {str(e)}\n\n📤 Te envío tu archivo original."
        if status_message:
            status_message.edit_text(error_message)
        else:
            message.reply_text(error_message)

        if backup_file and os.path.exists(backup_file):
            try:
                message.reply_document(backup_file)
            except:
                pass

    finally:
        # Limpiar archivos temporales restantes
        for file_path in [downloaded_file, compressed_file, backup_file]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

@app.on_message(filters.video | filters.animation)
def handle_media(client, message):
    # Evitar procesar el mismo mensaje múltiples veces
    if message.id in processed_messages:
        return
    
    try:
        # Marcar mensaje como procesado
        processed_messages.add(message.id)
        
        # Enviar notificación inicial
        status_message = message.reply_text("📥 **Descargando archivo**...\n\nEsto puede tomar unos segundos.")

        # Descargar archivo original
        file_id = message.video.file_id if message.video else message.animation.file_id
        downloaded_file = client.download_media(file_id)

        # Crear copia de seguridad del archivo original para rollback
        with tempfile.NamedTemporaryFile(delete=False, suffix="_backup") as backup_temp:
            backup_file = backup_temp.name
        shutil.copy2(downloaded_file, backup_file)

        # Calcular tamaño del archivo para estimar tiempo
        file_size_mb = os.path.getsize(downloaded_file) / 1024 / 1024
        
        # Crear archivo temporal para salida comprimida
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            compressed_file = temp_file.name

        # Eliminar archivo temporal si existe para evitar conflicto de FFmpeg
        if os.path.exists(compressed_file):
            os.remove(compressed_file)

        # Calcular tiempo estimado (usará el más lento como base)
        estimated_time_seconds = max(10, int(file_size_mb * 1.5))  # 1.5s por MB (puede mantener calidad)
        estimated_time_minutes = estimated_time_seconds // 60
        estimated_time_seconds_remainder = estimated_time_seconds % 60
        
        if estimated_time_minutes > 0:
            time_str = f"~{estimated_time_minutes}m {estimated_time_seconds_remainder}s"
        else:
            time_str = f"~{estimated_time_seconds}s"

        # Actualizar estado: Mostrando opciones de calidad
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 **Comprimir** (menor tamaño)", callback_data="quality_compress")],
            [InlineKeyboardButton("🎬 **Mantener calidad** (mayor tamaño)", callback_data="quality_maintain")]
        ])
        
        status_message.edit_text(
            f"📥 **Archivo descargado** ({file_size_mb:.1f} MB)\n\n"
            f"⏱️ Tiempo estimado: {time_str}\n\n"
            f"🎯 **Elije la opción de calidad:**",
            reply_markup=markup
        )

        # Guardar referencia del mensaje para poder usarlo en el callback
        # Esto se manejará a través del callback_query

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló el proceso
        error_message = f"❌ **Error durante preparación del video:** {str(e)}\n\n📤 Te envío tu archivo original."
        message.reply_text(error_message)

        if backup_file and os.path.exists(backup_file):
            try:
                message.reply_document(backup_file)
            except:
                pass

def process_video_with_quality(client, message, quality_option):
    """
    Procesa el video con la opción de calidad elegida
    quality_option: "compress" o "maintain"
    """
    downloaded_file = None
    compressed_file = None
    backup_file = None
    status_message = None

    try:
        # Descargar archivo original (si no ya se descargó)
        file_id = message.video.file_id if message.video else message.animation.file_id
        downloaded_file = client.download_media(file_id)

        # Crear copia de seguridad del archivo original para rollback
        with tempfile.NamedTemporaryFile(delete=False, suffix="_backup") as backup_temp:
            backup_file = backup_temp.name
        shutil.copy2(downloaded_file, backup_file)

        # Crear archivo temporal para salida comprimida
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            compressed_file = temp_file.name

        # Eliminar archivo temporal si existe para evitar conflicto de FFmpeg
        if os.path.exists(compressed_file):
            os.remove(compressed_file)

        # Calcular tamaño del archivo para estimar tiempo
        file_size_mb = os.path.getsize(downloaded_file) / 1024 / 1024
        file_size_bytes = os.path.getsize(downloaded_file)
        
        # Seleccionar parámetros según la opción de calidad
        if quality_option == "compress":
            # Comprimir más (menor calidad, menor tamaño)
            # CRF: 28 (más alta compresión)
            # BITRATE: 500k (menor bitrate)
            # PRESET: medium (compresión media)
            crf = 28
            bitrate = "500k"
            preset = "medium"
            quality_desc = "Comprimiendo (mayor compresión)"
            estimated_factor = 1.0  # 1s por MB (más rápido)
        elif quality_option == "maintain":
            # Mantener calidad (menor compresión, mayor tamaño)
            # CRF: 18 (mucho mejor calidad)
            # BITRATE: 2M (mayor bitrate)
            # PRESET: slow (mejor calidad)
            crf = 18
            bitrate = "2M"
            preset = "slow"
            quality_desc = "Manteniendo calidad (menor compresión)"
            estimated_factor = 1.5  # 1.5s por MB (más lento)
        else:
            # Usar valores por defecto (configuración actual)
            crf = VIDEO_CRF
            bitrate = VIDEO_BITRATE
            preset = VIDEO_PRESET
            quality_desc = f"Comprimiendo (CRF: {crf})"
            estimated_factor = 1.5

        # Calcular tiempo estimado
        estimated_time_seconds = max(10, int(file_size_mb * estimated_factor))

        # Crear tracker de progreso
        tracker = ProgressTracker(
            total_size_bytes=file_size_bytes,
            task_name=f"🎬 {quality_desc}",
            status_message=status_message,
            initial_message=f"🔄 **{quality_desc}**...\n\n⏱️ Tiempo estimado: ~{estimated_time_seconds}s\n\nEsto puede tomar varios minutos para archivos grandes.",
            show_speed=True
        )

        # Iniciar tracker en background
        tracker.start()

        # Filtro de escala que mantiene el aspect ratio original
        scale_filter = "scale='if(gt(iw,ih),640,-2):if(gt(iw,ih),-2,360)'"

        # Comprimir video en un hilo separado para permitir actualizaciones de progreso
        compression_complete = threading.Event()
        compression_error = [None]
        compressed_file_result = [None]

        def compress_video():
            try:
                # Crear archivo temporal para salida comprimida
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                    compressed_file_result[0] = temp_file.name

                # Eliminar archivo temporal si existe para evitar conflicto de FFmpeg
                if os.path.exists(compressed_file_result[0]):
                    os.remove(compressed_file_result[0])

                # Comprimir video (con -y para forzar sobrescrita sin confirmación)
                if message.animation:
                    subprocess.run(f'ffmpeg -y -i "{downloaded_file}" "{compressed_file_result[0]}"', shell=True, check=True)
                else:
                    subprocess.run(f'ffmpeg -y -i "{downloaded_file}" -vf "{scale_filter}" -r {VIDEO_FPS} -c:v {VIDEO_CODEC} -pix_fmt {VIDEO_PIXEL_FORMAT} -b:v {bitrate} -crf {crf} -preset {preset} -c:a {VIDEO_AUDIO_CODEC} -b:a {VIDEO_AUDIO_BITRATE} -ac {VIDEO_AUDIO_CHANNELS} -ar {VIDEO_AUDIO_SAMPLE_RATE} -profile:v {VIDEO_PROFILE} -map_metadata -1 "{compressed_file_result[0]}"', shell=True, check=True)
            except Exception as e:
                compression_error[0] = e
            finally:
                compression_complete.set()

        # Iniciar compresión en background
        compress_thread = threading.Thread(target=compress_video)
        compress_thread.start()

        # Actualizar progreso basado en tiempo estimado
        start_time = time.time()
        while not compression_complete.is_set():
            elapsed = time.time() - start_time
            # Estimar progreso basado en tiempo transcurrido
            estimated_progress = min((elapsed / estimated_time_seconds) * 100, 100)
            # Convertir a tamaño procesado estimado
            processed_size = int((estimated_progress / 100) * file_size_bytes)
            tracker.update(processed_size)
            time.sleep(0.5)

        # Esperar que termine el hilo de compresión
        compress_thread.join(timeout=30)

        # Detener tracker
        tracker.stop()

        # Verificar si hubo error en compresión
        if compression_error[0]:
            raise compression_error[0]

        # Obtener archivo comprimido del resultado
        compressed_file = compressed_file_result[0]

        # Actualizar estado: Enviando
        status_message.edit_text("📤 **Enviando archivo comprimido**...")

        # Verificar que el archivo comprimido tenga tamaño > 0
        if os.path.exists(compressed_file) and os.path.getsize(compressed_file) > 0:
            # Calcular tamaño del archivo comprimido
            compressed_size_mb = os.path.getsize(compressed_file) / 1024 / 1024
            original_size_mb = os.path.getsize(downloaded_file) / 1024 / 1024
            compression_ratio = (1 - compressed_size_mb / original_size_mb) * 100
            
            # Enviar video comprimido
            message.reply_video(compressed_file)

            # Actualizar estado: Completado
            if quality_option == "compress":
                completion_message = f"✅ **¡Listo!**\n\n🎉 Tu video ha sido comprimido exitosamente.\n\n📊 **Estadísticas:**\n   • Tamaño original: {original_size_mb:.1f} MB\n   • Tamaño comprimido: {compressed_size_mb:.1f} MB\n   • Reducción de tamaño: {compression_ratio:.1f}%"
            elif quality_option == "maintain":
                completion_message = f"✅ **¡Listo!**\n\n🎉 Tu video ha sido comprimido manteniendo alta calidad.\n\n📊 **Estadísticas:**\n   • Tamaño original: {original_size_mb:.1f} MB\n   • Tamaño comprimido: {compressed_size_mb:.1f} MB\n   • Reducción de tamaño: {compression_ratio:.1f}%\n   • Calidad: CRF {crf}, {preset}"
            else:
                completion_message = f"✅ **¡Listo!**\n\n🎉 Tu video ha sido comprimido exitosamente manteniendo la proporción original."

            status_message.edit_text(completion_message)

            # Solo eliminar el original después de éxito
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            if os.path.exists(backup_file):
                os.remove(backup_file)
        else:
            raise Exception("El archivo comprimido tiene 0 bytes")

    except subprocess.CalledProcessError as e:
        # ROLLBACK: Enviar archivo original si falló FFmpeg
        error_message = f"❌ **Error de FFmpeg:** {str(e)}\n\n📤 Te envío tu archivo original."
        try:
            status_message.edit_text(error_message)
        except:
            message.reply_text(error_message)

        if backup_file and os.path.exists(backup_file):
            try:
                message.reply_document(backup_file)
            except:
                pass

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló el proceso
        error_message = f"❌ **Error durante compresión de video:** {str(e)}\n\n📤 Te envío tu archivo original."
        try:
            status_message.edit_text(error_message)
        except:
            message.reply_text(error_message)

        if backup_file and os.path.exists(backup_file):
            try:
                message.reply_document(backup_file)
            except:
                pass

    finally:
        # Limpiar archivos temporales restantes
        for file_path in [downloaded_file, compressed_file, backup_file]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

app.run()
