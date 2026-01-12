import os
import subprocess
import time
import re
from typing import Tuple, Dict, Optional, Callable
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

    def compress(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
        is_animation: bool = False
    ) -> Tuple[bool, str]:
        """
        Comprime un archivo de video.

        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida
            progress_callback: Callback opcional para notificar progreso (0-100)
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
                result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            else:
                self.logger.info(f"Comprimiendo video: {input_path}")

                # Obtener parámetros de la estrategia o usar defaults
                params = self._get_compression_parameters()

                # Filtro de escala que mantiene el aspect ratio original
                scale_filter = "scale='if(gt(iw,ih),640,-2):if(gt(iw,ih),-2,360)'"

                # Construir comando FFmpeg como lista para subprocess.Popen
                cmd = [
                    'ffmpeg',
                    '-y',  # Sobrescribir sin preguntar
                    '-i', input_path,
                    '-vf', scale_filter,
                    '-r', str(VIDEO_FPS),
                    '-c:v', VIDEO_CODEC,
                    '-pix_fmt', VIDEO_PIXEL_FORMAT,
                    '-b:v', params["bitrate"],
                    '-crf', str(params["crf"]),
                    '-preset', params["preset"],
                    '-c:a', VIDEO_AUDIO_CODEC,
                    '-b:a', VIDEO_AUDIO_BITRATE,
                    '-ac', str(VIDEO_AUDIO_CHANNELS),
                    '-ar', str(VIDEO_AUDIO_SAMPLE_RATE),
                    '-profile:v', VIDEO_PROFILE,
                    '-map_metadata', '-1',
                    output_path
                ]

                self.logger.debug(f"Ejecutando FFmpeg: {' '.join(cmd)}")

                # Ejecutar FFmpeg con captura de progreso en tiempo real
                result = self._compress_with_progress(cmd, progress_callback)

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

    def _compress_with_progress(
        self,
        cmd: list,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> subprocess.CompletedProcess:
        """
        Ejecuta FFmpeg capturando el progreso en tiempo real desde stderr.

        Args:
            cmd: Comando FFmpeg como lista de argumentos
            progress_callback: Callback opcional para notificar progreso (0-100)

        Returns:
            subprocess.CompletedProcess: Resultado de la ejecución

        Raises:
            subprocess.CalledProcessError: Si FFmpeg falla
        """
        # Ejecutar FFmpeg y capturar stderr (donde escribe el progreso)
        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        duration = None
        stderr_output = []

        while True:
            line = process.stderr.readline()
            if not line:
                break

            stderr_output.append(line)

            # Buscar duración total del video (solo una vez)
            if duration is None:
                match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)', line)
                if match:
                    h, m, s = map(float, match.groups())
                    duration = int(h * 3600 + m * 60 + s)
                    self.logger.debug(f"Duración del video detectada: {duration}s")

            # Buscar el tiempo actual procesado
            match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d+)', line)
            if match and duration and duration > 0:
                h, m, s = map(float, match.groups())
                current_time = h * 3600 + m * 60 + s
                progress = (current_time / duration) * 100

                # Limitar el progreso a 100%
                progress = min(progress, 100)

                # Llamar al callback si existe
                if progress_callback:
                    try:
                        progress_callback(int(progress))
                    except Exception as e:
                        self.logger.warning(f"Error en callback de progreso: {e}")

            # Loguear errores o advertencias
            if 'error' in line.lower() or 'warning' in line.lower():
                self.logger.warning(f"FFmpeg: {line.strip()}")

        process.wait()

        # Verificar el código de salida
        if process.returncode != 0:
            stderr_text = ''.join(stderr_output)
            raise subprocess.CalledProcessError(
                process.returncode,
                cmd,
                stderr=stderr_text
            )

        # Retornar un objeto CompletedProcess simulado
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout='',
            stderr=''.join(stderr_output)
        )

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
