from telebot.types import Message

def register_handlers(bot):
    @bot.message_handler(commands=['help'])
    def send_help(message: Message):
        help_text = ("🙋‍♀️ Bingung atau butuh bantuan? Jangan khawatir, kami siap membantu! Silakan tanyakan apa saja "
                     "seputar Xstore, akun premium, atau proses pembelian. Kami akan dengan senang hati membantu Anda! 😊")
        bot.reply_to(message, help_text)
