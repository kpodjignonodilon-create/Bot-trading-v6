import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V9.2 Anti-Blocage - Live"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
    except: pass

def get_all_prices():
    # TENTATIVE 1: CoinGecko
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd", timeout=10).json()
        if r.get('bitcoin',{}).get('usd',0) > 0:
            return r
    except: pass

    # TENTATIVE 2: Binance (si CoinGecko bloque)
    try:
        b = requests.get('https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT","SOLUSDT"]', timeout=10).json()
        prices = {item['symbol']: float(item['price']) for item in b}
        return {
            "bitcoin": {"usd": prices.get("BTCUSDT",0)},
            "ethereum": {"usd": prices.get("ETHUSDT",0)},
            "solana": {"usd": prices.get("SOLUSDT",0)}
        }
    except:
        return {"bitcoin":{"usd":84800},"ethereum":{"usd":2680},"solana":{"usd":119}}

def get_support_resistance(coin_id, current):
    try:
        time.sleep(1)
        hist = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7", timeout=10).json()
        prices = [p[1] for p in hist['prices']]
        return min(prices), max(prices)
    except:
        return current*0.97, current*1.03

def format_crypto(coin_id, symbol, all_prices):
    current = float(all_prices[coin_id]['usd'])
    sup, res = get_support_resistance(coin_id, current)
    if current < sup*1.02: conseil = "🔵 BUY"
    elif current > res*0.98: conseil = "🔴 SELL"
    else: conseil = "🟡 WAIT"
    return f"{symbol}: {current:.2f}$\n Sup: {sup:.2f} | Res: {res:.2f}\n {conseil}"

def analyse_forex(pair_from, pair_to, symbol):
    try:
        r2 = requests.get(f"https://open.er-api.com/v6/latest/{pair_from}", timeout=10).json()
        current = float(r2['rates'][pair_to])
        return f"{symbol}: {current:.2f}\n Sup: {current*0.99:.2f} | Res: {current*1.01:.2f}\n 🟡 WAIT"
    except: return f"{symbol}: 1.13 - WAIT"

def bot_loop():
    time.sleep(10)
    try:
        all_p = get_all_prices()
        msg = f"📊 SIGNAL MULTI ODILON\n\n{format_crypto('bitcoin','BTC/USD',all_p)}\n\n{format_crypto('ethereum','ETH/USD',all_p)}\n\n{format_crypto('solana','SOL/USD',all_p)}\n\n{analyse_forex('USD','JPY','USD/JPY')}\n\n{analyse_forex('EUR','USD','EUR/USD')}\n\n⏰ {time.strftime('%H:%M')} - Prochain dans 2H"
        send_whatsapp(msg)
    except: pass
    while True:
        time.sleep(7200)
        try:
            all_p = get_all_prices()
            msg = f"📊 SIGNAL MULTI ODILON\n\n{format_crypto('bitcoin','BTC/USD',all_p)}\n\n{format_crypto('ethereum','ETH/USD',all_p)}\n\n{format_crypto('solana','SOL/USD',all_p)}\n\n{analyse_forex('USD','JPY','USD/JPY')}\n\n{analyse_forex('EUR','USD','EUR/USD')}\n\n⏰ {time.strftime('%H:%M')} - Prochain dans 2H"
            send_whatsapp(msg)
        except: pass

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))