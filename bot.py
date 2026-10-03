import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V9.1 FINAL Odilon - Live 2H"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
    except: pass

def get_all_prices():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd", timeout=20).json()
        return r
    except:
        return {"bitcoin":{"usd":0},"ethereum":{"usd":0},"solana":{"usd":0}}

def get_support_resistance(coin_id, current):
    try:
        time.sleep(2)
        hist = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7", timeout=20).json()
        prices = [p[1] for p in hist['prices']]
        return min(prices), max(prices)
    except:
        return current*0.95, current*1.05

def format_crypto(coin_id, symbol, all_prices):
    try:
        current = float(all_prices[coin_id]['usd'])
        if current == 0:
            return f"{symbol}: Chargement..."
        sup, res = get_support_resistance(coin_id, current)
        if current < sup*1.02:
            conseil = "🔵 BUY (proche support)"
        elif current > res*0.98:
            conseil = "🔴 SELL (proche resistance)"
        else:
            conseil = "🟡 WAIT"
        return f"{symbol}: {current:.2f}$\n Sup: {sup:.2f} | Res: {res:.2f}\n {conseil}"
    except:
        return f"{symbol}: Erreur temp"

def analyse_forex(pair_from, pair_to, symbol):
    try:
        r2 = requests.get(f"https://open.er-api.com/v6/latest/{pair_from}", timeout=10).json()
        current = float(r2['rates'][pair_to])
        support = current * 0.99
        resistance = current * 1.01
        conseil = "🟡 WAIT"
        if current < support*1.005: conseil = "🔵 BUY"
        elif current > resistance*0.995: conseil = "🔴 SELL"
        return f"{symbol}: {current:.2f}\n Sup: {support:.2f} | Res: {resistance:.2f}\n {conseil}"
    except:
        return f"{symbol}: Erreur"

def bot_loop():
    time.sleep(10)
    try:
        all_p = get_all_prices()
        btc = format_crypto("bitcoin", "BTC/USD", all_p)
        eth = format_crypto("ethereum", "ETH/USD", all_p)
        sol = format_crypto("solana", "SOL/USD", all_p)
        usdjpy = analyse_forex("USD", "JPY", "USD/JPY")
        eurusd = analyse_forex("EUR", "USD", "EUR/USD")
        msg = f"📊 SIGNAL MULTI ODILON\n\n{btc}\n\n{eth}\n\n{sol}\n\n{usdjpy}\n\n{eurusd}\n\n⏰ {time.strftime('%H:%M')} - Prochain dans 2H"
        send_whatsapp(msg)
    except: pass

    while True:
        time.sleep(7200)
        try:
            all_p = get_all_prices()
            btc = format_crypto("bitcoin", "BTC/USD", all_p)
            eth = format_crypto("ethereum", "ETH/USD", all_p)
            sol = format_crypto("solana", "SOL/USD", all_p)
            usdjpy = analyse_forex("USD", "JPY", "USD/JPY")
            eurusd = analyse_forex("EUR", "USD", "EUR/USD")
            msg = f"📊 SIGNAL MULTI ODILON\n\n{btc}\n\n{eth}\n\n{sol}\n\n{usdjpy}\n\n{eurusd}\n\n⏰ {time.strftime('%H:%M')} - Prochain dans 2H"
            send_whatsapp(msg)
        except: pass

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))