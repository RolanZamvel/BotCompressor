import os
import tempfile
import subprocess
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
        # Descargar archivo
        file_id = message.voice.file_id if message.chat.type == "voice" else message.audio.file_id
        downloaded_file = client.download_media(file_id)

        # Comprimir audio
        audio = AudioSegment.from_file(downloaded_file).set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)

        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX_AUDIO, delete=False) as temp_file:
            compressed_file = temp_file.name
        audio.export(compressed_file, format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)

        # Enviar archivo comprimido
        message.reply_document(compressed_file)

    except Exception as e:
        # Notificar error al usuario
        error_message = f"❌ Error durante compresión de audio: {str(e)}"
        message.reply_text(error_message)

    finally:
        # Limpiar archivos temporales
        if downloaded_file and os.path.exists(downloaded_file):
            try:
                os.remove(downloaded_file)
            except:
                pass

        if compressed_file and os.path.exists(compressed_file):
            try:
                os.remove(compressed_file)
            except:
                pass

@app.on_message(filters.video | filters.animation)
def handle_media(client, message):
    downloaded_file = None
    compressed_file = None

    try:
        # Descargar archivo
        file_id = message.video.file_id if message.video else message.animation.file_id
        downloaded_file = client.download_media(file_id)

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            compressed_file = temp_file.name

        # Comprimir video
        if message.animation:
            subprocess.run(f'ffmpeg -i "{downloaded_file}" "{compressed_file}"', shell=True, check=True)

        subprocess.run(f'ffmpeg -i "{downloaded_file}" -filter_complex "scale={VIDEO_SCALE}" -r {VIDEO_FPS} -c:v {VIDEO_CODEC} -pix_fmt {VIDEO_PIXEL_FORMAT} -b:v {VIDEO_BITRATE} -crf {VIDEO_CRF} -preset {VIDEO_PRESET} -c:a {VIDEO_AUDIO_CODEC} -b:a {VIDEO_AUDIO_BITRATE} -ac {VIDEO_AUDIO_CHANNELS} -ar {VIDEO_AUDIO_SAMPLE_RATE} -profile:v {VIDEO_PROFILE} -map_metadata -1 "{compressed_file}"', shell=True, check=True)

        # Enviar video comprimido
        message.reply_video(compressed_file)

    except subprocess.CalledProcessError as e:
        error_message = f"❌ Error de FFmpeg: {str(e)}"
        message.reply_text(error_message)
    except Exception as e:
        error_message = f"❌ Error durante compresión de video: {str(e)}"
        message.reply_text(error_message)

    finally:
        # Limpiar archivos temporales
        if downloaded_file and os.path.exists(downloaded_file):
            try:
                os.remove(downloaded_file)
            except:
                pass

        if compressed_file and os.path.exists(compressed_file):
            try:
                os.remove(compressed_file)
            except:
                pass

app.run()
