import os
import subprocess
import time
from typing import Tuple, Dict
from ..interfaces.media_compressor import IMediaCompressor
from ..strategies.compression_strategy import ICompressionStrategy
from ..utils.logger import get_logger
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
        self.logger = get_logger(__name__)

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
        start_time = time.time()
        try:
            # Para animaciones (GIFs), usar compresión simple
            if is_animation:
                self.logger.info(f"Comprimiendo animación (GIF): {input_path}")
                cmd = f'ffmpeg -y -i "{input_path}" "{output_path}"'
            else:
                self.logger.info(f"Comprimiendo video: {input_path}")
                
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

            self.logger.debug(f"Ejecutando FFmpeg: {cmd}")

            # Ejecutar comando
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

            elapsed = time.time() - start_time
            original_size = os.path.getsize(input_path) / 1024 / 1024
            compressed_size = os.path.getsize(output_path) / 1024 / 1024
            reduction_percent = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

            self.logger.info(
                f"{'Animación' if is_animation else 'Video'} comprimido exitosamente: "
                f"{original_size:.2f}MB -> {compressed_size:.2f}MB "
                f"({reduction_percent:.1f}% reducción) en {elapsed:.2f}s"
            )

            return True, f"{'Animación' if is_animation else 'Video'} comprimido exitosamente"
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            error_msg = e.stderr if e.stderr else str(e)
            self.logger.error(
                f"FFmpeg falló para {input_path} (después de {elapsed:.2f}s). "
                f"Stderr: {error_msg}",
                exc_info=False  # No incluir stack trace para subprocess errors
            )
            return False, f"Error de FFmpeg: {error_msg}"
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(
                f"Error comprimiendo {input_path} (después de {elapsed:.2f}s)",
                exc_info=True
            )
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
