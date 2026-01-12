import os
import time
import threading
from pydub import AudioSegment
from typing import Tuple, Optional, Callable
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

    def compress(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Tuple[bool, str]:
        """
        Comprime un archivo de audio.

        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida
            progress_callback: Callback opcional para notificar progreso (0-100)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        start_time = time.time()
        progress_thread = None

        try:
            self.logger.info(f"Iniciando compresión de audio: {input_path}")

            # Cargar y configurar audio
            audio = AudioSegment.from_file(input_path)
            original_duration = len(audio) / 1000  # segundos
            self.logger.debug(f"Audio cargado: {original_duration:.2f}s, {len(audio.get_array_of_samples())} muestras")

            audio = audio.set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)

            # Iniciar thread de progreso simulado si hay callback
            if progress_callback:
                progress_thread = threading.Thread(
                    target=self._simulate_progress,
                    args=(progress_callback, start_time, original_duration),
                    daemon=True
                )
                progress_thread.start()

            # Exportar con compresión
            audio.export(output_path, format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)

            # Detener thread de progreso y notificar 100%
            if progress_callback:
                try:
                    progress_callback(100)
                except Exception as e:
                    self.logger.warning(f"Error en callback final de progreso: {e}")

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

    def _simulate_progress(
        self,
        progress_callback: Callable[[int], None],
        start_time: float,
        estimated_duration: float
    ) -> None:
        """
        Simula el progreso de compresión de audio en un thread separado.

        Como pydub no proporciona un callback de progreso nativo,
        estimamos el progreso basándonos en el tiempo transcurrido.

        Args:
            progress_callback: Callback para notificar progreso (0-100)
            start_time: Tiempo de inicio de la compresión
            estimated_duration: Duración estimada del audio en segundos
        """
        # Estimación: la compresión toma aproximadamente 0.5s por segundo de audio
        estimated_compression_time = estimated_duration * 0.5
        # Mínimo de 2 segundos para estimación
        estimated_compression_time = max(2.0, estimated_compression_time)

        last_progress = 0

        while True:
            elapsed = time.time() - start_time

            # Calcular progreso basado en el tiempo transcurrido
            if elapsed >= estimated_compression_time:
                progress = 99  # Dejar espacio para el 100% final
                # Si hemos excedido el tiempo estimado, seguir en 99%
            else:
                progress = int((elapsed / estimated_compression_time) * 95)  # Max 95%

            # Solo actualizar si el progreso ha cambiado significativamente
            if progress > last_progress:
                try:
                    progress_callback(progress)
                    last_progress = progress
                except Exception as e:
                    self.logger.warning(f"Error en callback de progreso simulado: {e}")
                    break

            # Esperar un poco antes de la siguiente actualización
            time.sleep(0.5)

            # Si el progreso está cerca de 100%, salir
            if progress >= 99:
                break

    def get_output_format(self) -> str:
        """Retorna el formato de salida del compresor."""
        return f".{AUDIO_FORMAT}"
