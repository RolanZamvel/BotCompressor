from abc import ABC, abstractmethod
from typing import Optional


class IFileManager(ABC):
    """
    Interfaz para manejo de archivos temporales y backup.
    Implementa Interface Segregation Principle (ISP).
    """

    @abstractmethod
    def create_temp_file(self, suffix: str) -> str:
        """
        Crea un archivo temporal.

        Args:
            suffix: Sufijo del archivo temporal

        Returns:
            str: Ruta del archivo temporal creado
        """
        pass

    @abstractmethod
    def create_backup(self, file_path: str) -> Optional[str]:
        """
        Crea una copia de seguridad del archivo.

        Args:
            file_path: Ruta del archivo original

        Returns:
            Optional[str]: Ruta del archivo backup o None si falla
        """
        pass

    @abstractmethod
    def cleanup_file(self, file_path: str) -> bool:
        """
        Elimina un archivo de forma segura.

        Args:
            file_path: Ruta del archivo a eliminar

        Returns:
            bool: True si se eliminó correctamente
        """
        pass

    @abstractmethod
    def cleanup_all(self, file_paths: list) -> None:
        """
        Elimina múltiples archivos de forma segura.

        Args:
            file_paths: Lista de rutas de archivos a eliminar
        """
        pass

    @abstractmethod
    def get_file_size_mb(self, file_path: str) -> float:
        """
        Obtiene el tamaño de un archivo en MB.

        Args:
            file_path: Ruta del archivo

        Returns:
            float: Tamaño en MB
        """
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """
        Verifica si un archivo existe y tiene contenido.

        Args:
            file_path: Ruta del archivo

        Returns:
            bool: True si el archivo existe y tiene tamaño > 0
        """
        pass
