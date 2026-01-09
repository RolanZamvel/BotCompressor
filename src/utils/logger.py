"""
Módulo de logging estructurado para BotCompressor.

Proporciona un sistema de logging centralizado con:
- Formateo estructurado
- Rotación de archivos
- Múltiples niveles (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Logs tanto en consola como en archivo
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


class BotLogger:
    """
    Logger personalizado para el BotCompressor.

    Características:
    - Formato estructurado con timestamp, nivel, nombre, función y línea
    - Rotación automática de archivos (10MB máximo, 5 backups)
    - Salida tanto en consola como en archivo
    - Configuración flexible via variables de entorno
    """

    def __init__(
        self,
        name: str,
        log_dir: str = "logs",
        log_level: str = None,
        console_level: str = None,
        file_level: str = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        Inicializa el logger.

        Args:
            name: Nombre del logger (usualmente __name__ del módulo)
            log_dir: Directorio donde guardar los logs
            log_level: Nivel general de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_level: Nivel de logs para consola
            file_level: Nivel de logs para archivo
            max_file_size: Tamaño máximo del archivo de log en bytes
            backup_count: Número de archivos de backup a mantener
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Evitar duplicar handlers si ya existen
        if self.logger.handlers:
            return

        # Configurar niveles desde variables de entorno o parámetros
        log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
        console_level = console_level or os.getenv("CONSOLE_LOG_LEVEL", "INFO")
        file_level = file_level or os.getenv("FILE_LOG_LEVEL", "DEBUG")

        # Crear formatter estructurado
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, console_level.upper()))
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler con rotación
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            f"{log_dir}/{name}.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, file_level.upper()))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Log inicial
        self.logger.info(f"Logger inicializado: {name} (nivel: {log_level})")

    def debug(self, msg: str, **kwargs):
        """Log a DEBUG message."""
        self.logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs):
        """Log an INFO message."""
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg: str, **kwargs):
        """Log a WARNING message."""
        self.logger.warning(msg, extra=kwargs)

    def error(self, msg: str, exc_info: bool = True, **kwargs):
        """
        Log an ERROR message.

        Args:
            msg: Mensaje de error
            exc_info: Si es True, incluye el stack trace
            **kwargs: Campos adicionales para el log
        """
        self.logger.error(msg, exc_info=exc_info, extra=kwargs)

    def critical(self, msg: str, exc_info: bool = True, **kwargs):
        """
        Log a CRITICAL message.

        Args:
            msg: Mensaje crítico
            exc_info: Si es True, incluye el stack trace
            **kwargs: Campos adicionales para el log
        """
        self.logger.critical(msg, exc_info=exc_info, extra=kwargs)

    def exception(self, msg: str, **kwargs):
        """
        Log an exception with full traceback.

        Args:
            msg: Mensaje de excepción
            **kwargs: Campos adicionales para el log
        """
        self.logger.exception(msg, extra=kwargs)


# Instancia global del logger (se puede usar directamente)
_global_logger: Optional[BotLogger] = None


def get_logger(name: str = "bot_compressor") -> BotLogger:
    """
    Obtiene o crea una instancia del logger.

    Args:
        name: Nombre del logger

    Returns:
        BotLogger: Instancia del logger
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = BotLogger(name)

    return _global_logger
