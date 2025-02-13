import requests
from telebot.types import Message
from config import BASE_URL, HEADERS, YOUR_ADMIN_USER_ID

def register_handlers(bot):
    @bot.message_handler(commands=['broadcast'])
    def broadcast_message(message: Message):
        if message.from_user.id != YOUR_ADMIN_USER_ID:
            bot.reply_to(message, "Maaf, hanya admin yang dapat menggunakan perintah ini.")
            return

        # Ambil teks yang akan dibroadcast
        broadcast_text = message.text.replace('/broadcast', '').strip()

        # Jika perintah hanya /broadcast tanpa pesan tambahan
        if not broadcast_text:
            bot.reply_to(message, "Anda telah menggunakan perintah /broadcast tanpa pesan. Silakan sertakan pesan yang ingin Anda kirim.")
            return

        try:
            # Mendapatkan daftar user dari database
            response = requests.get(BASE_URL + 'users', headers=HEADERS)
            users = response.json()

            # Mengirim pesan broadcast ke setiap user_id
            for user in users:
                try:
                    bot.send_message(user['user_id'], broadcast_text)
                    print(f"Broadcast message sent to {user['user_id']}")

                except Exception as e:
                    print(f"Failed to send broadcast message to {user['user_id']}: {e}")

            bot.reply_to(message, "Pesan broadcast berhasil dikirim!")
        except Exception as e:
            print(f"Error during broadcasting: {e}")
            bot.reply_to(message, "Terjadi kesalahan saat mengirim pesan broadcast.")
