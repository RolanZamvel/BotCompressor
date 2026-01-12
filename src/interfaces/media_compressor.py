from abc import ABC, abstractmethod
from typing import Tuple, Optional, Callable


class IMediaCompressor(ABC):
    """
    Interfaz base para compresores de medios.
    Implementa Interface Segregation Principle (ISP).
    """

    @abstractmethod
    def compress(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Tuple[bool, str]:
        """
        Comprime un archivo de medios.

        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida
            progress_callback: Callback opcional para notificar progreso (0-100)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass

    @abstractmethod
    def get_output_format(self) -> str:
        """
        Retorna el formato de salida del compresor.

        Returns:
            str: Extensión del formato de salida (ej: '.mp3', '.mp4')
        """
        pass
