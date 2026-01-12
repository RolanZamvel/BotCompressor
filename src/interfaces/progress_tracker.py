"""
Interface for progress tracking services.
Follows Interface Segregation Principle (ISP) - focused, specific interfaces.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class IProgressTracker(ABC):
    """Interface for tracking download progress."""

    @abstractmethod
    def update(self, progress_data: Dict[str, Any]) -> None:
        """
        Update progress status.

        Args:
            progress_data: Dictionary containing progress information
                         (percent, downloaded, total, speed, eta, etc.)
        """
        pass

    @abstractmethod
    def get_current_progress(self) -> Dict[str, Any]:
        """
        Get current progress state.

        Returns:
            Dictionary with current progress information
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset progress tracking."""
        pass
