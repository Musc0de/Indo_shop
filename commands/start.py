from telebot.types import Message
from utils.db import save_user_to_db

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message: Message):
        welcome_text = ("✨ Selamat datang di Xstore! ✨\n\nKami menyediakan berbagai Akun Premium "
                        "berkualitas tinggi dengan harga terjangkau. Pelayanan cepat dijamin! 🚀\n\n"
                        "Untuk melihat daftar stok akun, ketik: /stok 📜\nButuh bantuan? Ketik: /help 🙋‍♀️\n"
                        "Ingin menghubungi admin? Ketik: /admin 🧑‍💻\nKami siap melayani Anda dengan sepenuh hati! 💖")
        bot.reply_to(message, welcome_text)
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        username = message.from_user.username
        save_user_to_db(user_id, first_name, last_name, username)
