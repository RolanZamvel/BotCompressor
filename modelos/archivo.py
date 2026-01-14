import uuid
import os
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Archivo:
    id_unico: str = field(default_factory=lambda: str(uuid.uuid4())[:8])  # Ej: "a1b2c3d4"
    nombre_original: str = "sin_nombre"
    user_id: int = 0
    etapa_actual: str = "PENDIENTE"  # PENDIENTE → DESCARGA → COMPRESION → SUBIDA → COMPLETADO
    progreso: int = 0  # 0-100%
    creado_en: str = field(default_factory=lambda: datetime.now().isoformat())
    ultima_actualizacion: str = field(default_factory=lambda: datetime.now().isoformat())
  
    
    def avanzar_etapa(self, nueva_etapa: str):
        """Cambia la etapa y reinicia progreso."""
        self.etapa_actual = nueva_etapa
        self.progreso = 0
        self.ultima_actualizacion = datetime.now().isoformat()
    
    def actualizar_progreso(self, porcentaje: int):
        """Actualiza progreso y marca última actualización."""
        self.progreso = max(0, min(100, porcentaje))  # Asegurar 0-100
        self.ultima_actualizacion = datetime.now().isoformat()
    
    def registrar_archivo_temporal(self, ruta: str):
        """Añade una ruta a la lista de archivos para limpieza."""
        if ruta not in self.archivos_temporales:
            self.archivos_temporales.append(ruta)
    
    def get_nombre_mostrar(self, max_len: int = 30) -> str:
        """Devuelve nombre truncado y seguro para mostrar a usuarios."""
        nombre_base = self.nombre_original[:max_len]
        if len(self.nombre_original) > max_len:
            nombre_base += "..."
        return f"`{nombre_base}`"