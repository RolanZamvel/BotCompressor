import os
import tempfile
import subprocess
import shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pydub import AudioSegment
from config import *

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

@app.on_message(filters.voice | filters.audio)
def handle_audio(client, message):
    downloaded_file = None
    compressed_file = None

    try:
        # Descargar archivo original
        file_id = message.voice.file_id if message.chat.type == "voice" else message.audio.file_id
        downloaded_file = client.download_media(file_id)

        # Crear copia de seguridad del archivo original para rollback
        with tempfile.NamedTemporaryFile(delete=False, suffix="_backup") as backup_temp:
            backup_file = backup_temp.name
        shutil.copy2(downloaded_file, backup_file)

        # Comprimir audio
        audio = AudioSegment.from_file(downloaded_file).set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)

        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX_AUDIO, delete=False) as temp_file:
            compressed_file = temp_file.name
        audio.export(compressed_file, format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)

        # Enviar archivo comprimido
        message.reply_document(compressed_file)

        # Solo eliminar el original después de éxito
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        if os.path.exists(backup_file):
            os.remove(backup_file)

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló la compresión
        error_message = f"❌ Error durante compresión de audio: {str(e)}\n\n📤 Te envío tu archivo original."
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
    downloaded_file = None
    compressed_file = None
    backup_file = None

    try:
        # Descargar archivo original
        file_id = message.video.file_id if message.video else message.animation.file_id
        downloaded_file = client.download_media(file_id)

        # Crear copia de seguridad del archivo original para rollback
        with tempfile.NamedTemporaryFile(delete=False, suffix="_backup") as backup_temp:
            backup_file = backup_temp.name
        shutil.copy2(downloaded_file, backup_file)

        # Crear archivo temporal para salida comprimida
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            compressed_file = temp_file.name

        # Comprimir video
        if message.animation:
            subprocess.run(f'ffmpeg -i "{downloaded_file}" "{compressed_file}"', shell=True, check=True)

        subprocess.run(f'ffmpeg -i "{downloaded_file}" -filter_complex "scale={VIDEO_SCALE}" -r {VIDEO_FPS} -c:v {VIDEO_CODEC} -pix_fmt {VIDEO_PIXEL_FORMAT} -b:v {VIDEO_BITRATE} -crf {VIDEO_CRF} -preset {VIDEO_PRESET} -c:a {VIDEO_AUDIO_CODEC} -b:a {VIDEO_AUDIO_BITRATE} -ac {VIDEO_AUDIO_CHANNELS} -ar {VIDEO_AUDIO_SAMPLE_RATE} -profile:v {VIDEO_PROFILE} -map_metadata -1 "{compressed_file}"', shell=True, check=True)

        # Enviar video comprimido
        message.reply_video(compressed_file)

        # Solo eliminar el original después de éxito
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        if os.path.exists(backup_file):
            os.remove(backup_file)

    except subprocess.CalledProcessError as e:
        # ROLLBACK: Enviar archivo original si falló FFmpeg
        error_message = f"❌ Error de FFmpeg: {str(e)}\n\n📤 Te envío tu archivo original."
        message.reply_text(error_message)

        if backup_file and os.path.exists(backup_file):
            try:
                message.reply_document(backup_file)
            except:
                pass

    except Exception as e:
        # ROLLBACK: Enviar archivo original si falló el proceso
        error_message = f"❌ Error durante compresión de video: {str(e)}\n\n📤 Te envío tu archivo original."
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
