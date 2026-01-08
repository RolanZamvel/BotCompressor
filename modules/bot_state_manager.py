"""
Módulo de gestión de estado para BotCompressor

Responsabilidades (SRP):
- Gestionar estado de mensajes pendientes
- Guardar contexto de videos pendientes de compresión
- Manejar preferencias de usuario
"""

from typing import Dict, Optional
from pyrogram.types import Message


class BotStateManager:
    """
    Clase responsable de gestionar el estado del bot
    """

    def __init__(self):
        """Inicializa el gestor de estado"""
        # Mensajes de video pendientes de procesamiento
        # {user_id: Message}
        self.pending_videos: Dict[int, Message] = {}

        # Preferencias de calidad del usuario
        # {user_id: "compress" o "maintain"}
        self.user_quality_preferences: Dict[int, str] = {}

        # Mensajes ya procesados (para evitar duplicados)
        self.processed_messages = set()

    def set_pending_video(self, user_id: int, message: Message):
        """
        Guarda un mensaje de video como pendiente

        Args:
            user_id: ID del usuario
            message: Mensaje con el video
        """
        self.pending_videos[user_id] = message

    def get_pending_video(self, user_id: int) -> Optional[Message]:
        """
        Obtiene el mensaje de video pendiente de un usuario

        Args:
            user_id: ID del usuario

        Returns:
            Mensaje con el video pendiente o None
        """
        return self.pending_videos.get(user_id)

    def clear_pending_video(self, user_id: int):
        """
        Limpia el video pendiente de un usuario

        Args:
            user_id: ID del usuario
        """
        if user_id in self.pending_videos:
            del self.pending_videos[user_id]

    def set_quality_preference(self, user_id: int, quality_option: str):
        """
        Guarda la preferencia de calidad de un usuario

        Args:
            user_id: ID del usuario
            quality_option: "compress" o "maintain"
        """
        self.user_quality_preferences[user_id] = quality_option

    def get_quality_preference(self, user_id: int) -> Optional[str]:
        """
        Obtiene la preferencia de calidad de un usuario

        Args:
            user_id: ID del usuario

        Returns:
            Preferencia de calidad o None
        """
        return self.user_quality_preferences.get(user_id)

    def is_message_processed(self, message_id: int) -> bool:
        """
        Verifica si un mensaje ya fue procesado

        Args:
            message_id: ID del mensaje

        Returns:
            True si el mensaje ya fue procesado
        """
        return message_id in self.processed_messages

    def mark_message_as_processed(self, message_id: int):
        """
        Marca un mensaje como procesado

        Args:
            message_id: ID del mensaje
        """
        self.processed_messages.add(message_id)
