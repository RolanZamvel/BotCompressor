from typing import Set
from interfaces.message_handler import IMessageTracker


class MessageTracker(IMessageTracker):
    """
    Implementación del tracking de mensajes procesados.
    Implementa Single Responsibility Principle (SRP).
    """

    def __init__(self):
        self._processed_messages: Set[int] = set()

    def is_processed(self, message_id: int) -> bool:
        """Verifica si un mensaje ya fue procesado."""
        return message_id in self._processed_messages

    def mark_as_processed(self, message_id: int) -> None:
        """Marca un mensaje como procesado."""
        self._processed_messages.add(message_id)

    def clear(self) -> None:
        """Limpia todos los mensajes procesados."""
        self._processed_messages.clear()
