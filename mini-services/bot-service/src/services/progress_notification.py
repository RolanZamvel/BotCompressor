from typing import Optional
from interfaces.message_handler import IProgressNotifier


class ProgressNotifier(IProgressNotifier):
    """
    Servicio de notificaciones de progreso para Telegram.
    Implementa Single Responsibility Principle (SRP).
    """

    def __init__(self, message):
        """
        Inicializa el notificador con un mensaje de Telegram.

        Args:
            message: Objeto de mensaje de Pyrogram
        """
        self._message = message
        self._status_message = None

    def notify_downloading(self) -> None:
        """Notifica que se está descargando el archivo."""
        self._status_message = self._message.reply_text(
            "📥 **Descargando archivo**...\n\nEsto puede tomar unos segundos."
        )

    def notify_compressing(self, estimated_time: str = "") -> None:
        """
        Notifica que se está comprimiendo.

        Args:
            estimated_time: Tiempo estimado (opcional)
        """
        if estimated_time:
            text = f"🔄 **Comprimiendo**...\n\n⏱️ Tiempo estimado: {estimated_time}\n\nEsto puede tomar un momento dependiendo del tamaño del archivo."
        else:
            text = "🔄 **Comprimiendo**...\n\n⏱️ Esto puede tomar un momento dependiendo del tamaño del archivo."

        if self._status_message:
            self._status_message.edit_text(text)

    def notify_sending(self) -> None:
        """Notifica que se está enviando el archivo."""
        if self._status_message:
            self._status_message.edit_text("📤 **Enviando archivo comprimido**...")

    def notify_success(self, message: str) -> None:
        """
        Notifica éxito con mensaje personalizado.

        Args:
            message: Mensaje de éxito
        """
        if self._status_message:
            self._status_message.edit_text(message)

    def notify_error(self, error_message: str) -> None:
        """
        Notifica error con mensaje personalizado.

        Args:
            error_message: Mensaje de error
        """
        if self._status_message:
            self._status_message.edit_text(error_message)
        else:
            self._message.reply_text(error_message)

    def get_status_message(self) -> Optional[object]:
        """Obtiene el objeto del mensaje de estado actual."""
        return self._status_message

    def notify_message(self, message: str) -> None:
        """
        Notifica un mensaje específico (para progreso en tiempo real).
        Este método envía el mensaje al sistema de logs del bot-service.

        Args:
            message: Mensaje de progreso
        """
        # Enviar al sistema de logs (se mostrará en el dashboard)
        import sys
        print(f"[PROGRESS] {message}")
        sys.stdout.flush()  # Asegurar que se envíe inmediatamente
