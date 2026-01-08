"""
Módulo de compresión de audio para BotCompressor

Responsabilidades (SRP):
- Comprimir archivos de audio
- Configurar parámetros de compresión
- Gestionar archivos temporales de salida
"""

import os
import tempfile
import threading
import time
from typing import Tuple, Optional
from pydub import AudioSegment
from config import (
    AUDIO_BITRATE,
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_RATE,
    AUDIO_FORMAT,
    TEMP_FILE_SUFFIX_AUDIO
)
from progress_tracker import ProgressTracker


class AudioCompressor:
    """
    Clase responsable de comprimir archivos de audio
    """

    def __init__(self):
        """Inicializa el compresor de audio"""
        pass

    def compress(
        self,
        input_file: str,
        status_message: object
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Comprime un archivo de audio

        Args:
            input_file: Ruta del archivo de entrada
            status_message: Objeto de mensaje de Telegram para actualizaciones

        Returns:
            Tupla (compressed_file_path, error_message)
            error_message es None si la compresión fue exitosa
        """
        compressed_file = None

        try:
            # Obtener información del archivo
            file_size_bytes = os.path.getsize(input_file)
            file_size_mb = file_size_bytes / 1024 / 1024

            # Estimar tiempo de compresión basado en tamaño
            estimated_time_seconds = max(5, int(file_size_mb * 0.5))

            # Crear tracker de progreso
            tracker = ProgressTracker(
                total_size_bytes=file_size_bytes,
                task_name="Comprimiendo audio",
                status_message=status_message,
                initial_message=f"🔄 **Comprimiendo audio**...\n\n⏱️ Tiempo estimado: ~{estimated_time_seconds}s\n\nEl procesamiento continuá. Por favor espera..."
            )

            # Iniciar tracker en background
            tracker.start()

            # Comprimir audio en un hilo separado para permitir actualizaciones de progreso
            compression_complete = threading.Event()
            compression_error = [None]
            compressed_file_result = [None]

            def compress_audio():
                try:
                    # Cargar y configurar audio
                    audio = AudioSegment.from_file(input_file).set_channels(
                        AUDIO_CHANNELS
                    ).set_frame_rate(AUDIO_SAMPLE_RATE)

                    # Crear archivo temporal de salida
                    with tempfile.NamedTemporaryFile(
                        suffix=TEMP_FILE_SUFFIX_AUDIO,
                        delete=False
                    ) as temp_file:
                        compressed_file_result[0] = temp_file.name

                    # Exportar audio comprimido
                    audio.export(
                        compressed_file_result[0],
                        format=AUDIO_FORMAT,
                        bitrate=AUDIO_BITRATE
                    )
                except Exception as e:
                    compression_error[0] = e
                finally:
                    compression_complete.set()

            # Iniciar compresión en background
            compress_thread = threading.Thread(target=compress_audio)
            compress_thread.start()

            # Actualizar progreso basado en tiempo estimado
            start_time = time.time()
            while not compression_complete.is_set():
                elapsed = time.time() - start_time
                # Estimar progreso basado en tiempo transcurrido
                estimated_progress = min((elapsed / estimated_time_seconds) * 100, 100)
                # Convertir a tamaño procesado estimado
                processed_size = int((estimated_progress / 100) * file_size_bytes)
                tracker.update(processed_size)
                time.sleep(0.5)

            # Esperar que termine el hilo de compresión
            compress_thread.join(timeout=5)

            # Detener tracker
            tracker.stop()

            # Verificar si hubo error en compresión
            if compression_error[0]:
                raise compression_error[0]

            # Obtener archivo comprimido del resultado
            compressed_file = compressed_file_result[0]

            return compressed_file, None

        except Exception as e:
            error_message = f"Error al comprimir audio: {str(e)}"
            return compressed_file, error_message

    def cleanup(self, *file_paths: str):
        """
        Elimina archivos temporales de forma segura

        Args:
            *file_paths: Lista de rutas de archivos a eliminar
        """
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    # No lanzar error si falla limpieza de un archivo temporal
                    pass
