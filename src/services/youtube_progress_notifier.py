"""
YouTube Progress Notifier Service.
Follows Single Responsibility Principle (SRP) - only notifies progress updates.
"""
from typing import Dict, Any, Optional

from src.interfaces.progress_tracker import IProgressTracker


class YouTubeProgressNotifier(IProgressTracker):
    """Service for notifying YouTube download progress to Telegram users."""

    def __init__(self, message, update_interval: int = 5):
        """
        Initialize the progress notifier.

        Args:
            message: Telegram message to update with progress
            update_interval: Update message every N percent
        """
        self.message = message
        self.update_interval = update_interval
        self.current_progress: Dict[str, Any] = {}
        self.last_update_percent = 0

    def update(self, progress_data: Dict[str, Any]) -> None:
        """
        Update progress status and notify user if needed.

        Args:
            progress_data: Dictionary containing progress information
                         (percent, downloaded, total, speed, eta, etc.)
        """
        self.current_progress = progress_data.copy()

        # Check if we should update the message
        percent = progress_data.get('percent', 0)
        if abs(percent - self.last_update_percent) >= self.update_interval or percent >= 100:
            self._notify_user()
            self.last_update_percent = percent

    def get_current_progress(self) -> Dict[str, Any]:
        """
        Get current progress state.

        Returns:
            Dictionary with current progress information
        """
        return self.current_progress.copy()

    def reset(self) -> None:
        """Reset progress tracking."""
        self.current_progress = {}
        self.last_update_percent = 0

    def _notify_user(self) -> None:
        """Send progress notification to user."""
        try:
            percent = self.current_progress.get('percent', 0)
            downloaded = self.current_progress.get('downloaded', 0)
            total = self.current_progress.get('total', 0)
            speed = self.current_progress.get('speed', 0)
            eta = self.current_progress.get('eta', 0)

            # Convert to MB for better readability
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            speed_mb = speed / (1024 * 1024)

            # Format ETA
            if eta > 0:
                eta_str = f"{int(eta // 60)}m {int(eta % 60)}s"
            else:
                eta_str = "calculando..."

            # Create progress bar
            progress_bar = self._create_progress_bar(percent)

            # Format message
            message_text = (
                f"📥 **Descargando video de YouTube...**\n\n"
                f"{progress_bar}\n\n"
                f"📊 Progreso: {percent:.1f}%\n"
                f"📏 {downloaded_mb:.1f} / {total_mb:.1f} MB\n"
                f"⚡ Velocidad: {speed_mb:.1f} MB/s\n"
                f"⏱️ Tiempo restante: {eta_str}"
            )

            self.message.edit_text(message_text)

        except Exception as e:
            # Silently fail to avoid interrupting download
            print(f"Error notifying progress: {e}")

    def _create_progress_bar(self, percent: float, length: int = 10) -> str:
        """
        Create a visual progress bar.

        Args:
            percent: Progress percentage (0-100)
            length: Length of the progress bar in characters

        Returns:
            Progress bar string
        """
        filled = int(length * percent / 100)
        bar = '█' * filled + '░' * (length - filled)
        return f"[{bar}]"

    def notify_error(self, error_message: str) -> None:
        """
        Notify user about an error.

        Args:
            error_message: Error message to display
        """
        try:
            text = f"❌ **Error durante la descarga:**\n\n{error_message}"
            self.message.edit_text(text)
        except Exception:
            pass

    def notify_completion(self) -> None:
        """Notify user about download completion."""
        try:
            text = "✅ **Descarga completada!**\n\nComprimiendo el video..."
            self.message.edit_text(text)
        except Exception:
            pass
