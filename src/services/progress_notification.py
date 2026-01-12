from typing import Optional
import time
from ..interfaces.message_handler import IProgressNotifier


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
        self._download_start_time = None
        self._download_total_bytes = 0
        self._download_progress_timer = None

    def notify_downloading(self) -> None:
        """Notifica que se está descargando el archivo."""
        self._download_start_time = time.time()
        self._status_message = self._message.reply_text(
            "📥 **Descargando archivo**...\n\nEsto puede tomar unos segundos."
        )

    def update_download_progress(self, current: int, total: int) -> None:
        """
        Actualiza el progreso de descarga.

        Args:
            current: Bytes descargados
            total: Bytes totales
        """
        if not self._download_start_time:
            return

        self._download_total_bytes = total
        elapsed_time = time.time() - self._download_start_time

        # Calcular porcentaje
        progress_percent = (current / total * 100) if total > 0 else 0

        # Si han pasado más de 5 segundos y el progreso es significativo
        if elapsed_time >= 5 and progress_percent > 5:
            # Calcular tiempo restante estimado
            if current > 0 and elapsed_time > 0:
                speed = current / elapsed_time  # bytes por segundo
                remaining_bytes = total - current
                remaining_seconds = remaining_bytes / speed if speed > 0 else 0

                # Formatear tiempo restante
                if remaining_seconds >= 60:
                    remaining_minutes = int(remaining_seconds // 60)
                    remaining_seconds_int = int(remaining_seconds % 60)
                    time_str = f"{remaining_minutes} min restante" if remaining_seconds_int == 0 else f"{remaining_minutes} min {remaining_seconds_int}s restante"
                else:
                    time_str = f"{int(remaining_seconds)}s restante"
            else:
                time_str = "Calculando..."

            # Generar barra de progreso
            progress_bar = self._generate_progress_bar(progress_percent)

            # Actualizar mensaje
            text = f"📥 **Descargando archivo**...\n\n{progress_percent:.0f}%    {time_str}\n{progress_bar}"

            try:
                if self._status_message:
                    self._status_message.edit_text(text)
            except Exception:
                pass  # Ignorar errores de edición

    def _generate_progress_bar(self, percent: float, width: int = 10) -> str:
        """
        Genera una barra de progreso visual.

        Args:
            percent: Porcentaje completado (0-100)
            width: Ancho de la barra en caracteres

        Returns:
            str: Barra de progreso formateada
        """
        filled = int(width * percent / 100)
        empty = width - filled

        # Usar = para completado y × para pendiente
        bar = "×" * empty + "=" * filled
        return f"  {bar} ({int(percent)}%)"

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
