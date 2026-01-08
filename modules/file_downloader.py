"""
Módulo de descarga de archivos para BotCompressor

Responsabilidades (SRP):
- Descargar archivos de Telegram
- Crear copias de seguridad para rollback
- Calcular información de tamaño del archivo
"""

import os
import shutil
import tempfile
from typing import Tuple, Optional


class FileDownloader:
    """
    Clase responsable de descargar archivos desde Telegram
    """

    def __init__(self, client):
        """
        Inicializa el downloader con un cliente de Pyrogram

        Args:
            client: Cliente de Pyrogram para descargar archivos
        """
        self.client = client

    def download(
        self,
        file_id: str,
        create_backup: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Descarga un archivo y opcionalmente crea una copia de seguridad

        Args:
            file_id: ID del archivo en Telegram
            create_backup: Si True, crea copia de seguridad del original

        Returns:
            Tupla (downloaded_file_path, backup_file_path)
            backup_file_path es None si create_backup=False
        """
        try:
            # Descargar archivo
            downloaded_file = self.client.download_media(file_id)

            # Crear copia de seguridad si se solicita
            backup_file = None
            if create_backup:
                with tempfile.NamedTemporaryFile(delete=False, suffix="_backup") as backup_temp:
                    backup_file = backup_temp.name
                shutil.copy2(downloaded_file, backup_file)

            return downloaded_file, backup_file

        except Exception as e:
            raise Exception(f"Error al descargar archivo: {str(e)}")

    def get_file_info(self, file_path: str) -> dict:
        """
        Obtiene información del archivo

        Args:
            file_path: Ruta del archivo

        Returns:
            Diccionario con información del archivo:
            {
                'size_bytes': int,
                'size_mb': float,
                'exists': bool
            }
        """
        try:
            size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            size_mb = size_bytes / 1024 / 1024

            return {
                'size_bytes': size_bytes,
                'size_mb': size_mb,
                'exists': os.path.exists(file_path)
            }
        except Exception as e:
            raise Exception(f"Error al obtener información del archivo: {str(e)}")

    def cleanup(self, *file_paths: str):
        """
        Elimina archivos temporales de forma segura

        Args:
            *file_paths: Lista de rutas de archivos a eliminar
        """
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    # No lanzar error si falla limpieza de un archivo temporal
                    pass
