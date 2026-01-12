"""
Simple FileManager for BotCompressor 2.0
"""

import os
import tempfile
import shutil
from pathlib import Path

class FileManager:
    """Simple file manager for compression operations"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
    def create_temp_file(self, suffix: str) -> str:
        """Create a temporary file"""
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        return path
        
    def create_backup(self, file_path: str) -> str:
        """Create a backup of the file"""
        try:
            backup_path = file_path + ".backup"
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception:
            return None
            
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists and has content"""
        try:
            return os.path.exists(file_path) and os.path.getsize(file_path) > 0
        except Exception:
            return False
            
    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in MB"""
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0
            
    def cleanup_file(self, file_path: str):
        """Clean up a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
            
    def cleanup_all(self, file_paths: list):
        """Clean up multiple files"""
        for file_path in file_paths:
            self.cleanup_file(file_path)