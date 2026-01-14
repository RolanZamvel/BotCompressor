from pyrogram import Client
from plugins.cargador import load_handlers as manejadores

class TelegramBot:
    def __init__(self):
        self.app = Client(
            "mi_bot", 
            api_id="39532396",
            api_hash="7dfa32c18bbac9c85c4bd65c2b6e253a",
            bot_token="8018262234:AAHb3GdVJy_DolhKTHt0F9miSxYwhBljqv0"
            )
        
    def inicializar_manejadores(self):
        manejadores(self.app)
        
    def run(self):
        self.inicializar_manejadores()
        print("Bot activo")
        self.app.run()
        
        
if __name__=="__main__":
    app = TelegramBot()
    app.run()
