"""
YouTube Information Extractor Service.
Follows Single Responsibility Principle (SRP) - only extracts video information.
"""
import re
from typing import Dict, Any, List


class YouTubeInfoExtractor:
    """Service for extracting information from YouTube videos."""

    def __init__(self):
        """Initialize the info extractor."""
        pass

    def extract_video_info(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant information from video data.

        Args:
            video_data: Raw video data from yt-dlp

        Returns:
            Dictionary with extracted information
        """
        return {
            'title': self._extract_title(video_data),
            'duration': self._extract_duration(video_data),
            'duration_str': self._format_duration(self._extract_duration(video_data)),
            'filesize': self._extract_filesize(video_data),
            'filesize_mb': self._extract_filesize(video_data) / (1024 * 1024),
            'thumbnail': self._extract_thumbnail(video_data),
            'url': self._extract_url(video_data),
            'channel': self._extract_channel(video_data),
            'views': self._extract_views(video_data)
        }

    def extract_formats(self, video_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and format available video formats.

        Args:
            video_data: Raw video data from yt-dlp

        Returns:
            List of formatted format options
        """
        formats = []
        seen = set()

        for f in video_data.get('formats', []):
            # Filter for useful video formats
            if f.get('vcodec') != 'none' and f.get('ext') == 'mp4':
                resolution = f.get('resolution', f.get('format_note', 'unknown'))
                filesize = f.get('filesize', 0) / (1024 * 1024)
                format_id = f.get('format_id')

                if format_id not in seen and resolution:
                    formats.append({
                        'format_id': format_id,
                        'resolution': resolution,
                        'filesize_mb': round(filesize, 2),
                        'ext': f.get('ext'),
                        'vcodec': f.get('vcodec'),
                        'acodec': f.get('acodec'),
                        'fps': f.get('fps', 0)
                    })
                    seen.add(format_id)

        # Sort by resolution (descending)
        formats.sort(key=lambda x: self._parse_resolution(x['resolution']), reverse=True)
        return formats[:10]  # Return top 10 formats

    def _extract_title(self, video_data: Dict[str, Any]) -> str:
        """Extract video title."""
        return video_data.get('title', 'Video')

    def _extract_duration(self, video_data: Dict[str, Any]) -> int:
        """Extract video duration in seconds."""
        return video_data.get('duration', 0)

    def _extract_filesize(self, video_data: Dict[str, Any]) -> int:
        """Extract file size in bytes."""
        return video_data.get('filesize', 0)

    def _extract_thumbnail(self, video_data: Dict[str, Any]) -> str:
        """Extract thumbnail URL."""
        return video_data.get('thumbnail', '')

    def _extract_url(self, video_data: Dict[str, Any]) -> str:
        """Extract video URL."""
        return video_data.get('webpage_url', '')

    def _extract_channel(self, video_data: Dict[str, Any]) -> str:
        """Extract channel name."""
        return video_data.get('channel', video_data.get('uploader', 'Unknown'))

    def _extract_views(self, video_data: Dict[str, Any]) -> int:
        """Extract view count."""
        return video_data.get('view_count', 0)

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable string."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            m = seconds // 60
            s = seconds % 60
            return f"{m}m {s}s"
        else:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h}h {m}m {s}s"

    def _parse_resolution(self, res_str: str) -> int:
        """
        Convert resolution string to number for sorting.

        Args:
            res_str: Resolution string (e.g., "1080p", "720p")

        Returns:
            Resolution as integer
        """
        try:
            # Extract first number from resolution string
            match = re.search(r'(\d+)', res_str)
            return int(match.group(1)) if match else 0
        except Exception:
            return 0
