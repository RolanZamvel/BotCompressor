import os
import time
import threading
from typing import Tuple, Optional
from interfaces.media_compressor import IMediaCompressor
from interfaces.file_handler import IFileManager
from interfaces.message_handler import IMessageTracker, IProgressNotifier


class CompressionOrchestrator:
    """
    Orquestador que coordina el proceso de compresión de medios.
    Implementa Dependency Inversion Principle (DIP).
    """

    def __init__(
        self,
        compressor: IMediaCompressor,
        file_manager: IFileManager,
        message_tracker: IMessageTracker,
        notifier: IProgressNotifier
    ):
        """
        Inicializa el orquestador con dependencias inyectadas.

        Args:
            compressor: Compresor de medios
            file_manager: Manejador de archivos
            message_tracker: Tracker de mensajes
            notifier: Notificador de progreso
        """
        self._compressor = compressor
        self._file_manager = file_manager
        self._message_tracker = message_tracker
        self._notifier = notifier

    def process(self, message, file_id: str, is_animation: bool = False) -> bool:
        """
        Procesa un mensaje de compresión completo.

        Args:
            message: Mensaje de Telegram
            file_id: ID del archivo a descargar
            is_animation: True si es una animación

        Returns:
            bool: True si el proceso fue exitoso
        """
        downloaded_file = None
        compressed_file = None
        backup_file = None

        # Variables de progreso
        download_progress = 0
        upload_progress = 0
        compression_progress = 0
        compression_start_time = None

        try:
            # Verificar si ya fue procesado
            if self._message_tracker.is_processed(message.id):
                return True

            # Marcar como procesado
            self._message_tracker.mark_as_processed(message.id)

            # OBTENER INFORMACIÓN DEL ARCHIVO (Para progreso)
            total_bytes = 0
            try:
                file_info = message._client.get_file(file_id)
                total_bytes = getattr(file_info, 'file_size', 0)
                total_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0

                # NOTIFICAR: Información del archivo
                self._notifier.notify_message(
                    f"📥 **Procesando archivo**\n"
                    f"📊 Tamaño: {total_mb:.2f} MB\n"
                    f"💾 Tipo: {'Video' if message.video or message.animation else 'Audio'}"
                )
            except Exception:
                total_bytes = 0
                self._notifier.notify_message("⚠️ No se pudo obtener información del archivo")

            # Callback de progreso para descarga
            def download_callback(current_downloaded, total_downloaded):
                nonlocal download_progress

                if total_downloaded > 0:
                    progress = (current_downloaded / total_downloaded) * 100
                    downloaded_mb = current_downloaded / (1024 * 1024)
                    total_mb = total_bytes / (1024 * 1024)

                    # Actualizar solo cada 10% o si es 100%
                    if progress - download_progress >= 10 or progress >= 100:
                        download_progress = progress

                        self._notifier.notify_message(
                            f"⬇️ **Descargando** {progress:.0f}%\n"
                            f"💾 {downloaded_mb:.1f} MB / {total_mb:.1f} MB"
                        )

            # NOTIFICAR: Inicio de descarga
            self._notifier.notify_downloading()
            self._notifier.notify_message("⬇️ **Iniciando descarga**...")

            # Descargar archivo CON progreso
            if total_bytes > 0:
                downloaded_file = message._client.download_media(
                    file_id,
                    progress=download_callback
                )
            else:
                # Fallback para archivos pequeños
                downloaded_file = message._client.download_media(file_id)
                download_progress = 100

            # NOTIFICAR: Fin de descarga
            self._notifier.notify_message(f"✅ **Descarga completada**: {download_progress:.0f}%")

            # Crear backup para rollback
            backup_file = self._file_manager.create_backup(downloaded_file)

            # Calcular tiempo estimado
            file_size_mb = self._file_manager.get_file_size_mb(downloaded_file)
            estimated_time = self._calculate_estimated_time(file_size_mb)

            # Crear archivo de salida
            compressed_file = self._file_manager.create_temp_file(
                self._compressor.get_output_format()
            )

            # Eliminar si existe para evitar conflictos
            if os.path.exists(compressed_file):
                os.remove(compressed_file)

            # Callback de progreso para compresión
            def update_compression_progress():
                nonlocal compression_progress, compression_start_time

                if compression_start_time:
                    elapsed = time.time() - compression_start_time
                    estimated_seconds = self._parse_estimated_time(estimated_time)

                    if estimated_seconds > 0:
                        progress = min(90, (elapsed / estimated_seconds) * 100)

                        # Actualizar cada 15% o cada 10 segundos
                        if progress - compression_progress >= 15 or elapsed % 10 == 0:
                            compression_progress = progress

                            self._notifier.notify_message(
                                f"🗜️ **Comprimiendo** {progress:.0f}%\n"
                                f"⏱️ Tiempo: {estimated_time}"
                            )

            # NOTIFICAR: Inicio de compresión
            self._notifier.notify_compressing(estimated_time)
            self._notifier.notify_message(f"🗜️ **Iniciando compresión**\n⏱️ Tiempo estimado: {estimated_time}")

            # Iniciar timer de compresión
            compression_start_time = time.time()

            # Iniciar actualizador de progreso en hilo separado
            progress_thread = threading.Thread(target=update_compression_progress)
            progress_thread.daemon = True
            progress_thread.start()

            # Comprimir
            if is_animation:
                success, result_msg = self._compressor.compress(downloaded_file, compressed_file)
            else:
                success, result_msg = self._compressor.compress(downloaded_file, compressed_file)

            if not success:
                raise Exception(result_msg)

            # NOTIFICAR: Fin de compresión
            compression_progress = 100
            self._notifier.notify_message("✅ **Compresión completada**: 100%")

            # NOTIFICAR: Inicio del envío
            self._notifier.notify_sending()
            self._notifier.notify_message("📤 **Enviando archivo comprimido**...")

            # Callback de progreso para envío
            def upload_callback(current_uploaded, total_uploaded):
                nonlocal upload_progress

                if total_uploaded > 0:
                    progress = (current_uploaded / total_uploaded) * 100
                    uploaded_mb = current_uploaded / (1024 * 1024)
                    total_mb = total_uploaded / (1024 * 1024)

                    # Actualizar solo cada 10% o si es 100%
                    if progress - upload_progress >= 10 or progress >= 100:
                        upload_progress = progress

                        self._notifier.notify_message(
                            f"📤 **Enviando** {progress:.0f}%\n"
                            f"💾 {uploaded_mb:.1f} MB / {total_mb:.1f} MB"
                        )

            # Verificar archivo comprimido
            if not self._file_manager.file_exists(compressed_file):
                raise Exception("El archivo comprimido tiene 0 bytes")

            # Obtener tamaño del archivo comprimido
            compressed_size_bytes = os.path.getsize(compressed_file)

            # Enviar archivo comprimido CON progreso
            if self._compressor.get_output_format() == ".mp3":
                message.reply_document(
                    compressed_file,
                    progress=upload_callback
                )
            else:
                message.reply_video(
                    compressed_file,
                    progress=upload_callback
                )

            # NOTIFICAR: Fin del envío
            upload_progress = 100
            self._notifier.notify_message("✅ **Archivo enviado**: 100%")

            # Calcular estadísticas
            compressed_size_mb = self._file_manager.get_file_size_mb(compressed_file)
            original_size_mb = self._file_manager.get_file_size_mb(downloaded_file)
            compression_ratio = (1 - compressed_size_mb / original_size_mb) * 100

            # Notificar éxito
            success_message = self._build_success_message(
                original_size_mb, compressed_size_mb, compression_ratio
            )
            self._notifier.notify_success(success_message)

            # Limpiar originales en caso de éxito
            self._file_manager.cleanup_file(downloaded_file)
            self._file_manager.cleanup_file(backup_file)

            return True

        except Exception as e:
            # ROLLBACK: Notificar error y enviar original
            error_message = f"❌ **Error durante compresión:** {str(e)}\n\n📤 Te envío tu archivo original."
            self._notifier.notify_error(error_message)

            # Enviar archivo original
            if backup_file and self._file_manager.file_exists(backup_file):
                try:
                    message.reply_document(backup_file)
                except Exception:
                    pass

            return False

        finally:
            # Limpiar temporales
            self._file_manager.cleanup_all([downloaded_file, compressed_file, backup_file])

    def _calculate_estimated_time(self, size_mb: float) -> str:
        """
        Calcula el tiempo estimado de compresión.

        Args:
            size_mb: Tamaño del archivo en MB

        Returns:
            str: Tiempo estimado formateado
        """
        # Video: ~1.5s por MB, Audio: ~0.5s por MB
        is_video = self._compressor.get_output_format() == ".mp4"
        factor = 1.5 if is_video else 0.5

        estimated_time_seconds = max(5 if is_video else 2, int(size_mb * factor))
        estimated_time_minutes = estimated_time_seconds // 60
        estimated_time_seconds_remainder = estimated_time_seconds % 60

        if estimated_time_minutes > 0:
            return f"~{estimated_time_minutes}m {estimated_time_seconds_remainder}s"
        else:
            return f"~{estimated_time_seconds}s"

    def _parse_estimated_time(self, time_str: str) -> float:
        """
        Convierte el tiempo estimado (formato "~5m 30s") a segundos.

        Args:
            time_str: Tiempo estimado formateado

        Returns:
            float: Tiempo en segundos
        """
        try:
            # Remover el símbolo "~" si existe
            time_str = time_str.replace("~", "").strip()

            # Si solo tiene segundos
            if "m" not in time_str:
                seconds = float(time_str.replace("s", "").strip())
                return max(1, seconds)

            # Si tiene minutos y segundos
            parts = time_str.split("m")
            if len(parts) == 2:
                minutes = float(parts[0].strip())
                seconds_part = parts[1].replace("s", "").strip()
                seconds = (minutes * 60) + float(seconds_part)
                return max(1, seconds)

            # Si solo tiene minutos
            return max(60, float(time_str.replace("m", "").strip()) * 60)
        except:
            return 60  # Fallback a 1 minuto

    def _build_success_message(self, original_mb: float, compressed_mb: float, ratio: float) -> str:
        """
        Construye el mensaje de éxito con estadísticas.

        Args:
            original_mb: Tamaño original en MB
            compressed_mb: Tamaño comprimido en MB
            ratio: Porcentaje de reducción

        Returns:
            str: Mensaje de éxito formateado
        """
        media_type = "video" if self._compressor.get_output_format() == ".mp4" else "audio"
        return (
            f"✅ **¡Listo!**\n\n"
            f"🎉 Tu {media_type} ha sido comprimido exitosamente.\n\n"
            f"📊 **Estadísticas:**\n"
            f"   • Tamaño original: {original_mb:.1f} MB\n"
            f"   • Tamaño comprimido: {compressed_mb:.1f} MB\n"
            f"   • Reducción de tamaño: {ratio:.1f}%"
        )
