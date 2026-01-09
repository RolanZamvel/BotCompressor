import os
import time
from pydub import AudioSegment
from typing import Tuple
from ..interfaces.media_compressor import IMediaCompressor
from ..utils.logger import get_logger
from config import AUDIO_CHANNELS, AUDIO_SAMPLE_RATE, AUDIO_FORMAT, AUDIO_BITRATE


class AudioCompressor(IMediaCompressor):
    """
    Compresor de archivos de audio usando Pydub.
    Implementa Single Responsibility Principle (SRP).
    Implementa Liskov Substitution Principle (LSP) con IMediaCompressor.
    """

    def __init__(self):
        """Inicializa el AudioCompressor con logger."""
        self.logger = get_logger(__name__)

    def compress(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Comprime un archivo de audio.

        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida

        Returns:
            Tuple[bool, str]: (success, message)
        """
        start_time = time.time()
        try:
            self.logger.info(f"Iniciando compresión de audio: {input_path}")
            
            # Cargar y configurar audio
            audio = AudioSegment.from_file(input_path)
            original_duration = len(audio) / 1000  # segundos
            self.logger.debug(f"Audio cargado: {original_duration:.2f}s, {len(audio.get_array_of_samples())} muestras")
            
            audio = audio.set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)

            # Exportar con compresión
            audio.export(output_path, format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)

            elapsed = time.time() - start_time
            original_size = os.path.getsize(input_path) / 1024 / 1024
            compressed_size = os.path.getsize(output_path) / 1024 / 1024
            reduction_percent = (1 - compressed_size / original_size) * 100

            self.logger.info(
                f"Audio comprimido exitosamente: {original_size:.2f}MB -> {compressed_size:.2f}MB "
                f"({reduction_percent:.1f}% reducción) en {elapsed:.2f}s"
            )

            return True, "Audio comprimido exitosamente"
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(
                f"Error comprimiendo audio {input_path} (después de {elapsed:.2f}s)",
                exc_info=True
            )
            return False, f"Error al comprimir audio: {str(e)}"

    def get_output_format(self) -> str:
        """Retorna el formato de salida del compresor."""
        return f".{AUDIO_FORMAT}"
