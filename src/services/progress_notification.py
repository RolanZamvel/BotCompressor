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
        self._last_update_time = 0  # Controlar frecuencia de actualizaciones
        self._last_text = ""  # Guardar último texto para evitar ediciones duplicadas

        # Variables para compresión
        self._compression_start_time = None
        self._compression_total_bytes = 0
        self._compression_last_update_time = 0
        self._compression_last_text = ""

        # Variables para subida
        self._upload_start_time = None
        self._upload_total_bytes = 0
        self._upload_last_update_time = 0
        self._upload_last_text = ""

    def set_download_total(self, total_bytes: int) -> None:
        """
        Establece el tamaño total de la descarga.

        Args:
            total_bytes: Tamaño total del archivo en bytes
        """
        self._download_total_bytes = total_bytes
        print(f"📐 [PROGRESO] Tamaño total establecido: {total_bytes} bytes ({total_bytes/(1024*1024):.1f} MB)")

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
            total: Bytes totales (puede ser 0 si Pyrogram no lo proporciona)
        """
        # Log para debug: verificar que se llama al callback
        print(f"🔍 [PROGRESO] Callback llamado: {current}/{total} bytes (Pyrogram total)")

        if not self._download_start_time:
            print(f"❌ [PROGRESO] _download_start_time es None, retornando")
            return

        # Usar el tamaño total establecido como fallback
        effective_total = total if total > 0 else self._download_total_bytes
        
        # Actualizar el tamaño total si Pyrogram lo proporciona y es mayor
        if total > self._download_total_bytes:
            self._download_total_bytes = total
            effective_total = total

        elapsed_time = time.time() - self._download_start_time
        current_time = time.time()

        # Calcular porcentaje
        if effective_total > 0:
            progress_percent = (current / effective_total * 100)
        else:
            progress_percent = 0

        print(f"⏱️ [PROGRESO] Tiempo: {elapsed_time:.1f}s, Progreso: {progress_percent:.1f}% ({current}/{effective_total} bytes)")

        # Si han pasado más de 5 segundos y el progreso es significativo
        if elapsed_time >= 5 and progress_percent > 5:
            # Controlar frecuencia de actualizaciones (mínimo 1 segundo entre actualizaciones)
            time_since_last = current_time - self._last_update_time
            if time_since_last < 1.0:
                print(f"⏸️ [PROGRESO] Bloqueado por tiempo: {time_since_last:.1f}s < 1.0s")
                return

            print(f"✅ [PROGRESO] Procediendo con actualización...")

            # Calcular tiempo restantes estimado
            if current > 0 and elapsed_time > 0:
                speed = current / elapsed_time  # bytes por segundo
                remaining_bytes = effective_total - current
                remaining_seconds = remaining_bytes / speed if speed > 0 else 0

                # Formatear tiempo restantes
                if remaining_seconds >= 60:
                    remaining_minutes = int(remaining_seconds // 60)
                    remaining_seconds_int = int(remaining_seconds % 60)
                    time_str = f"{remaining_minutes} min restantes" if remaining_seconds_int == 0 else f"{remaining_minutes} min {remaining_seconds_int}s restantes"
                else:
                    time_str = f"{int(remaining_seconds)}s restantes"
            else:
                time_str = "Calculando..."

            # Generar barra de progreso
            progress_bar = self._generate_progress_bar(progress_percent)

            # Actualizar mensaje
            text = f"📥 **Descargando archivo...**\n  `{progress_percent:.0f}%` • `{time_str}`\n  {progress_bar}"

            print(f"📝 [PROGRESO] Nuevo texto generado")

            # Evitar ediciones duplicadas
            if text == self._last_text:
                print(f"⏭️ [PROGRESO] Texto duplicado, omitiendo actualización")
                return

            # Actualizar mensaje con manejo de errores
            try:
                if self._status_message:
                    print(f"🔄 [PROGRESO] Intentando editar mensaje...")
                    self._status_message.edit_text(text)
                    self._last_update_time = current_time
                    self._last_text = text
                    print(f"✅ [PROGRESO] Mensaje editado exitosamente")
            except Exception as e:
                # Manejar errores específicos de Telegram
                error_str = str(e)
                print(f"❌ [PROGRESO] Error editando: {error_str}")

                # Si el error es MESSAGE_TOO_LONG, crear nuevo mensaje
                if "MESSAGE_TOO_LONG" in error_str or "message too long" in error_str.lower():
                    print("⚠️ [PROGRESO] MESSAGE_TOO_LONG detectado, creando nuevo mensaje...")
                    try:
                        self._status_message = self._message.reply_text(text)
                        self._last_update_time = current_time
                        self._last_text = text
                        print("✅ [PROGRESO] Nuevo mensaje creado")
                    except Exception as e2:
                        print(f"❌ [PROGRESO] Error creando nuevo mensaje: {e2}")
                # Si el error es MESSAGE_NOT_MODIFIED, ignorar (normal)
                elif "MESSAGE_NOT_MODIFIED" in error_str or "message not modified" in error_str.lower():
                    print("ℹ️ [PROGRESO] MESSAGE_NOT_MODIFIED: mensaje ya tiene el contenido")
                    pass
                # Otros errores: loguear
                else:
                    print(f"❌ [PROGRESO] Error no manejado: {e}")
        else:
            print(f"⏸️ [PROGRESO] Bloqueado: tiempo < 5s ({elapsed_time:.1f}s) o progreso < 5% ({progress_percent:.1f}%)")

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

        # Usar ▰ para completado y ▱ para pendiente
        bar = "▰" * filled + "▱" * empty
        return f"  {bar}"

    def notify_compressing(self, estimated_time: str = "") -> None:
        """
        Notifica que se está comprimiendo.

        Args:
            estimated_time: Tiempo estimado (opcional)
        """
        if estimated_time:
            text = f"🔄 **Comprimiendo archivo**...\n⏱️ Tiempo estimado: `{estimated_time}`"
        else:
            text = f"🔄 **Comprimiendo archivo**...\n⏱️ Esto puede tomar un momento dependiendo del tamaño del archivo."

        try:
            if self._status_message:
                self._status_message.edit_text(text)
                self._last_text = text
        except Exception as e:
            error_str = str(e)
            if "MESSAGE_TOO_LONG" in error_str or "message too long" in error_str.lower():
                self._status_message = self._message.reply_text(text)
            elif "MESSAGE_NOT_MODIFIED" in error_str or "message not modified" in error_str.lower():
                pass
            else:
                print(f"❌ Error actualizando mensaje de compresión: {e}")

    def set_compression_total(self, total_bytes: int) -> None:
        """
        Establece el tamaño total para cálculo de progreso de compresión.

        Args:
            total_bytes: Tamaño total del archivo en bytes
        """
        self._compression_total_bytes = total_bytes
        self._compression_start_time = time.time()
        print(f"⚙️ [COMPRESIÓN] Tamaño total establecido: {total_bytes} bytes ({total_bytes/(1024*1024):.1f} MB)")

    def update_compression_progress(self, current_bytes: int) -> None:
        """
        Actualiza el progreso de compresión.

        Args:
            current_bytes: Bytes procesados
        """
        if not self._compression_start_time:
            return

        elapsed_time = time.time() - self._compression_start_time
        current_time = time.time()

        # Calcular porcentaje
        if self._compression_total_bytes > 0:
            progress_percent = (current_bytes / self._compression_total_bytes * 100)
        else:
            progress_percent = 0

        print(f"⏱️ [COMPRESIÓN] Tiempo: {elapsed_time:.1f}s, Progreso: {progress_percent:.1f}% ({current_bytes}/{self._compression_total_bytes} bytes)")

        # Actualizar solo si han pasado 5 segundos o el progreso es significativo
        if elapsed_time >= 5 and progress_percent > 5:
            # Controlar frecuencia de actualizaciones (mínimo 1 segundo)
            time_since_last = current_time - self._compression_last_update_time
            if time_since_last < 1.0:
                print(f"⏸️ [COMPRESIÓN] Bloqueado por tiempo: {time_since_last:.1f}s < 1.0s")
                return

            print(f"✅ [COMPRESIÓN] Procediendo con actualización...")

            # Calcular tiempo restantes estimado
            if current_bytes > 0 and elapsed_time > 0:
                speed = current_bytes / elapsed_time  # bytes por segundo
                remaining_bytes = self._compression_total_bytes - current_bytes
                remaining_seconds = remaining_bytes / speed if speed > 0 else 0

                # Formatear tiempo restantes
                if remaining_seconds >= 60:
                    remaining_minutes = int(remaining_seconds // 60)
                    remaining_seconds_int = int(remaining_seconds % 60)
                    time_str = f"{remaining_minutes} min restantes" if remaining_seconds_int == 0 else f"{remaining_minutes} min {remaining_seconds_int}s restantes"
                else:
                    time_str = f"{int(remaining_seconds)}s restantes"
            else:
                time_str = "Calculando..."

            # Generar barra de progreso
            progress_bar = self._generate_progress_bar(progress_percent)

            # Actualizar mensaje
            text = f"🔄 **Comprimiendo archivo...**\n  `{progress_percent:.0f}%` • `{time_str}`\n  {progress_bar}"

            print(f"📝 [COMPRESIÓN] Nuevo texto generado")

            # Evitar ediciones duplicadas
            if text == self._compression_last_text:
                print(f"⏭️ [COMPRESIÓN] Texto duplicado, omitiendo actualización")
                return

            # Actualizar mensaje con manejo de errores
            try:
                if self._status_message:
                    print(f"🔄 [COMPRESIÓN] Intentando editar mensaje...")
                    self._status_message.edit_text(text)
                    self._compression_last_update_time = current_time
                    self._compression_last_text = text
                    print(f"✅ [COMPRESIÓN] Mensaje editado exitosamente")
            except Exception as e:
                error_str = str(e)
                print(f"❌ [COMPRESIÓN] Error editando: {error_str}")

                if "MESSAGE_TOO_LONG" in error_str or "message too long" in error_str.lower():
                    print("⚠️ [COMPRESIÓN] MESSAGE_TOO_LONG detectado, creando nuevo mensaje...")
                    try:
                        self._status_message = self._message.reply_text(text)
                        self._compression_last_update_time = current_time
                        self._compression_last_text = text
                        print("✅ [COMPRESIÓN] Nuevo mensaje creado")
                    except Exception as e2:
                        print(f"❌ [COMPRESIÓN] Error creando nuevo mensaje: {e2}")
                elif "MESSAGE_NOT_MODIFIED" in error_str or "message not modified" in error_str.lower():
                    print("ℹ️ [COMPRESIÓN] MESSAGE_NOT_MODIFIED: mensaje ya tiene el contenido")
                    pass
                else:
                    print(f"❌ [COMPRESIÓN] Error no manejado: {e}")
        else:
            print(f"⏸️ [COMPRESIÓN] Bloqueado: tiempo < 5s ({elapsed_time:.1f}s) o progreso < 5% ({progress_percent:.1f}%)")

    def set_upload_total(self, total_bytes: int) -> None:
        """
        Establece el tamaño total para cálculo de progreso de subida.

        Args:
            total_bytes: Tamaño total del archivo en bytes
        """
        self._upload_total_bytes = total_bytes
        self._upload_start_time = time.time()
        print(f"⬆️ [SUBIDA] Tamaño total establecido: {total_bytes} bytes ({total_bytes/(1024*1024):.1f} MB)")

    def update_upload_progress(self, current_bytes: int) -> None:
        """
        Actualiza el progreso de subida.

        Args:
            current_bytes: Bytes subidos
        """
        if not self._upload_start_time:
            return

        elapsed_time = time.time() - self._upload_start_time
        current_time = time.time()

        # Calcular porcentaje
        if self._upload_total_bytes > 0:
            progress_percent = (current_bytes / self._upload_total_bytes * 100)
        else:
            progress_percent = 0

        print(f"⬆️ [SUBIDA] Tiempo: {elapsed_time:.1f}s, Progreso: {progress_percent:.1f}% ({current_bytes}/{self._upload_total_bytes} bytes)")

        # Actualizar solo si han pasado 2 segundos o el progreso es significativo
        if elapsed_time >= 2 and progress_percent > 2:
            # Controlar frecuencia de actualizaciones (mínimo 1 segundo)
            time_since_last = current_time - self._upload_last_update_time
            if time_since_last < 1.0:
                print(f"⏸️ [SUBIDA] Bloqueado por tiempo: {time_since_last:.1f}s < 1.0s")
                return

            print(f"✅ [SUBIDA] Procediendo con actualización...")

            # Calcular tiempo restantes estimado
            if current_bytes > 0 and elapsed_time > 0:
                speed = current_bytes / elapsed_time  # bytes por segundo
                remaining_bytes = self._upload_total_bytes - current_bytes
                remaining_seconds = remaining_bytes / speed if speed > 0 else 0

                # Formatear tiempo restantes
                if remaining_seconds >= 60:
                    remaining_minutes = int(remaining_seconds // 60)
                    remaining_seconds_int = int(remaining_seconds % 60)
                    time_str = f"{remaining_minutes} min restantes" if remaining_seconds_int == 0 else f"{remaining_minutes} min {remaining_seconds_int}s restantes"
                else:
                    time_str = f"{int(remaining_seconds)}s restantes"
            else:
                time_str = "Calculando..."

            # Generar barra de progreso
            progress_bar = self._generate_progress_bar(progress_percent)

            # Actualizar mensaje
            text = f"📤 **Enviando archivo comprimido**...\n  `{progress_percent:.0f}%` • `{time_str}`\n  {progress_bar}"

            print(f"📝 [SUBIDA] Nuevo texto generado")

            # Evitar ediciones duplicadas
            if text == self._upload_last_text:
                print(f"⏭️ [SUBIDA] Texto duplicado, omitiendo actualización")
                return

            # Actualizar mensaje con manejo de errores
            try:
                if self._status_message:
                    print(f"🔄 [SUBIDA] Intentando editar mensaje...")
                    self._status_message.edit_text(text)
                    self._upload_last_update_time = current_time
                    self._upload_last_text = text
                    print(f"✅ [SUBIDA] Mensaje editado exitosamente")
            except Exception as e:
                error_str = str(e)
                print(f"❌ [SUBIDA] Error editando: {error_str}")

                if "MESSAGE_TOO_LONG" in error_str or "message too long" in error_str.lower():
                    print("⚠️ [SUBIDA] MESSAGE_TOO_LONG detectado, creando nuevo mensaje...")
                    try:
                        self._status_message = self._message.reply_text(text)
                        self._upload_last_update_time = current_time
                        self._upload_last_text = text
                        print("✅ [SUBIDA] Nuevo mensaje creado")
                    except Exception as e2:
                        print(f"❌ [SUBIDA] Error creando nuevo mensaje: {e2}")
                elif "MESSAGE_NOT_MODIFIED" in error_str or "message not modified" in error_str.lower():
                    print("ℹ️ [SUBIDA] MESSAGE_NOT_MODIFIED: mensaje ya tiene el contenido")
                    pass
                else:
                    print(f"❌ [SUBIDA] Error no manejado: {e}")
        else:
            print(f"⏸️ [SUBIDA] Bloqueado: tiempo < 2s ({elapsed_time:.1f}s) o progreso < 2% ({progress_percent:.1f}%)")

    def notify_sending(self) -> None:
        """Notifica que se está enviando el archivo."""
        text = f"📤 **Enviando archivo comprimido**...\n⏱️ Preparando..."
        try:
            if self._status_message:
                self._status_message.edit_text(text)
                self._last_text = text
        except Exception as e:
            error_str = str(e)
            if "MESSAGE_TOO_LONG" in error_str or "message too long" in error_str.lower():
                self._status_message = self._message.reply_text(text)
            elif "MESSAGE_NOT_MODIFIED" in error_str or "message not modified" in error_str.lower():
                pass
            else:
                print(f"❌ Error actualizando mensaje de envío: {e}")

    def notify_success(self, message: str) -> None:
        """
        Notifica éxito con mensaje personalizado.

        Args:
            message: Mensaje de éxito
        """
        try:
            if self._status_message:
                self._status_message.edit_text(message)
                self._last_text = message
        except Exception as e:
            error_str = str(e)
            if "MESSAGE_TOO_LONG" in error_str or "message too long" in error_str.lower():
                self._status_message = self._message.reply_text(message)
            elif "MESSAGE_NOT_MODIFIED" in error_str or "message not modified" in error_str.lower():
                pass
            else:
                print(f"❌ Error actualizando mensaje de éxito: {e}")

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
