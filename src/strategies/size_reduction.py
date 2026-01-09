from typing import Dict
from .compression_strategy import ICompressionStrategy


class SizeReductionStrategy(ICompressionStrategy):
    """
    Estrategia de compresión que prioriza la reducción de tamaño.
    Implementa Open/Closed Principle (OCP).
    """

    def get_parameters(self) -> Dict:
        return {
            "crf": 28,
            "bitrate": "500k",
            "preset": "medium",
            "quality": "low"
        }

    def get_description(self) -> str:
        return "📊 **Comprimiendo (mayor compresión)**"

    def get_estimated_time_factor(self) -> float:
        return 1.0
