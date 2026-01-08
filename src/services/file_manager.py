import os
import tempfile
import shutil
from typing import Optional
from ..interfaces.file_handler import IFileManager


class FileManager(IFileManager):
    """
    Implementación concreta del manejo de archivos.
    Implementa Single Responsibility Principle (SRP).
    """

    def create_temp_file(self, suffix: str) -> str:
        """Crea un archivo temporal con el sufijo especificado."""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            return temp_file.name

    def create_backup(self, file_path: str) -> Optional[str]:
        """Crea una copia de seguridad del archivo."""
        try:
            backup_path = self.create_temp_file("_backup")
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception:
            return None

    def cleanup_file(self, file_path: str) -> bool:
        """Elimina un archivo de forma segura."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        return False

    def cleanup_all(self, file_paths: list) -> None:
        """Elimina múltiples archivos de forma segura."""
        for file_path in file_paths:
            self.cleanup_file(file_path)

    def get_file_size_mb(self, file_path: str) -> float:
        """Obtiene el tamaño de un archivo en MB."""
        if os.path.exists(file_path):
            return os.path.getsize(file_path) / 1024 / 1024
        return 0.0

    def file_exists(self, file_path: str) -> bool:
        """Verifica si un archivo existe y tiene contenido."""
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
