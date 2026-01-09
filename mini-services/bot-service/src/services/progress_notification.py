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
        """Notifica que se está descargando el archivo al chat del usuario."""
        self._status_message = self._message.reply_text(
            "📥 **Iniciando descarga**...\n\n⏳ Espera un momento..."
        )

    def notify_compressing(self, estimated_time: str = "") -> None:
        """
        Notifica que se está comprimiendo al chat del usuario.

        Args:
            estimated_time: Tiempo estimado (opcional)
        """
        if estimated_time:
            text = f"🗜️ **Iniciando compresión**...\n\n⏱️ Tiempo estimado: {estimated_time}\n\n⏳ Espera un momento..."
        else:
            text = "🗜️ **Iniciando compresión**...\n\n⏳ Espera un momento..."

        if self._status_message:
            self._status_message.edit_text(text)

    def notify_sending(self) -> None:
        """Notifica que se está enviando el archivo al chat del usuario."""
        if self._status_message:
            self._status_message.edit_text("📤 **Enviando archivo comprimido**...\n\n⏳ Espera un momento...")

    def notify_success(self, message: str) -> None:
        """
        Notifica éxito con mensaje personalizado al chat del usuario.

        Args:
            message: Mensaje de éxito
        """
        if self._status_message:
            self._status_message.edit_text(message)

    def notify_error(self, error_message: str) -> None:
        """
        Notifica error con mensaje personalizado al chat del usuario.

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
        Actualiza el mensaje de progreso en el chat del usuario Y en los logs del dashboard.

        Este método es CRÍTICO porque:
        1. Actualiza el mensaje de progreso en el chat del usuario (Telegram)
        2. Envía el mismo mensaje al sistema de logs (se mostrará en el dashboard)

        Args:
            message: Mensaje de progreso (debe incluir porcentajes y tamaños)
        """
        # 1. ACTUALIZAR EN EL CHAT DEL USUARIO (Telegram)
        if self._status_message:
            try:
                self._status_message.edit_text(message)
            except Exception as edit_error:
                # Si falla la edición, enviar como nuevo mensaje
                self._message.reply_text(message)

        # 2. ENVIAR A LOS LOGS DEL DASHBOARD
        # Esto se mostrará en la sección "Live Logs" del dashboard
        import sys
        print(f"[PROGRESS] {message}")
        sys.stdout.flush()  # Asegurar que se envíe inmediatamente

    def update_download_progress(self, current_downloaded: int, total_downloaded: int) -> None:
        """
        Actualiza el progreso de descarga en el chat del usuario y en los logs.

        Args:
            current_downloaded: Bytes descargados actualmente
            total_downloaded: Total de bytes a descargar
        """
        if total_downloaded > 0:
            progress = (current_downloaded / total_downloaded) * 100
            downloaded_mb = current_downloaded / (1024 * 1024)
            total_mb = total_downloaded / (1024 * 1024)

            # Formato del mensaje de progreso
            message = f"⬇️ **Descargando** {progress:.0f}%\n\n💾 {downloaded_mb:.1f} MB / {total_mb:.1f} MB"

            self.notify_message(message)

    def update_compression_progress(self, progress: float, estimated_time: str) -> None:
        """
        Actualiza el progreso de compresión en el chat del usuario y en los logs.

        Args:
            progress: Porcentaje de progreso (0-90)
            estimated_time: Tiempo estimado restante
        """
        # Formato del mensaje de progreso
        message = f"🗜️ **Comprimiendo** {progress:.0f}%\n\n⏱️ Tiempo estimado: {estimated_time}\n\n⏳ Procesando..."

        self.notify_message(message)

    def update_upload_progress(self, current_uploaded: int, total_uploaded: int) -> None:
        """
        Actualiza el progreso de envío en el chat del usuario y en los logs.

        Args:
            current_uploaded: Bytes enviados actualmente
            total_uploaded: Total de bytes a enviar
        """
        if total_uploaded > 0:
            progress = (current_uploaded / total_uploaded) * 100
            uploaded_mb = current_uploaded / (1024 * 1024)
            total_mb = total_uploaded / (1024 * 1024)

            # Formato del mensaje de progreso
            message = f"📤 **Enviando** {progress:.0f}%\n\n💾 {uploaded_mb:.1f} MB / {total_mb:.1f} MB"

            self.notify_message(message)

    def notify_download_complete(self, total_mb: float) -> None:
        """
        Notifica que la descarga se completó en el chat del usuario y en los logs.

        Args:
            total_mb: Tamaño total del archivo en MB
        """
        message = f"✅ **Descarga completada**\n\n💾 Tamaño: {total_mb:.2f} MB\n\n🗜️ Iniciando compresión..."
        self.notify_message(message)

    def notify_compression_complete(self) -> None:
        """Notifica que la compresión se completó en el chat del usuario y en los logs."""
        message = "✅ **Compresión completada: 100%**\n\n📤 Iniciando envío..."
        self.notify_message(message)

    def notify_upload_complete(self) -> None:
        """Notifica que el envío se completó en el chat del usuario y en los logs."""
        message = "✅ **Archivo enviado: 100%**"
        self.notify_message(message)
