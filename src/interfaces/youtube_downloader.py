"""
Interface for YouTube downloader service.
Follows Dependency Inversion Principle (DIP) - depends on abstractions.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable


class IYouTubeDownloader(ABC):
    """Interface for YouTube video downloader implementations."""

    @abstractmethod
    def download(
        self,
        url: str,
        format_id: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> str:
        """
        Download video from YouTube.

        Args:
            url: YouTube video URL
            format_id: Optional format identifier
            progress_callback: Optional callback for progress updates

        Returns:
            Path to downloaded file

        Raises:
            Exception: If download fails
        """
        pass

    @abstractmethod
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get video information without downloading.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary with video information

        Raises:
            Exception: If info extraction fails
        """
        pass

    @abstractmethod
    def get_available_formats(self, url: str) -> list:
        """
        Get available video formats.

        Args:
            url: YouTube video URL

        Returns:
            List of available formats

        Raises:
            Exception: If format extraction fails
        """
        pass
