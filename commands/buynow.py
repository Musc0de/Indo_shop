import requests
import time
import threading
import traceback
import random
import os
from telebot import TeleBot
from telebot.types import Message
from config import API_TOKEN, BASE_URL, HEADERS, BSCSCAN_API_KEY
from utils.helpers import generate_order_id, get_indonesia_time
from utils.db import save_user_to_db

# Initialize the bot
bot = TeleBot(API_TOKEN)

def check_payment_status(order_id, payment_address, expected_bnb_amount, expected_idr_amount, chat_id, message_id):
    start_time = time.time()
    while True:
        try:
            elapsed_time = time.time() - start_time
            if elapsed_time > 60:  # 60 seconds = 1 minute
                cancel_unpaid_order(order_id)
                delete_message(chat_id, message_id)  # Delete the payment message
                return

            # Query BscScan API to get transactions for the payment address
            bsc_api_url = f'https://api.bscscan.com/api?module=account&action=txlist&address={payment_address}&startblock=0&endblock=99999999&sort=desc&apikey={BSCSCAN_API_KEY}'
            response = requests.get(bsc_api_url)
            data = response.json()

            # Ensure 'result' key is present and contains a list
            transactions = data.get('result')
            if not isinstance(transactions, list):
                print(f"Unexpected response structure or no transactions found: {data}")
                time.sleep(10)
                continue

            # Check for a transaction with the correct amount
            payment_found = False
            for tx in transactions:
                received_bnb_amount = float(tx['value']) / 10**18
                if (
                    tx['to'].lower() == payment_address.lower() and 
                    received_bnb_amount == expected_bnb_amount and
                    int(tx['confirmations']) >= 1  # Ensure the transaction is confirmed
                ):
                    payment_found = True
                    break 

            if payment_found:
                # Payment found, update order status and send notification
                mark_order_as_paid(order_id)
                notify_user_of_success(order_id)

                # Stop checking payment status once it's paid
                return

            time.sleep(10)  # Check every 10 seconds

        except Exception as e:
            print(f"Error checking payment status: {e}")
            traceback.print_exc()


def delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
        print(f"Deleted message with ID {message_id} for chat {chat_id}.")
    except Exception as e:
        print(f"Error deleting message {message_id} for chat {chat_id}: {e}")
        traceback.print_exc()

def cancel_unpaid_order(order_id):
    try:
        # Retrieve the order by order_id to get the ObjectId and user details
        query_url = f"{BASE_URL}orders?q={{\"order_id\":\"{order_id}\"}}"
        response = requests.get(query_url, headers=HEADERS)
        order = response.json()

        if not order:
            print(f"Order with ID {order_id} not found.")
            return

        order_object_id = order[0]['_id']  # Get the actual MongoDB ObjectId
        chat_id = order[0]['user_id']  # Get the user ID (Telegram chat ID)

        # Notify user that their order will be canceled
        notify_user_of_cancellation(order_id, chat_id)

        # Now delete the order using the ObjectId
        delete_url = f"{BASE_URL}orders/{order_object_id}"
        delete_response = requests.delete(delete_url, headers=HEADERS)
        print(f"Order {order_id} has been canceled due to non-payment. Response: {delete_response.status_code}, {delete_response.text}")
        
    except Exception as e:
        print(f"Error canceling unpaid order {order_id}: {e}")
        traceback.print_exc()

def notify_user_of_cancellation(order_id, chat_id):
    try:
        message = (f"Pesanan Anda dengan nomor {order_id} telah dibatalkan karena tidak dibayar dalam waktu yang ditentukan.")

        # Send notification to user
        send_telegram_message(chat_id, message)

    except Exception as e:
        print(f"Error notifying user of order cancellation: {e}")
        traceback.print_exc()

def mark_order_as_paid(order_id):
    try:
        # Fetch the order to get details
        query_url = f"{BASE_URL}orders?q={{\"order_id\":\"{order_id}\"}}"
        response = requests.get(query_url, headers=HEADERS)
        order = response.json()

        if not order:
            print(f"Order with ID {order_id} not found.")
            return

        order_object_id = order[0]['_id']  # Using the valid ObjectId
        product_name = order[0]['product_name']
        quantity = order[0]['quantity']
        user_id = order[0]['user_id']

        # Update order status to 'paid'
        update_url = f"{BASE_URL}orders/{order_object_id}"
        update_data = {
            "payment_status": "paid",
            "notified": False  # Notify the user separately
        }
        response = requests.patch(update_url, json=update_data, headers=HEADERS)
        print(f"Order update response: {response.status_code}, {response.text}")

        if response.status_code == 200:
            print(f"Order {order_id} status updated to 'paid'")

            # Now update stock after payment confirmation
            update_stock_and_notify(order_object_id, product_name, quantity)

            # Send account details
            send_account_details(order_id, user_id)

        else:
            print(f"Failed to update order status for {order_id}")

    except Exception as e:
        print(f"Error updating order status for {order_id}: {e}")
        traceback.print_exc()

def send_account_details(order_id, user_id):
    try:
        # Tentukan path file 'akun.txt'
        file_path = os.path.join(os.path.dirname(__file__), 'akun.txt')

        # Cek apakah file 'akun.txt' ada
        if not os.path.exists(file_path):
            print(f"File '{file_path}' tidak ditemukan.")
            return

        # Baca file akun.txt
        with open(file_path, 'r+') as file:
            lines = file.readlines()
            account_details = []
            start_index = None

            # Cari akun yang belum terkirim
            for i, line in enumerate(lines):
                if '[SENT]' in line:
                    continue
                if line.startswith('email'):
                    if start_index is not None:
                        break
                    start_index = i
                if start_index is not None:
                    account_details.append(line.strip())

            if not account_details:
                print("Tidak ada akun yang tersedia untuk dikirim.")
                return

            # Gabungkan detail akun menjadi satu pesan
            account_details_message = "\n".join(account_details)

            # Kirim pesan ke user
            chat_id = user_id
            message = (f"Pembayaran Anda untuk pesanan {order_id} telah kami terima.\n\n"
                       f"Berikut adalah detail akun Anda:\n"
                       f"{account_details_message}")

            send_telegram_message(chat_id, message)

            # Tandai akun sebagai terkirim
            for i in range(start_index, start_index + len(account_details)):
                lines[i] = lines[i].strip() + ' [SENT]\n'

            # Update file dengan tanda [SENT]
            file.seek(0)
            file.writelines(lines)
            file.truncate()
    except Exception as e:
        print(f"Error sending account details: {e}")
        traceback.print_exc()

def notify_user_of_success(order_id):
    try:
        # Fetch the order to get user information
        query_url = f"{BASE_URL}orders?q={{\"order_id\":\"{order_id}\"}}"
        response = requests.get(query_url, headers=HEADERS)
        order = response.json()[0]  # Assuming order exists

        chat_id = order['user_id']
        message = (f"Pembayaran Anda untuk pesanan {order_id} telah kami terima\n\n"
                f"* Nomor Pesanan : {order_id}\n"
                f"* Total Harga : Rp.{order['total_price']} (BNB: {order['amount_bnb']:.8f})\n"
                f"* Alamat Transaksi: {order['crypto_address']}\n"
                f"* Produk : {order['product_name']}\n"
                f"* Jumlah : {order['quantity']}")

        # Send notification to user
        send_telegram_message(chat_id, message)

    except Exception as e:
        print(f"Error notifying user of success: {e}")
        traceback.print_exc()

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, data=payload)
    return response.json()

def update_stock_and_notify(order_id, product_name, quantity):
    try:
        # Fetch the product details to update stock
        product_url = f"{BASE_URL}services?q={{\"service_name\":\"{product_name}\"}}"
        product_response = requests.get(product_url, headers=HEADERS)
        products = product_response.json()

        if products:
            product_id = products[0]['_id']
            current_stock = int(products[0]['current_stock'])
            new_stock = current_stock - quantity

            # Update the stock
            stock_update_url = f"{BASE_URL}services/{product_id}"
            stock_update_data = {
                "current_stock": str(new_stock)
            }
            stock_update_response = requests.patch(stock_update_url, json=stock_update_data, headers=HEADERS)
            print(f"Stock update response: {stock_update_response.status_code}, {stock_update_response.text}")

            if stock_update_response.status_code == 200:
                print(f"Updated stock for product {product_name} to {new_stock}")

                # Mark the order as notified
                order_notify_update_url = f"{BASE_URL}orders/{order_id}"
                notify_update_data = {
                    "notified": True
                }
                order_update_response = requests.patch(order_notify_update_url, json=notify_update_data, headers=HEADERS)
                print(f"Order notify update response: {order_update_response.status_code}, {order_update_response.text}")
            else:
                print(f"Failed to update stock for product {product_name}")

        else:
            print(f"Product {product_name} not found.")

    except Exception as e:
        print(f"Error updating stock for product {product_name}: {e}")
        traceback.print_exc()

def register_handlers(bot):
    @bot.message_handler(func=lambda message: message.text.lower().startswith('buynow'))
    def handle_buy_now(message: Message):
        try:
            parts = message.text.split()
            print(f"Received command from {message.chat.id}: {message.text}")
            print(f"Message parts: {parts}")

            if len(parts) < 3:
                bot.reply_to(message, "Format perintah salah. Gunakan: buynow <kode> <jumlah>")
                return

            code = parts[1].lower()
            jumlah = int(parts[2])
            print(f"Code: {code}, Jumlah: {jumlah}")

            response = requests.get(f"{BASE_URL}services?q={{\"product_code\":\"{code}\"}}", headers=HEADERS)
            print(f"API Response for buynow: {response.status_code}, {response.text}")
            services = response.json()

            if not services or jumlah > int(services[0]['current_stock']):
                bot.reply_to(message, "Maaf, stok tidak mencukupi atau produk tidak ditemukan.")
                print(f"Stock issue or product not found for {message.chat.id}")
                return

            # Ambil informasi pengguna
            user_id = message.from_user.id
            first_name = message.from_user.first_name
            last_name = message.from_user.last_name
            username = message.from_user.username

            # Simpan user ke database
            save_user_to_db(user_id, first_name, last_name, username)

            service = services[0]
            harga_per_unit = int(service['price'])
            total_price = harga_per_unit * jumlah

            # Menambahkan fee platform secara acak antara Rp. 0 hingga Rp. 100
            platform_fee = random.randint(0, 100)
            total_payment = total_price + platform_fee

            order_id = generate_order_id()
            order_date = get_indonesia_time()

            # Request the payment link from the PHP script
            payment_response = requests.post(
                'https://indoshop.site/api/payment/v1/payment.php',
                data={'order_id': order_id, 'total_price': total_payment},
                verify=False  # Disable SSL certificate verification
            )

            print(f"Payment API response status: {payment_response.status_code}")
            print(f"Payment API response content: {payment_response.text}")

            payment_data = payment_response.json()

            payment_page_url = payment_data['payment_page']
            bnb_amount = float(payment_data['amount_bnb'])
            crypto_address = payment_data['crypto_address']

            order_data = {
                "order_id": order_id,
                "product_name": service['service_name'],
                "total_price": total_payment,
                "payment_status": "unpaid",
                "order_date": order_date,
                "user_id": user_id,  # Save the user's chat ID with the order
                "quantity": jumlah,  # Save the order quantity for stock updates
                "crypto_address": crypto_address,
                "amount_bnb": bnb_amount
            }
            response = requests.post(BASE_URL + 'orders', json=order_data, headers=HEADERS)
            print(f"Order save response: {response.status_code}, {response.text}")

            # Construct the response message with the payment page URL
            response_text = (f"Berhasil Membuat Transaksi\n"
                             f"Cek Qris Pembayaran Di Private Chat!\n\n"
                             f"「 TRANSAKSI PENDING 」\n\n"
                             f"* Order Number : {order_id}\n"
                             f"* Nama Produk : {service['service_name']}\n"
                             f"* Jumlah Beli : {jumlah}\n"
                             f"* Total Harga : Rp.{total_price}\n"
                             f"* Platform Fee : Rp.{platform_fee}\n"
                             f"* Total Dibayar : Rp.{total_payment}\n"
                             f"* Tanggal Pemesanan : {order_date}\n"
                             f"* Deskripsi : {service['service_name']}\n\n"
                             f"🔗 Pembayaran Crypto:\n"
                             f"BNB yang harus dibayar: {bnb_amount:.8f}\n"
                             f"Address: {crypto_address}\n"
                             f"Link Pembayaran: {payment_page_url}\n\n"
                             f"Harap selesaikan pembayaran dalam 10 menit.")

            sent_message = bot.reply_to(message, response_text)
            print(f"Sent order confirmation to user {message.chat.id}")

            # Start a new thread to periodically check the payment status and delete message if not paid
            threading.Thread(target=check_payment_status, args=(order_id, crypto_address, bnb_amount, total_payment, message.chat.id, sent_message.message_id)).start()

        except Exception as e:
            print(f"Error in handle_buy_now: {e}")
            traceback.print_exc()
            bot.reply_to(message, "Terjadi kesalahan dalam memproses pesanan Anda.")

    # You can add more handlers here if needed

# Main bot entry point
if __name__ == "__main__":
    # Register bot handlers
    register_handlers(bot)

    # Start bot polling
    bot.polling()