import os
import time
import requests
from datetime import datetime
import pytz
from flask import Flask
import threading

PHONE = os.getenv("PHONE", "2290196118878")
APIKEY = os.getenv("APIKEY", "9300299")
FOREX_ALERT_PCT = 0.4
CRYPTO_ALERT_PCT = 2.5

last_prices = {}
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot trading V7 en ligne - Odilon - USD/JPY CAD/JPY BTS"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={requests.utils.quote(msg)}&apikey={APIKEY}"
        r = requests.get(url, timeout=10)
        print(f"WhatsApp: {r.text}")
    except Exception as e:
        print(f"Erreur: {e}")

def get_time_cotonou():
    tz = pytz.timezone('Africa/Porto-Novo')
    return datetime.now(tz).strftime("%H:%M:%S %d/%m/%Y")

def get_forex_rate(base, target):
    try:
        r = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=10).json()
        if 'rates' in r and target in r['rates']:
            return float(r['rates'][target])
    except: pass
    try:
        r = requests.get(f"https://api.frankfurter.app/latest?from={base}&to={target}", timeout=10).json()
        if 'rates' in r and target in r['rates']:
            return float(r['rates'][target])
    except: pass
    return None

def get_crypto_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=10).json()
        return float(r['lastPrice']), float(r['priceChangePercent'])
    except:
        return None, None

def format_alert(pair_name, price, pct, market_type):
    heure = get_time_cotonou()
    direction = "HAUSSIER 🚀" if pct > 0 else "BAISSIER 📉"
    conseil = "💡 CONSEIL: ACHETER" if pct > 0 else "💡 CONSEIL: VENDRE / ATTENDRE"
    emoji = "💱" if market_type=="FOREX" else "💰"
    return f"{direction} {pair_name}\n{emoji} Prix: {price}\n📊 Variation: {pct:+.2f}%\n🕒 Heure: {heure} (Cotonou)\n{conseil}\n🤖 Bot V7 Odilon"

def bot_loop():
    print("BOT V7 LANCE")
    send_whatsapp(f"✅ BOT V7 PRO LANCE\n💱 USD/JPY, CAD/JPY, BTS\n🕒 {get_time_cotonou()}")
    while True:
        try:
            price = get_forex_rate("USD", "JPY")
            if price:
                old = last_prices.get("USD/JPY")
                if old:
                    pct = ((price-old)/old)*100
                    if abs(pct) >= FOREX_ALERT_PCT:
                        send_whatsapp(format_alert("USD/JPY", round(price,3), pct, "FOREX"))
                        last_prices["USD/JPY"]=price
                else: last_prices["USD/JPY"]=price
            time.sleep(2)
            price = get_forex_rate("CAD", "JPY")
            if price:
                old = last_prices.get("CAD/JPY")
                if old:
                    pct = ((price-old)/old)*100
                    if abs(pct) >= FOREX_ALERT_PCT:
                        send_whatsapp(format_alert("CAD/JPY", round(price,3), pct, "FOREX"))
                        last_prices["CAD/JPY"]=price
                else: last_prices["CAD/JPY"]=price
            time.sleep(2)
            price, chg = get_crypto_price("BTSUSDT")
            if price and abs(chg) >= CRYPTO_ALERT_PCT:
                if time.time() - last_prices.get("BTS_ALERT",0) > 3600:
                    send_whatsapp(format_alert("BTS/USDT", price, chg, "CRYPTO"))
                    last_prices["BTS_ALERT"]=time.time()
            time.sleep(60)
        except Exception as e:
            print(e); time.sleep(30)

threading.Thread(target=bot_loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))