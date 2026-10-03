import os
import time
import requests
import urllib.parse
from datetime import datetime
import pytz
from flask import Flask
import threading

# CORRIGÉ : sans le 0 après 229
PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "9300299")
FOREX_ALERT_PCT = 0.4
CRYPTO_ALERT_PCT = 2.5

last_prices = {}
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot trading V7 en ligne - Odilon - USD/JPY CAD/JPY BTC - LIVE"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        r = requests.get(url, timeout=15)
        print(f"WhatsApp envoyé: {r.text[:100]}")
        return True
    except Exception as e:
        print(f"Erreur WhatsApp: {e}")
        return False

def get_crypto_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        r = requests.get(url, timeout=10).json()
        return float(r['price'])
    except:
        return None

def get_forex_price(pair="USDJPY"):
    try:
        # Utilise exchangerate gratuit
        base = pair[:3]
        target = pair[3:]
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        r = requests.get(url, timeout=10).json()
        return float(r['rates'][target])
    except:
        return None

def bot_loop():
    print("BOT V7 LANCE")
    send_whatsapp("✅ BOT V7 LANCE - Odilon - USD/JPY CAD/JPY BTC en surveillance")

    symbols_crypto = ["BTC", "ETH", "SOL", "BNB"]
    symbols_forex = ["USDJPY", "CADJPY"]

    while True:
        try:
            # 1. Crypto
            for sym in symbols_crypto:
                price = get_crypto_price(sym)
                if price:
                    old = last_prices.get(sym)
                    if old:
                        pct = abs(price - old) / old * 100
                        if