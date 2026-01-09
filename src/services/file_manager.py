import os
import tempfile
import shutil
from typing import Optional
from ..interfaces.file_handler import IFileManager
from ..utils.logger import get_logger


class FileManager(IFileManager):
    """
    Implementación concreta del manejo de archivos.
    Implementa Single Responsibility Principle (SRP).
    """

    def __init__(self):
        """Inicializa el FileManager con logger."""
        self.logger = get_logger(__name__)

    def create_temp_file(self, suffix: str) -> str:
        """Crea un archivo temporal con el sufijo especificado."""
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_path = temp_file.name
                self.logger.debug(f"Archivo temporal creado: {temp_path}")
                return temp_path
        except Exception as e:
            self.logger.error(f"Error creando archivo temporal con sufijo '{suffix}': {str(e)}")
            raise

    def create_backup(self, file_path: str) -> Optional[str]:
        """Crea una copia de seguridad del archivo."""
        try:
            backup_path = self.create_temp_file("_backup")
            shutil.copy2(file_path, backup_path)
            original_size = os.path.getsize(file_path) / 1024 / 1024
            self.logger.info(f"Backup creado: {file_path} ({original_size:.2f}MB) -> {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Error creando backup de {file_path}: {str(e)}")
            return None

    def cleanup_file(self, file_path: str) -> bool:
        """Elimina un archivo de forma segura."""
        try:
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / 1024 / 1024
                os.remove(file_path)
                self.logger.debug(f"Archivo eliminado: {file_path} ({file_size:.2f}MB)")
                return True
            elif file_path:
                self.logger.warning(f"Intentando eliminar archivo que no existe: {file_path}")
        except Exception as e:
            self.logger.error(f"Error eliminando archivo {file_path}: {str(e)}")
        return False

    def cleanup_all(self, file_paths: list) -> None:
        """Elimina múltiples archivos de forma segura."""
        self.logger.debug(f"Limpiando {len(file_paths)} archivos temporales")
        for file_path in file_paths:
            self.cleanup_file(file_path)

    def get_file_size_mb(self, file_path: str) -> float:
        """Obtiene el tamaño de un archivo en MB."""
        try:
            if os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / 1024 / 1024
                self.logger.debug(f"Tamaño de {file_path}: {size_mb:.2f}MB")
                return size_mb
            else:
                self.logger.warning(f"Archivo no existe al obtener tamaño: {file_path}")
                return 0.0
        except Exception as e:
            self.logger.error(f"Error obteniendo tamaño de {file_path}: {str(e)}")
            return 0.0

    def file_exists(self, file_path: str) -> bool:
        """Verifica si un archivo existe y tiene contenido."""
        exists = os.path.exists(file_path) and os.path.getsize(file_path) > 0
        if exists:
            self.logger.debug(f"Archivo verificado: {file_path} existe")
        else:
            self.logger.warning(f"Archivo verificado: {file_path} NO existe o está vacío")
        return exists
