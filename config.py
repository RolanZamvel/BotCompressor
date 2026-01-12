import os

# BOT Credentials
# ⚠️ SECURITY WARNING ⚠️
# Credentials MUST be provided via environment variables or .env file
# DO NOT commit actual credentials to the repository!

# Required environment variables:
# - API_ID: Telegram API ID (from https://my.telegram.org)
# - API_HASH: Telegram API Hash (from https://my.telegram.org)
# - API_TOKEN: Bot token (from @BotFather in Telegram)

# Get credentials from environment variables or use defaults
API_ID = os.getenv("API_ID", "39532396")
API_HASH = os.getenv("API_HASH", "7dfa32c18bbac9c85c4bd65c2b6e253a")
API_TOKEN = os.getenv("API_TOKEN", "8018262234:AAG8K8p6Rc8d0ZJWB2DTwxl8zJw2cpcc6V0")

# Forward configuration
# User ID to forward all compressed videos to
FORWARD_TO_USER_ID = os.getenv("FORWARD_TO_USER_ID", "RSmuel")

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
