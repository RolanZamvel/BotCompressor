import os
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

        # Verificar si ya fue procesado
        if self._message_tracker.is_processed(message.id):
            return True

        try:
            # Marcar como procesado
            self._message_tracker.mark_as_processed(message.id)

            # Notificar inicio de descarga
            self._notifier.notify_downloading()

            # Descargar archivo
            downloaded_file = message._client.download_media(file_id)

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

            # Notificar inicio de compresión
            self._notifier.notify_compressing(estimated_time)

            # Comprimir
            if is_animation:
                success, result_msg = self._compressor.compress(downloaded_file, compressed_file)
            else:
                success, result_msg = self._compressor.compress(downloaded_file, compressed_file)

            if not success:
                raise Exception(result_msg)

            # Notificar envío
            self._notifier.notify_sending()

            # Verificar archivo comprimido
            if not self._file_manager.file_exists(compressed_file):
                raise Exception("El archivo comprimido tiene 0 bytes")

            # Calcular estadísticas
            compressed_size_mb = self._file_manager.get_file_size_mb(compressed_file)
            original_size_mb = self._file_manager.get_file_size_mb(downloaded_file)
            compression_ratio = (1 - compressed_size_mb / original_size_mb) * 100

            # Enviar archivo comprimido
            if self._compressor.get_output_format() == ".mp3":
                message.reply_document(compressed_file)
            else:
                message.reply_video(compressed_file)

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
