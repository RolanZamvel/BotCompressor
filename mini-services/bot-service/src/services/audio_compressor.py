from pydub import AudioSegment
from typing import Tuple
from interfaces.media_compressor import IMediaCompressor
from config import AUDIO_CHANNELS, AUDIO_SAMPLE_RATE, AUDIO_FORMAT, AUDIO_BITRATE


class AudioCompressor(IMediaCompressor):
    """
    Compresor de archivos de audio usando Pydub.
    Implementa Single Responsibility Principle (SRP).
    Implementa Liskov Substitution Principle (LSP) con IMediaCompressor.
    """

    def compress(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Comprime un archivo de audio.

        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Cargar y configurar audio
            audio = AudioSegment.from_file(input_path)
            audio = audio.set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)

            # Exportar con compresión
            audio.export(output_path, format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)

            return True, "Audio comprimido exitosamente"
        except Exception as e:
            return False, f"Error al comprimir audio: {str(e)}"

    def get_output_format(self) -> str:
        """Retorna el formato de salida del compresor."""
        return f".{AUDIO_FORMAT}"
