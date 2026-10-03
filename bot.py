import os
import time
import requests
import urllib.parse
from flask import Flask
import threading

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "9300299")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot V7 Live Odilon"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        r = requests.get(url, timeout=15)
        print(f"WhatsApp: {r.text}")
        return True
    except Exception as e:
        print(f"Erreur: {e}")
        return False

def bot_loop():
    print("BOT V7 LANCE")
    send_whatsapp("BOT V7 LANCE - Odilon - Test reussi")
    while True:
        time.sleep(60)
        print("Bot en vie...")

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)