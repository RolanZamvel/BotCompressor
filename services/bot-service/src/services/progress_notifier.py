"""
Enhanced ProgressNotifier for BotCompressor 2.0
"""

from pyrogram.types import Message
import asyncio
from datetime import datetime

class ProgressNotifier:
    """Enhanced progress notifier with better status updates"""
    
    def __init__(self, message: Message):
        self.message = message
        self.current_message = None
        self.download_total = 0
        self.compression_total = 0
        self.upload_total = 0
        
    async def notify_downloading(self):
        """Notify download start"""
        text = "📥 **Descargando archivo...**\n\n⏳ Por favor espera..."
        self.current_message = await self.message.reply_text(text)
        
    async def notify_compressing(self, estimated_time: str):
        """Notify compression start"""
        text = f"🗜️ **Comprimiendo archivo...**\n\n⏱️ Tiempo estimado: {estimated_time}\n⏳ Por favor espera..."
        if self.current_message:
            await self.current_message.edit_text(text)
        else:
            self.current_message = await self.message.reply_text(text)
            
    async def notify_sending(self):
        """Notify upload start"""
        text = "📤 **Enviando archivo comprimido...**\n\n⏳ Casi listo..."
        if self.current_message:
            await self.current_message.edit_text(text)
        else:
            self.current_message = await self.message.reply_text(text)
            
    async def notify_success(self, success_message: str):
        """Notify successful completion"""
        text = f"✅ **¡Completado!**\n\n{success_message}"
        if self.current_message:
            await self.current_message.edit_text(text)
        else:
            await self.message.reply_text(text)
            
    async def notify_error(self, error_message: str):
        """Notify error"""
        text = f"❌ **Error**\n\n{error_message}"
        if self.current_message:
            await self.current_message.edit_text(text)
        else:
            await self.message.reply_text(text)
            
    def set_download_total(self, total: int):
        """Set total download size"""
        self.download_total = total
        
    def set_compression_total(self, total: int):
        """Set total compression size"""
        self.compression_total = total
        
    def set_upload_total(self, total: int):
        """Set total upload size"""
        self.upload_total = total
        
    async def update_download_progress(self, current: int):
        """Update download progress"""
        if self.download_total > 0:
            percentage = (current / self.download_total) * 100
            current_mb = current / (1024 * 1024)
            total_mb = self.download_total / (1024 * 1024)
            
            text = (
                f"📥 **Descargando archivo...**\n\n"
                f"📊 Progreso: {percentage:.1f}%\n"
                f"📏 Tamaño: {current_mb:.1f} MB / {total_mb:.1f} MB"
            )
            
            if self.current_message:
                try:
                    await self.current_message.edit_text(text)
                except:
                    pass  # Message might be too old to edit
                    
    async def update_compression_progress(self, current: int):
        """Update compression progress"""
        if self.compression_total > 0:
            percentage = (current / self.compression_total) * 100
            current_mb = current / (1024 * 1024)
            total_mb = self.compression_total / (1024 * 1024)
            
            text = (
                f"🗜️ **Comprimiendo archivo...**\n\n"
                f"📊 Progreso: {percentage:.1f}%\n"
                f"📏 Procesado: {current_mb:.1f} MB / {total_mb:.1f} MB"
            )
            
            if self.current_message:
                try:
                    await self.current_message.edit_text(text)
                except:
                    pass
                    
    async def update_upload_progress(self, current: int):
        """Update upload progress"""
        if self.upload_total > 0:
            percentage = (current / self.upload_total) * 100
            current_mb = current / (1024 * 1024)
            total_mb = self.upload_total / (1024 * 1024)
            
            text = (
                f"📤 **Enviando archivo...**\n\n"
                f"📊 Progreso: {percentage:.1f}%\n"
                f"📏 Enviado: {current_mb:.1f} MB / {total_mb:.1f} MB"
            )
            
            if self.current_message:
                try:
                    await self.current_message.edit_text(text)
                except:
                    pass

    def update(self, progress: float):
        """Legacy update method for compatibility"""
        # This would be used by older compression code
        pass