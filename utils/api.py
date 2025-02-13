import requests
from config import BASE_URL, HEADERS

def update_order_status(order_id, status):
    try:
        api_url = f"{BASE_URL}orders?q={{\"order_id\":\"{order_id}\"}}"
        response = requests.get(api_url, headers=HEADERS)
        orders = response.json()

        if orders:
            order_id_db = orders[0]['_id']
            update_data = {"payment_status": status}
            update_response = requests.patch(f"{BASE_URL}orders/{order_id_db}", json=update_data, headers=HEADERS)
            if update_response.status_code == 200:
                print(f"Order ID {order_id} status updated to {status}")
            else:
                print(f"Failed to update order ID {order_id} status")
        else:
            print(f"Order ID {order_id} not found for status update")
    except Exception as e:
        print(f"Error in update_order_status: {e}")

def send_to_external_api(order_id, product_name, total_price):
    try:
        api_url = 'http://indoshop.site/api/receive_order.php'
        data = {
            'order_id': order_id,
            'product_name': product_name,
            'total_price': total_price
        }
        response = requests.post(api_url, data=data)
        if response.status_code == 200:
            print("Data berhasil dikirim ke API eksternal")
        else:
            print("Gagal mengirim data ke API eksternal")
    except Exception as e:
        print(f"Error in send_to_external_api: {e}")
