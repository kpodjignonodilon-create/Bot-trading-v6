import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V9 MULTI 2H - Live - New Key"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        print(requests.get(url, timeout=15).text)
    except Exception as e: print(e)

def analyse_crypto(coin_id, symbol):
    try:
        price_data = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd", timeout=15).json()
        current = float(price_data[coin_id]['usd'])
        try:
            hist = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7", timeout=15).json()
            prices = [p[1] for p in hist['prices']]
            support = min(prices)
            resistance = max(prices)
        except:
            support = current * 0.95
            resistance = current * 1.05
        if current < support * 1.02: conseil = "🔵 BUY (proche support)"
        elif current > resistance * 0.98: conseil = "🔴 SELL (proche resistance)"
        else: conseil = "🟡 WAIT"
        return f"{symbol}: {current:.2f}$\n Sup: {support:.2f} | Res: {resistance:.2f}\n {conseil}"
    except: return f"{symbol}: Erreur"

def analyse_forex(pair_from, pair_to, symbol):
    try:
        r2 = requests.get(f"https://open.er-api.com/v6/latest/{pair_from}", timeout=10).json()
        current = float(r2['rates'][pair_to])
        support = current * 0.99
        resistance = current * 1.01
        if current < support * 1.005: conseil = "🔵 BUY"
        elif current > resistance * 0.995: conseil = "🔴 SELL"
        else: conseil = "🟡 WAIT"
        return f"{symbol}: {current:.2f}\n Sup: {support:.2f} | Res: {resistance:.2f}\n {conseil}"
    except: return f"{symbol}: Erreur"

def bot_loop():
    send_whatsapp("🚀 BOT V9 MULTI LANCE - Nouvelle cle 3189307 - 2H")
    while True:
        try:
            btc = analyse_crypto("bitcoin", "BTC/USD")
            eth = analyse_crypto("ethereum", "ETH/USD")
            sol = analyse_crypto("solana", "SOL/USD")
            usdjpy = analyse_forex("USD", "JPY", "USD/JPY")
            eurusd = analyse_forex("EUR", "USD", "EUR/USD")
            msg = f"📊 SIGNAL MULTI ODILON\n\n{btc}\n\n{eth}\n\n{sol}\n\n{usdjpy}\n\n{eurusd}\n\n⏰ {time.strftime('%H:%M')} - Prochain dans 2H"
            send_whatsapp(msg)
        except: pass
        time.sleep(7200)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))