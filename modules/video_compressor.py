"""
Módulo de compresión de video para BotCompressor

Responsabilidades (SRP):
- Comprimir archivos de video usando FFmpeg
- Configurar parámetros de compresión según calidad
- Gestionar archivos temporales de salida
"""

import os
import tempfile
import threading
import time
import subprocess
from typing import Tuple, Optional, Dict, Any
from config import (
    VIDEO_FPS,
    VIDEO_CODEC,
    VIDEO_PIXEL_FORMAT,
    VIDEO_AUDIO_CODEC,
    VIDEO_AUDIO_BITRATE,
    VIDEO_AUDIO_CHANNELS,
    VIDEO_AUDIO_SAMPLE_RATE,
    VIDEO_PROFILE,
    TEMP_FILE_SUFFIX_VIDEO
)
from progress_tracker import ProgressTracker


class VideoCompressor:
    """
    Clase responsable de comprimir archivos de video
    """

    def __init__(self):
        """Inicializa el compresor de video"""
        pass

    def get_quality_params(self, quality_option: str) -> Dict[str, Any]:
        """
        Obtiene parámetros de compresión según la opción de calidad

        Args:
            quality_option: "compress" o "maintain"

        Returns:
            Diccionario con parámetros de compresión:
            {
                'crf': int,
                'bitrate': str,
                'preset': str,
                'description': str,
                'estimated_factor': float
            }
        """
        if quality_option == "compress":
            # Comprimir más (menor calidad, menor tamaño)
            return {
                'crf': 28,
                'bitrate': '500k',
                'preset': 'medium',
                'description': 'Comprimiendo (mayor compresión)',
                'estimated_factor': 1.0  # 1s por MB (más rápido)
            }
        elif quality_option == "maintain":
            # Mantener calidad (menor compresión, mayor tamaño)
            return {
                'crf': 18,
                'bitrate': '2M',
                'preset': 'slow',
                'description': 'Manteniendo calidad (menor compresión)',
                'estimated_factor': 1.5  # 1.5s por MB (más lento)
            }
        else:
            raise Exception(f"Opción de calidad no válida: {quality_option}")

    def compress(
        self,
        input_file: str,
        quality_option: str,
        status_message: object,
        is_animation: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Comprime un archivo de video

        Args:
            input_file: Ruta del archivo de entrada
            quality_option: "compress" o "maintain"
            status_message: Objeto de mensaje de Telegram para actualizaciones
            is_animation: Si True, trata el archivo como animación (GIF)

        Returns:
            Tupla (compressed_file_path, error_message)
            error_message es None si la compresión fue exitosa
        """
        compressed_file = None

        try:
            # Obtener información del archivo
            file_size_bytes = os.path.getsize(input_file)
            file_size_mb = file_size_bytes / 1024 / 1024

            # Obtener parámetros de calidad
            params = self.get_quality_params(quality_option)

            # Calcular tiempo estimado
            estimated_time_seconds = max(10, int(file_size_mb * params['estimated_factor']))

            # Crear tracker de progreso
            tracker = ProgressTracker(
                total_size_bytes=file_size_bytes,
                task_name=f"🎬 {params['description']}",
                status_message=status_message,
                initial_message=f"🔄 **{params['description']}**...\n\n⏱️ Tiempo estimado: ~{estimated_time_seconds}s\n\nEsto puede tomar varios minutos para archivos grandes.",
                show_speed=True
            )

            # Iniciar tracker en background
            tracker.start()

            # Filtro de escala que mantiene el aspect ratio original
            scale_filter = "scale='if(gt(iw,ih),640,-2):if(gt(iw,ih),-2,360)'"

            # Comprimir video en un hilo separado para permitir actualizaciones de progreso
            compression_complete = threading.Event()
            compression_error = [None]
            compressed_file_result = [None]

            def compress_video():
                try:
                    # Crear archivo temporal de salida
                    with tempfile.NamedTemporaryFile(
                        suffix='.mp4',
                        delete=False
                    ) as temp_file:
                        compressed_file_result[0] = temp_file.name

                    # Eliminar archivo temporal si existe para evitar conflicto de FFmpeg
                    if os.path.exists(compressed_file_result[0]):
                        os.remove(compressed_file_result[0])

                    # Construir comando FFmpeg
                    if is_animation:
                        # Para animaciones (GIFs), comprimir sin recodificar
                        ffmpeg_cmd = f'ffmpeg -y -i "{input_file}" "{compressed_file_result[0]}"'
                    else:
                        # Para videos, usar compresión completa
                        ffmpeg_cmd = (
                            f'ffmpeg -y -i "{input_file}" '
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
                            f'-map_metadata -1 "{compressed_file_result[0]}"'
                        )

                    # Ejecutar FFmpeg
                    subprocess.run(ffmpeg_cmd, shell=True, check=True)

                except Exception as e:
                    compression_error[0] = e
                finally:
                    compression_complete.set()

            # Iniciar compresión en background
            compress_thread = threading.Thread(target=compress_video)
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
            compress_thread.join(timeout=30)

            # Detener tracker
            tracker.stop()

            # Verificar si hubo error en compresión
            if compression_error[0]:
                raise compression_error[0]

            # Obtener archivo comprimido del resultado
            compressed_file = compressed_file_result[0]

            return compressed_file, None

        except subprocess.CalledProcessError as e:
            error_message = f"Error de FFmpeg: {str(e)}"
            return compressed_file, error_message
        except Exception as e:
            error_message = f"Error al comprimir video: {str(e)}"
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
