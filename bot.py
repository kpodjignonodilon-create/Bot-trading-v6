import os, time, requests, urllib.parse, threading
from flask import Flask
import yfinance as yf
import pandas as pd

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "9300299")

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot V8 Odilon - USDJPY BTC - Live"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
        print(f"Envoyé: {msg[:50]}")
    except Exception as e:
        print(f"Erreur: {e}")

def get_signal(ticker, name):
    try:
        data = yf.download(ticker, period="2d", interval="5m", progress=False)
        if data.empty: return f"{name}: Pas de données"
        close = data['Close'].iloc[-1]
        ma20 = data['Close'].rolling(20).mean().iloc[-1]
        if close > ma20:
            return f"🟢 {name} BUY - {float(close):.2f} au dessus MA20"
        else:
            return f"🔴 {name} SELL - {float(close):.2f} en dessous MA20"
    except Exception as e:
        return f"{name}: Erreur {e}"

def bot_loop():
    send_whatsapp("🚀 BOT V8 ODILON LANCE - USD/JPY + BTC actif toutes les 5 min")
    while True:
        try:
            usd = get_signal("USDJPY=X", "USD/JPY")
            btc = get_signal("BTC-USD", "BTC/USD")
            msg = f"📊 SIGNAL ODILON\n\n{usd}\n{btc}\n\nHeure: {time.strftime('%H:%M')}"
            send_whatsapp(msg)
        except Exception as e:
            print(f"Loop erreur: {e}")
        time.sleep(300)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)