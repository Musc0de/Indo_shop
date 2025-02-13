import requests
from telebot.types import Message
from config import BASE_URL, HEADERS

def register_handlers(bot):
    @bot.message_handler(commands=['stok'])
    
    def send_stock_info(message: Message):
        try:
            print(f"User {message.chat.id} requested /stok")

            response = requests.get(BASE_URL + 'services', headers=HEADERS)
            services = response.json()

            response_text = "╔┈──〔 BOT AUTO ORDER 〕\n" \
                            "┊ • \n" \
                            "┊ • ketik stok untuk melihat stok & code produk \n" \
                            "┊ • ketik buynow ( code ) ( jumlah )\n" \
                            "┊ • contoh : buynow netflix 1\n" \
                            "┊ • pastikan code & jumlah di ketik dengan benar\n" \
                            "╚┈┈┈┈───────•\n\n"

            for service in services:
                response_text += (f"╔┈──〔 {service['service_name']} 〕\n"
                                  f"┊ • 💰 Harga: Rp.{service['price']}\n"
                                  f"┊ • 📦 Stok Tersedia: {service['current_stock']}\n"
                                  f"┊ • 🔑 Code: {service['product_code']}\n"
                                  f"┊ • ✍🏽 Ketik: buynow {service['product_code']} 1\n"
                                  f"┊ • 📜 Deskripsi: {service['service_name']}\n"
                                  f"╚┈┈┈┈───────•\n\n")

            bot.reply_to(message, response_text)
            print(f"Sent stock info to user {message.chat.id}")
        except Exception as e:
            print(f"Error in send_stock_info: {e}")
            bot.reply_to(message, "Terjadi kesalahan dalam mengambil informasi stok Please Try Again.")
