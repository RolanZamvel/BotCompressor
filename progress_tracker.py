"""
Módulo de seguimiento de progreso para BotCompressor
Proporciona tracking en tiempo real de compresión de audio y video
"""

import time
import threading
import os
from typing import Optional, Callable
from config import (
    PROGRESS_UPDATE_INTERVAL,
    PROGRESS_BAR_WIDTH
)


class ProgressTracker:
    """
    Clase para tracking de progreso durante la compresión de archivos
    """

    def __init__(
        self,
        total_size_bytes: int,
        task_name: str,
        status_message: object,
        initial_message: str = "",
        show_speed: bool = False
    ):
        """
        Inicializa el tracker de progreso

        Args:
            total_size_bytes: Tamaño total del archivo en bytes
            task_name: Nombre de la tarea (ej: "Comprimiendo audio")
            status_message: Objeto de mensaje de Telegram para actualizaciones
            initial_message: Mensaje inicial a mostrar
            show_speed: Si True, mostrar velocidad de procesamiento
        """
        self.total_size_bytes = total_size_bytes
        self.task_name = task_name
        self.status_message = status_message
        self.show_speed = show_speed

        self.start_time = time.time()
        self.processed_size_bytes = 0
        self.progress_percentage = 0.0
        self.is_running = False
        self.is_complete = False
        self.update_thread: Optional[threading.Thread] = None
        self.update_interval = PROGRESS_UPDATE_INTERVAL
        self.error: Optional[str] = None

        # Enviar mensaje inicial
        if initial_message:
            try:
                self.status_message.edit_text(initial_message)
            except Exception as e:
                self.error = f"Error sending initial message: {str(e)}"

    def start(self):
        """Inicia el tracking en un hilo separado"""
        self.is_running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def stop(self):
        """Detiene el tracking"""
        self.is_running = False
        self.is_complete = True
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)

    def update(self, processed_size: int):
        """
        Actualiza el progreso basado en el tamaño procesado

        Args:
            processed_size: Tamaño procesado en bytes
        """
        self.processed_size_bytes = processed_size
        if self.total_size_bytes > 0:
            self.progress_percentage = (processed_size / self.total_size_bytes) * 100
        else:
            self.progress_percentage = 0

    def _get_elapsed_time(self) -> str:
        """
        Obtiene el tiempo transcurrido formateado

        Returns:
            Tiempo en formato MM:SS
        """
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _get_remaining_time(self) -> str:
        """
        Estima el tiempo restante basado en el progreso

        Returns:
            Tiempo restante estimado en formato ~Mm Ss
        """
        elapsed = time.time() - self.start_time

        if self.progress_percentage > 0 and elapsed > 0:
            # Calcular velocidad promedio
            rate = self.processed_size_bytes / elapsed

            if rate > 0:
                remaining_bytes = self.total_size_bytes - self.processed_size_bytes
                remaining_seconds = remaining_bytes / rate

                minutes = int(remaining_seconds // 60)
                seconds = int(remaining_seconds % 60)

                if minutes > 0:
                    return f"~{minutes}m {seconds}s"
                else:
                    return f"~{seconds}s"

        # Si no hay suficiente información, mostrar indicador genérico
        return "~Estimando..."

    def _get_progress_bar(self) -> str:
        """
        Genera una barra de progreso visual

        Returns:
            Barra de progreso en formato [===>    ]
        """
        filled = int((self.progress_percentage / 100) * PROGRESS_BAR_WIDTH)
        bar = "=" * filled + ">" + " " * (PROGRESS_BAR_WIDTH - filled)
        return f"[{bar}]"

    def _get_size_display(self) -> str:
        """
        Formatea el tamaño del archivo para display

        Returns:
            Tamaño en formato "X.X MB / Y.Y MB"
        """
        processed_mb = self.processed_size_bytes / 1024 / 1024
        total_mb = self.total_size_bytes / 1024 / 1024
        return f"{processed_mb:.1f} MB / {total_mb:.1f} MB"

    def _get_speed_display(self) -> str:
        """
        Calcula la velocidad de procesamiento

        Returns:
            Velocidad en formato "X.X MB/s"
        """
        elapsed = time.time() - self.start_time

        if elapsed > 0 and self.processed_size_bytes > 0:
            speed_mb_per_sec = (self.processed_size_bytes / 1024 / 1024) / elapsed
            return f"{speed_mb_per_sec:.1f} MB/s"

        return "Calculando..."

    def _get_status_message(self) -> str:
        """
        Genera el mensaje de estado completo

        Returns:
            Mensaje formateado con toda la información de progreso
        """
        # Línea de tarea
        message = f"🔄 **{self.task_name}**...\n\n"

        # Línea de progreso con barra visual
        message += f"📊 **Progreso:** {self.progress_percentage:.0f}% | {self._get_progress_bar()}\n"

        # Tiempo transcurrido
        message += f"⏱️ **Tiempo transcurrido:** {self._get_elapsed_time()}\n"

        # Tiempo restante estimado
        message += f"⏳ **Tiempo restante:** {self._get_remaining_time()}\n"

        # Tamaño procesado
        message += f"📦 **Tamaño procesado:** {self._get_size_display()}\n"

        # Velocidad (opcional)
        if self.show_speed:
            message += f"🎯 **Velocidad:** {self._get_speed_display()}\n"

        message += "\nEl procesamiento continúa. Por favor espera..."

        return message

    def _update_loop(self):
        """Loop de actualización en background"""
        last_update_time = 0

        while self.is_running and not self.is_complete:
            current_time = time.time()

            # Solo actualizar cada intervalo configurado
            if current_time - last_update_time >= self.update_interval:
                try:
                    new_message = self._get_status_message()
                    self.status_message.edit_text(new_message)
                    last_update_time = current_time
                except Exception as e:
                    # Si falla la actualización, no detener el proceso principal
                    # Solo registrar el error
                    self.error = f"Error updating status: {str(e)}"
                    break

            # Dormir un poco para no consumir CPU
            time.sleep(0.5)

    def finalize(self, completion_message: str):
        """
        Finaliza el tracking con un mensaje de completado

        Args:
            completion_message: Mensaje final a mostrar
        """
        self.stop()
        try:
            self.status_message.edit_text(completion_message)
        except Exception as e:
            self.error = f"Error sending final message: {str(e)}"

    def set_error(self, error_message: str):
        """
        Marca un error y detiene el tracking

        Args:
            error_message: Mensaje de error
        """
        self.error = error_message
        self.stop()
