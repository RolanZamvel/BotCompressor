from abc import ABC, abstractmethod
from typing import Optional


class IMessageTracker(ABC):
    """
    Interfaz para tracking de mensajes procesados.
    Implementa Interface Segregation Principle (ISP).
    """

    @abstractmethod
    def is_processed(self, message_id: int) -> bool:
        """
        Verifica si un mensaje ya fue procesado.

        Args:
            message_id: ID del mensaje

        Returns:
            bool: True si ya fue procesado
        """
        pass

    @abstractmethod
    def mark_as_processed(self, message_id: int) -> None:
        """
        Marca un mensaje como procesado.

        Args:
            message_id: ID del mensaje
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Limpia todos los mensajes procesados."""
        pass


class IProgressNotifier(ABC):
    """
    Interfaz para notificaciones de progreso.
    Implementa Interface Segregation Principle (ISP).
    """

    @abstractmethod
    def notify_downloading(self) -> None:
        """Notifica que se está descargando el archivo."""
        pass

    @abstractmethod
    def set_download_total(self, total_bytes: int) -> None:
        """
        Establece el tamaño total de la descarga.

        Args:
            total_bytes: Tamaño total del archivo en bytes
        """
        pass

    @abstractmethod
    def update_download_progress(self, current: int, total: int) -> None:
        """
        Actualiza el progreso de descarga.

        Args:
            current: Bytes descargados
            total: Bytes totales (puede ser 0 si Pyrogram no lo proporciona)
        """
        pass

    @abstractmethod
    def notify_compressing(self, estimated_time: str = "") -> None:
        """
        Notifica que se está comprimiendo.

        Args:
            estimated_time: Tiempo estimado (opcional)
        """
        pass

    @abstractmethod
    def set_compression_total(self, total_bytes: int) -> None:
        """
        Establece el tamaño total para cálculo de progreso de compresión.

        Args:
            total_bytes: Tamaño total del archivo en bytes
        """
        pass

    @abstractmethod
    def update_compression_progress(self, current_bytes: int) -> None:
        """
        Actualiza el progreso de compresión.

        Args:
            current_bytes: Bytes procesados
        """
        pass

    @abstractmethod
    def notify_sending(self) -> None:
        """Notifica que se está enviando el archivo."""
        pass

    @abstractmethod
    def set_upload_total(self, total_bytes: int) -> None:
        """
        Establece el tamaño total para cálculo de progreso de subida.

        Args:
            total_bytes: Tamaño total del archivo en bytes
        """
        pass

    @abstractmethod
    def update_upload_progress(self, current_bytes: int) -> None:
        """
        Actualiza el progreso de subida.

        Args:
            current_bytes: Bytes subidos
        """
        pass

    @abstractmethod
    def notify_success(self, message: str) -> None:
        """
        Notifica éxito con mensaje personalizado.

        Args:
            message: Mensaje de éxito
        """
        pass

    @abstractmethod
    def notify_error(self, error_message: str) -> None:
        """
        Notifica error con mensaje personalizado.

        Args:
            error_message: Mensaje de error
        """
        pass

    @abstractmethod
    def get_status_message(self) -> Optional[object]:
        """
        Obtiene el objeto del mensaje de estado actual.

        Returns:
            Optional[object]: Objeto del mensaje o None
        """
        pass
