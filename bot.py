from flask import Flask
import threading
import requests
import time
import urllib.parse

app = Flask(__name__)

APIKEY = "3189307"
PHONE = "2290191083450"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

@app.route('/')
def home():
    return "Bot trading V6 en ligne - Odilon"

def run_web():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_web, daemon=True).start()

def send_whatsapp(msg):
    try:
        text = urllib.parse.quote(msg)
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={text}&apikey={APIKEY}"
        r = requests.get(url, timeout=15)
        print(f"WhatsApp envoyé: {r.text}")
    except Exception as e:
        print(f"Erreur WhatsApp: {e}")

def get_signal(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=10).json()
        price = float(r['lastPrice'])
        change = float(r['priceChangePercent'])
        if change > 2.5:
            return f"🚀 {symbol} HAUSSIER +{change:.2f}% Prix: {price}"
        elif change < -2.5:
            return f"📉 {symbol} BAISSIER {change:.2f}% Prix: {price}"
        return None
    except:
        return None

send_whatsapp("✅ BOT V6 WHATSAPP LANCE - BTC/ETH/SOL/BNB")
print("BOT LANCE")

while True:
    for sym in SYMBOLS:
        sig = get_signal(sym)
        if sig:
            send_whatsapp(sig)
    time.sleep(60)