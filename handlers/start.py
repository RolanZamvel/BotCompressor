from pyrogram.types import Message

def register(app, interface):
    
    @interface.command("start")
    async def start_command(client, message: Message):
        await message.reply(
            "¡Hola! Soy tu bot. Usa /help para ver comandos."
        )

def help():
    return "/start: Iniciar el bot"
        