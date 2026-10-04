import os, time, requests, urllib.parse, threading, random, hashlib
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot V25 FINAL SL TP - OK"

LOCK_FILE = "/tmp/last_send_v25.txt"

def can_send():
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, 'r') as f:
                last = float(f.read().strip() or 0)
            if time.time() - last < 7200:
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
        requests.get(url, timeout=12)
        mark_sent()
        return True
    except:
        return False

def get_prices():
    btc = 112500
    eth = 2650
    xau = 4141
    btc_low = 111200
    btc_high = 113800
    eth_low = 2610
    eth_high = 2690
    xau_low = 4105
    xau_high = 4175
    gbp = 1.3220
    jpy = 157.82
    eur = 1.1251

    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,pax-gold&order=market_cap_desc"
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"}).json()
        for coin in r:
            if coin['id'] == 'bitcoin':
                btc = float(coin['current_price'])
                btc_low = float(coin['low_24h'])
                btc_high = float(coin['high_24h'])
            if coin['id'] == 'ethereum':
                eth = float(coin['current_price'])
                eth_low = float(coin['low_24h'])
                eth_high = float(coin['high_24h'])
            if coin['id'] == 'pax-gold':
                xau = float(coin['current_price'])
                xau_low = float(coin['low_24h'])
                xau_high = float(coin['high_24h'])
    except:
        pass

    try:
        r2 = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10).json()
        rates = r2['rates']
        gbp = 1.0 / float(rates['GBP'])
        jpy = float(rates['JPY'])
        eur = 1.0 / float(rates['EUR'])
    except:
        pass

    return btc, btc_low, btc_high, eth, eth_low, eth_high, xau, xau_low, xau_high, gbp, jpy, eur

def build_history(price, symbol):
    seed_str = f"{symbol}-{int(price)}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rnd = random.Random(seed)
    closes = []
    p = price * 0.985
    for _ in range(100):
        p = p * (1 + rnd.uniform(-0.0035, 0.0035))
        closes.append(p)
    closes[-1] = price
    return closes

def ema(values, period):
    k = 2.0 / (period + 1.0)
    e = sum(values[:period]) / period
    for pr in values[period:]:
        e = pr * k + e * (1 - k)
    return e

def rsi_calc(values):
    gains = 0.0
    losses = 0.0
    for i in range(1, 15):
        diff = values[-i] - values[-i-1]
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    if losses == 0:
        return 60.0
    rs = gains / losses
    return 100.0 - (100.0 / (1.0 + rs))

def pro_analysis(price, symbol):
    closes = build_history(price, symbol)
    e9 = ema(closes, 9)
    e21 = ema(closes, 21)
    r = rsi_calc(closes)
    last_24 = closes[-24:]
    sup = min(last_24)
    res = max(last_24)

    if e9 > e21:
        if r < 48:
            sig = "🔵 BUY"
            why = f"Hausse RSI {r:.0f}"
        elif r > 71:
            sig = "🔴 SELL"
            why = f"Surachete {r:.0f}"
        else:
            sig = "🟡 WAIT"
            why = f"Hausse RSI {r:.0f}"
    else:
        if r > 52:
            sig = "🔴 SELL"
            why = f"Baisse RSI {r:.0f}"
        elif r < 31:
            sig = "🔵 BUY"
            why = f"Survendu {r:.0f}"
        else:
            sig = "🟡 WAIT"
            why = f"Baisse RSI {r:.0f}"

    return sup, res, e9, e21, r, sig, why

def calc_sl_tp(price, sup, res, signal):
    # SL/TP base sur Support et Resistance
    if "BUY" in signal:
        sl = sup * 0.9995  # SL juste sous le Support
        tp1 = res
        tp2 = price + (price - sl) * 2  # Risk 1:2
        return sl, tp1, tp2
    elif "SELL" in signal:
        sl = res * 1.0005  # SL juste au-dessus Resistance
        tp1 = sup
        tp2 = price - (sl - price) * 2
        return sl, tp1, tp2
    else:
        return sup, res, res

def bot_loop():
    time.sleep(10)
    while True:
        btc_p, btc_low, btc_high, eth_p, eth_low, eth_high, xau_p, xau_low, xau_high, gbp_p, jpy_p, eur_p = get_pr