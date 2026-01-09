from typing import Dict
from .compression_strategy import ICompressionStrategy


class QualityPreservationStrategy(ICompressionStrategy):
    """
    Estrategia de compresión que preserva la calidad del video.
    Implementa Open/Closed Principle (OCP).
    """

    def get_parameters(self) -> Dict:
        return {
            "crf": 18,
            "bitrate": "2M",
            "preset": "slow",
            "quality": "high"
        }

    def get_description(self) -> str:
        return "🎬 **Manteniendo calidad (menor compresión)**"

    def get_estimated_time_factor(self) -> float:
        return 1.5
