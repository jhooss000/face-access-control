import requests

# Reemplaza con tus valores
TELEGRAM_TOKEN = "7594546848:AAF9U_dclxNLLbW0JvdiUNSF_7eJv2VEJbg"
CHAT_ID = "1705639602"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR Telegram] {e}")
        return False

