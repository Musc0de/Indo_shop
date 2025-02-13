from telebot.types import Message

def register_handlers(bot):
    @bot.message_handler(func=lambda message: True)
    def handle_unknown(message: Message):
        bot.reply_to(message, "Maaf, perintah tidak dikenal. Silakan ketik /start untuk melihat opsi yang tersedia.")
