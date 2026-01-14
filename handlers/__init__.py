from pyrogram import Client, filters
from typing import Callable

class CommandInterface:
    def __init__(self, app: Client):
        self.app = app
        self.handlers = []
    
    def command(self, cmd: str, **kwargs):
        """Decorador para registrar comandos"""
        def decorator(func: Callable):
            # Registra el comando con el decorador de Pyrogram
            handler = self.app.on_message(
                filters.command(cmd) & filters.incoming, 
                **kwargs
            )(func)
            self.handlers.append(handler)
            return func
        return decorator
    
    def media(self, filtro: str, **kwargs):
        """Decorador para registrar comandos"""
        if filtro not in {"photo", "video", "audio", "document", "voice", "video_note", "animation", "sticker"}:
            raise ValueError(f"Tipo de medio inválido: {filtro}")
        
        def decorator(func: Callable):
            # Registra el comando con el decorador de Pyrogram
            handler = self.app.on_message(
                getattr(filters,filtro) & filters.incoming, 
                **kwargs
            )(func)
            self.handlers.append(handler)
            return func
        return decorator
    
    def message(self, **kwargs):
        """Decorador para mensajes generales"""
        def decorator(func: Callable):
            handler = self.app.on_message(**kwargs)(func)
            self.handlers.append(handler)
            return func
        return decorator