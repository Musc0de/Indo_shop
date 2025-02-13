from telebot.types import Message

def register_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def send_admin_contact(message: Message):
        admin_text = "🧑‍💻 Punya pertanyaan khusus atau ingin berbicara langsung dengan admin? Hubungi kami melalui Telegram di @mahesaxevier 💬 Kami selalu siap membantu Anda!"
        bot.reply_to(message, admin_text)
