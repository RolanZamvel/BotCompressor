import subprocess
from typing import Tuple, Dict
from interfaces.media_compressor import IMediaCompressor
from strategies.compression_strategy import ICompressionStrategy
from config import (
    VIDEO_FPS, VIDEO_CODEC, VIDEO_PIXEL_FORMAT,
    VIDEO_AUDIO_CODEC, VIDEO_AUDIO_BITRATE,
    VIDEO_AUDIO_CHANNELS, VIDEO_AUDIO_SAMPLE_RATE,
    VIDEO_PROFILE, VIDEO_CRF, VIDEO_BITRATE, VIDEO_PRESET
)


class VideoCompressor(IMediaCompressor):
    """
    Compresor de archivos de video usando FFmpeg.
    Implementa Single Responsibility Principle (SRP).
    Implementa Liskov Substitution Principle (LSP) con IMediaCompressor.
    """

    def __init__(self, strategy: ICompressionStrategy = None):
        """
        Inicializa el compresor con una estrategia opcional.

        Args:
            strategy: Estrategia de compresión (opcional)
        """
        self._strategy = strategy

    def set_strategy(self, strategy: ICompressionStrategy) -> None:
        """
        Establece la estrategia de compresión.

        Args:
            strategy: Estrategia de compresión
        """
        self._strategy = strategy

    def compress(self, input_path: str, output_path: str, is_animation: bool = False) -> Tuple[bool, str]:
        """
        Comprime un archivo de video.

        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida
            is_animation: True si es una animación (GIF)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Para animaciones (GIFs), usar compresión simple
            if is_animation:
                cmd = f'ffmpeg -y -i "{input_path}" "{output_path}"'
            else:
                # Obtener parámetros de la estrategia o usar defaults
                params = self._get_compression_parameters()

                # Filtro de escala que mantiene el aspect ratio original
                scale_filter = "scale='if(gt(iw,ih),640,-2):if(gt(iw,ih),-2,360)'"

                # Construir comando FFmpeg
                cmd = (
                    f'ffmpeg -y -i "{input_path}" '
                    f'-vf "{scale_filter}" '
                    f'-r {VIDEO_FPS} '
                    f'-c:v {VIDEO_CODEC} '
                    f'-pix_fmt {VIDEO_PIXEL_FORMAT} '
                    f'-b:v {params["bitrate"]} '
                    f'-crf {params["crf"]} '
                    f'-preset {params["preset"]} '
                    f'-c:a {VIDEO_AUDIO_CODEC} '
                    f'-b:a {VIDEO_AUDIO_BITRATE} '
                    f'-ac {VIDEO_AUDIO_CHANNELS} '
                    f'-ar {VIDEO_AUDIO_SAMPLE_RATE} '
                    f'-profile:v {VIDEO_PROFILE} '
                    f'-map_metadata -1 '
                    f'"{output_path}"'
                )

            # Ejecutar comando
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

            return True, "Video comprimido exitosamente"
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            return False, f"Error de FFmpeg: {error_msg}"
        except Exception as e:
            return False, f"Error al comprimir video: {str(e)}"

    def get_output_format(self) -> str:
        """Retorna el formato de salida del compresor."""
        return ".mp4"

    def _get_compression_parameters(self) -> Dict:
        """
        Obtiene los parámetros de compresión según la estrategia configurada.

        Returns:
            Dict: Parámetros de compresión
        """
        if self._strategy:
            return self._strategy.get_parameters()

        # Valores por defecto de config.py
        return {
            "crf": VIDEO_CRF,
            "bitrate": VIDEO_BITRATE,
            "preset": VIDEO_PRESET
        }
