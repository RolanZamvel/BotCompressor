from abc import ABC, abstractmethod
from typing import Dict


class ICompressionStrategy(ABC):
    """
    Interfaz base para estrategias de compresión.
    Implementa Open/Closed Principle (OCP).
    """

    @abstractmethod
    def get_parameters(self) -> Dict:
        """
        Retorna los parámetros de compresión.

        Returns:
            Dict: Diccionario con parámetros de compresión
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Retorna una descripción de la estrategia.

        Returns:
            str: Descripción de la estrategia
        """
        pass

    @abstractmethod
    def get_estimated_time_factor(self) -> float:
        """
        Retorna el factor de tiempo estimado para compresión.

        Returns:
            float: Factor multiplicador del tiempo estimado
        """
        pass
