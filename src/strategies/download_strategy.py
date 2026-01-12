"""
Download Strategies for YouTube videos.
Follows Open/Closed Principle (OCP) - open for extension, closed for modification.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class IDownloadStrategy(ABC):
    """Interface for download strategies."""

    @abstractmethod
    def get_format_selector(self) -> str:
        """
        Get the format selector for yt-dlp.

        Returns:
            Format selector string
        """
        pass

    @abstractmethod
    def get_download_options(self) -> Dict[str, Any]:
        """
        Get additional download options.

        Returns:
            Dictionary of download options
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Get human-readable description of the strategy.

        Returns:
            Description string
        """
        pass


class BestQualityStrategy(IDownloadStrategy):
    """Strategy for downloading best quality video."""

    def get_format_selector(self) -> str:
        """Select best quality format."""
        return 'best[ext=mp4]/best'

    def get_download_options(self) -> Dict[str, Any]:
        """Get download options for best quality."""
        return {
            'merge_output_format': 'mp4',
        }

    def get_description(self) -> str:
        """Get strategy description."""
        return "Mejor calidad (mayor tamaño)"


class OptimalQualityStrategy(IDownloadStrategy):
    """Strategy for downloading optimal quality (balanced)."""

    def get_format_selector(self) -> str:
        """Select optimal quality format."""
        return 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    def get_download_options(self) -> Dict[str, Any]:
        """Get download options for optimal quality."""
        return {
            'merge_output_format': 'mp4',
            'prefer_ffmpeg': True,
        }

    def get_description(self) -> str:
        """Get strategy description."""
        return "Calidad óptima (balanceado)"


class EfficientQualityStrategy(IDownloadStrategy):
    """Strategy for downloading efficient quality (smaller size)."""

    def get_format_selector(self) -> str:
        """Select efficient quality format."""
        return 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[ext=mp4]'

    def get_download_options(self) -> Dict[str, Any]:
        """Get download options for efficient quality."""
        return {
            'merge_output_format': 'mp4',
            'prefer_ffmpeg': True,
        }

    def get_description(self) -> str:
        """Get strategy description."""
        return "Calidad eficiente (menor tamaño)"


class AudioOnlyStrategy(IDownloadStrategy):
    """Strategy for downloading audio only."""

    def get_format_selector(self) -> str:
        """Select audio only format."""
        return 'bestaudio[ext=m4a]/bestaudio/best'

    def get_download_options(self) -> Dict[str, Any]:
        """Get download options for audio only."""
        return {
            'format': 'bestaudio/best',
            'extract_audio': True,
            'audio_format': 'mp3',
            'audio_quality': '128K',
        }

    def get_description(self) -> str:
        """Get strategy description."""
        return "Solo audio (MP3)"
