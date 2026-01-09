import os

# BOT Credentials
# ⚠️ ADVERTENCIA DE SEGURIDAD ⚠️
# Estas credenciales están en el código solo para facilitar el DESARROLLO.
# ANTES DE HACER DEPLOY A PRODUCCIÓN, DEBES:
# 1. Borrar las credenciales de este archivo
# 2. Usar variables de entorno (.env o variables del sistema)
# 3. Agregar .env a .gitignore (ya está configurado)
# 4. Nunca commitear credenciales reales

# Para desarrollo, usa las credenciales aquí.
# Para producción, usa variables de entorno: API_ID, API_HASH, API_TOKEN
API_ID = os.getenv("API_ID", "39532396")
API_HASH = os.getenv("API_HASH", "7dfa32c18bbac9c85c4bd65c2b6e253a")
API_TOKEN = os.getenv("API_TOKEN", "8018262234:AAH2vS1Pdwqc3fbAbGaRa9oT5slfki2QsEc")

# NOTA: Si quieres usar variables de entorno en lugar de las credenciales por defecto,
# simplemente crea un archivo .env con tus credenciales o exporta las variables de entorno.
# El archivo .env está en .gitignore y no se subirá a GitHub.

# Audio compression settings
AUDIO_BITRATE = "32k"
AUDIO_FORMAT = "mp3"
AUDIO_CHANNELS = 1
AUDIO_SAMPLE_RATE = 44100

# Video compression settings
VIDEO_SCALE = "640:360"
VIDEO_FPS = 24
VIDEO_CODEC = "libx265"
VIDEO_BITRATE = "100k"
VIDEO_CRF = 30
VIDEO_PRESET = "ultrafast"
VIDEO_PIXEL_FORMAT = "yuv420p"
VIDEO_PROFILE = "main"
VIDEO_AUDIO_CODEC = "aac"
VIDEO_AUDIO_BITRATE = "64k"
VIDEO_AUDIO_CHANNELS = 1
VIDEO_AUDIO_SAMPLE_RATE = 44100

# Temporary file settings
TEMP_FILE_SUFFIX_AUDIO = ".mp3"
TEMP_FILE_SUFFIX_VIDEO = ".mp4"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR = os.getenv("LOG_DIR", "logs")
CONSOLE_LOG_LEVEL = os.getenv("CONSOLE_LOG_LEVEL", "INFO")
FILE_LOG_LEVEL = os.getenv("FILE_LOG_LEVEL", "DEBUG")
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_FILE_BACKUP_COUNT = 5
