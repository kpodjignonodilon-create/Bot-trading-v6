import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot V18 PRO EMA+RSI - Live"

LOCK_FILE = "/tmp/last_send_v18.txt"

def can_send():
    try:
        if not os.path.exists(LOCK_FILE):
            return True
        with open(LOCK_FILE, 'r') as f:
            last = float(f.read().strip() or 0)
        if time.time() - last < 5400:
            return False
        return True
    except:
        return True

def mark_sent():
    with open(LOCK_FILE, 'w') as f:
        f.write(str(time.time()))

def send_whatsapp(msg):
    if not can_send():
        return False
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
        mark_sent()
        return True
    except:
        return False

def get_klines(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=100"
        r = requests.get(url, timeout=10).json()
        closes = [float(c[4]) for c in r]
        return closes
    except:
        return []

def ema(values, period):
    if len(values) < period:
        return None
    k = 2 / (period + 1)
    ema_val = sum(values[:period]) / period
    for price in values[period:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def rsi(values, period=14):
    if len(values) < period + 1:
        return 50
    gains = 0
    losses = 0
    for i in range(1, period + 1):
        diff = values[-i] - values[-i-1]
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    if losses == 0:
        return 70
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def get_fx(base, to):
    try:
        r = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=10).json()
        return float(r['rates'][to])
    except:
        return 1.0

def analyze_signal(closes):
    if len(closes) < 30:
        return 0, 0, "WAIT", "Calcul..."
    e9 = ema(closes, 9)
    e21 = ema(closes, 21)
    r = rsi(closes, 14)
    if e9 is None or e21 is None:
        return 0, 0, "WAIT", "Calcul..."
    if e9 > e21:
        if 30 <= r <= 50:
            return e9, r, "BUY", f"Hausse + RSI {r:.0f}"
        elif r > 70:
            return e9, r, "SELL", f"Surachete {r:.0f}"
        else:
            return e9, r, "WAIT", f"Hausse RSI {r:.0f}"
    else:
        if 50 <= r <= 70:
            return e9, r, "SELL", f"Baisse + RSI {r:.0f}"
        elif r < 30:
            return e9, r, "BUY", f"Survendu {r:.0f}"
        else:
            return e9, r, "WAIT", f"Baisse RSI {r:.0f}"

def bot_loop():
    time.sleep(10)
    while True:
        try:
            btc_c = get_klines("BTCUSDT")
            eth_c = get_klines("ETHUSDT")
            xau_c = get_klines("PAXGUSDT")

            btc_price = btc_c[-1] if btc_c else 84800
            eth_price = eth_c[-1] if eth_c else 2680
            xau_price = xau_c[-1] if xau_c else 4141

            b_e9, b_r, b_sig, b_why = analyze_signal(btc_c)
            e_e9, e_r, e_sig, e_why = analyze_signal(eth_c)
            x_e9, x_r, x_sig, x_why = analyze_signal(xau_c)

            gbp = 1 / get_fx('USD', 'GBP')
            uj = get_fx('USD', 'JPY')
            eu = get_fx('EUR', 'USD')

            msg = "📊 SIGNAL PRO V18 - EMA+RSI\n\n"
            msg += f"BTC: {btc_price:.2f}$ EMA9:{b_e9:.2f} RSI:{b_r:.0f}\n {b_sig} - {b_why}\n\n"
            msg += f"ETH: {eth_price:.2f}$ EMA9:{e_e9:.2f} RSI:{e_r:.0f}\n {e_sig} - {e_why}\n\n"
            msg += f"XAU: {xau_price:.2f}$ EMA9:{x_e9:.2f} RSI:{x_r:.0f}\n {x_sig} - {x_why}\n\n"
            msg += f"GBP:{gbp:.4f} JPY:{uj:.2f} EUR:{eu:.4f}\n"
            msg += f"⏰ {time.strftime('%H:%M')}"

            send_whatsapp(msg)
        except Exception as e:
            print(e)
        time.sleep(7200)

if os.environ.get("BOT_STARTED")!= "1":
    os.environ["BOT_STARTED"] = "1"
    threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))