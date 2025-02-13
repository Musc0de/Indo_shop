import random
import datetime
import pytz

def generate_order_id():
    return ''.join([str(random.randint(0, 9)) for _ in range(8)])

def get_indonesia_time():
    indonesia_timezone = pytz.timezone('Asia/Jakarta')
    return datetime.datetime.now(indonesia_timezone).strftime("%m/%d/%Y %H:%M")
