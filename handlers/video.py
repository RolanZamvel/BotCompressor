from pyrogram.types import Message

def register(app, interface):
    
    @interface.media("video")
    async def start_command(client, message: Message):
        await message.reply(
            "video recibido"
        )

def help():
    return "🎥 Procesamiento de videos"