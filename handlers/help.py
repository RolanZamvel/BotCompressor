from pyrogram.types import Message
from plugins.cargador import load_helpers

messages : str

def register(app, interface):
    #cargar pagina de ayuda
    messages = load_helpers(app)
    
    @interface.command("help")
    async def start_command(client, message: Message):
        if(messages):
            await message.reply(
                messages
            )
        else:
            await message.reply(
                "no hay comandos para mostrar"
            )

def help():
    return "/help: Comandos disponibles"
    