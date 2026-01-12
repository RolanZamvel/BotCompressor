"""
YouTube Downloader Service.
Follows Dependency Inversion Principle (DIP) and Open/Closed Principle (OCP).
Implements IYouTubeDownloader interface and uses download strategies.
"""
import os
from typing import Optional, Dict, Any, Callable
import yt_dlp

from src.interfaces.youtube_downloader import IYouTubeDownloader
from src.strategies.download_strategy import IDownloadStrategy, BestQualityStrategy
from src.services.youtube_info_extractor import YouTubeInfoExtractor
from config import TEMP_FILE_SUFFIX_VIDEO


class YouTubeDownloader(IYouTubeDownloader):
    """
    Service for downloading videos from YouTube.
    Uses yt-dlp as the underlying download engine.
    """

    def __init__(self, download_dir: str = 'downloads'):
        """
        Initialize the YouTube downloader.

        Args:
            download_dir: Directory to store downloaded videos
        """
        self.download_dir = download_dir
        self.info_extractor = YouTubeInfoExtractor()
        self._ensure_download_dir()

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
            format_id: Optional format identifier (overrides strategy)
            progress_callback: Optional callback for progress updates

        Returns:
            Path to downloaded file

        Raises:
            Exception: If download fails
        """
        # Create download options
        ydl_opts = self._build_download_options(format_id, progress_callback)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                # Rename to correct extension if necessary
                filename = self._normalize_filename(filename)

                return filename

        except Exception as e:
            raise Exception(f"Error descargando video: {str(e)}")

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
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return self.info_extractor.extract_video_info(info)

        except Exception as e:
            raise Exception(f"Error obteniendo información del video: {str(e)}")

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
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'listformats': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return self.info_extractor.extract_formats(info)

        except Exception as e:
            raise Exception(f"Error obteniendo formatos disponibles: {str(e)}")

    def download_with_strategy(
        self,
        url: str,
        strategy: IDownloadStrategy,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> str:
        """
        Download video using a specific strategy.

        Args:
            url: YouTube video URL
            strategy: Download strategy to use
            progress_callback: Optional callback for progress updates

        Returns:
            Path to downloaded file
        """
        ydl_opts = self._build_download_options(
            format_id=strategy.get_format_selector(),
            progress_callback=progress_callback
        )

        # Merge strategy options
        ydl_opts.update(strategy.get_download_options())

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filename = self._normalize_filename(filename)
                return filename

        except Exception as e:
            raise Exception(f"Error descargando video: {str(e)}")

    def _build_download_options(
        self,
        format_id: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Build yt-dlp download options.

        Args:
            format_id: Optional format identifier
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary of download options
        """
        opts = {
            'format': format_id if format_id else 'best[ext=mp4]/best',
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'concurrent_fragment_download': True,
            'merge_output_format': 'mp4',
        }

        # Add progress hook if callback provided
        if progress_callback:
            opts['progress_hooks'] = [self._create_progress_hook(progress_callback)]

        return opts

    def _create_progress_hook(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Create a progress hook for yt-dlp.

        Args:
            callback: Progress callback function

        Returns:
            Progress hook function
        """
        def hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)

                percent = (downloaded / total * 100) if total > 0 else 0

                callback({
                    'percent': percent,
                    'downloaded': downloaded,
                    'total': total,
                    'speed': speed,
                    'eta': eta,
                    'status': 'downloading'
                })

        return hook

    def _normalize_filename(self, filename: str) -> str:
        """
        Normalize filename to correct extension.

        Args:
            filename: Original filename

        Returns:
            Normalized filename
        """
        if not filename.endswith(TEMP_FILE_SUFFIX_VIDEO):
            new_filename = filename.rsplit('.', 1)[0] + TEMP_FILE_SUFFIX_VIDEO
            if os.path.exists(filename):
                os.rename(filename, new_filename)
                filename = new_filename

        return filename

    def _ensure_download_dir(self) -> None:
        """Ensure download directory exists."""
        os.makedirs(self.download_dir, exist_ok=True)

    def cleanup_downloaded_file(self, filepath: str) -> None:
        """
        Clean up downloaded file.

        Args:
            filepath: Path to file to delete
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error eliminando archivo {filepath}: {e}")
