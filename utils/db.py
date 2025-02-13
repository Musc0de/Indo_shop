import requests
from config import BASE_URL, HEADERS

def save_user_to_db(user_id, first_name, last_name, username):
    url = f"{BASE_URL}users"
    
    # Cek apakah user_id sudah ada di database
    response = requests.get(f"{url}?q={{\"user_id\": \"{user_id}\"}}", headers=HEADERS)
    users = response.json()

    if users:  # Jika user sudah ada
        existing_user = users[0]  # Ambil data user yang sudah ada
        
        # Periksa apakah ada perubahan pada first_name, last_name, atau username
        if (existing_user['first_name'] != first_name or 
            existing_user['last_name'] != last_name or 
            existing_user['username'] != username):
            
            update_data = {
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
            }
            
            update_response = requests.patch(f"{url}/{existing_user['_id']}", json=update_data, headers=HEADERS)
            if update_response.status_code == 200:
                print(f"User {user_id} updated in the database.")
            else:
                print(f"Failed to update user {user_id}. Response: {update_response.text}")
        else:
            print(f"User {user_id} already exists and no update is necessary.")
    
    else:  # Jika user belum ada, tambahkan ke database
        next_id = len(users) + 1
        dummy_email = f"{username or 'user'}_{user_id}@random.com"

        data = {
            "no": next_id,
            "user_id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": dummy_email,
            "active": True
        }
        response = requests.post(url, json=data, headers=HEADERS)
        if response.status_code == 201:
            print(f"User {user_id} with ID {next_id} saved to database.")
        else:
            print(f"Failed to save user {user_id} to database. Response: {response.text}")
