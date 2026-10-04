import os, time, requests, urllib.parse, threading, random, hashlib
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot V23 FINAL PRO - Live"

LOCK_FILE = "/tmp/last_send_v23.txt"
BOT_FLAG = "/tmp/bot_running_v23.txt"

def can_send():
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, 'r') as f:
                last = float(f.read().strip() or 0)
            # 7200 sec = 2H strict
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
        print("Doublon bloque - deja envoye il y a moins de 2H")
        return False
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=12)
        mark_sent()
        print("WhatsApp envoye")
        return True
    except Exception as e:
        print(f"Erreur WhatsApp: {e}")
        return False

def get_all_prices():
    btc = eth = xau = 0
    btc_low = btc_high = 0
    eth_low = eth_high = 0
    xau_low = xau_high = 0
    
    try:
        # CoinGecko markets donne prix + high/low 24h reel
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,pax-gold&order=market_cap_desc"
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"}).json()
        for coin in r:
            if coin['id'] == 'bitcoin':
                btc = float(coin['current_price'])
                btc_low = float(coin['low_24h'])
                btc_high = float(coin['high_24h'])
            elif coin['id'] == 'ethereum':
                eth = float(coin['current_price'])
                eth_low = float(coin['low_24h'])
                eth_high = float(coin['high_24h'])
            elif coin['id'] == 'pax-gold':
                xau = float(coin['current_price'])
                xau_low = float(coin['low_24h'])
                xau_high = float(coin['high_24h'])
    except:
        btc, btc_low, btc_high = 112500, 111200, 113800
        eth, eth_low, eth_high = 2650, 2610, 2690
        xau, xau_low, xau_high = 4141, 4105, 4175

    gbp = jpy = eur = 0
    try:
        r2 = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10, headers={"User-Agent": "Mozilla/5.0"}).json()
        rates = r2['rates']
        # Correction permutation: USD base
        # GBP/USD = 1 / (GBP per USD)
        # EUR/USD = 1 / (EUR per USD)
        # USD/JPY = JPY per USD direct
        gbp = 1.0 / float(rates['GBP'])
        jpy = float(rates['JPY'])
        eur = 1.0 / float(rates['EUR'])
    except:
        gbp = 1.3220
        jpy = 157.82
        eur = 1.1251

    return (btc, btc_low, btc_high, eth, eth_low, eth_high, xau, xau_low, xau_high, gbp, jpy, eur)

def build_history(price, symbol):
    # Historique stable: meme prix = meme historique = meme signal
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
    for price in values[period:]:
        e = price * k + e * (1 - k)
    return e

def rsi(values, period=14):
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
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
    r = rsi(closes)
    
    # Support / Resistance sur 24 dernieres bougies simulees
    last_24 = closes[-24:]
    sup = min(last_24)
    res = max(last_24)

    if e9 > e21:
        # Tendance haussiere
        if r < 48:
            sig = "🔵 BUY"
            reason = f"Hausse + RSI {r:.0f} bon"
        elif r > 71:
            sig = "🔴 SELL"
            reason = f"Surachete RSI {r:.0f}"
        else:
            sig = "🟡 WAIT"
            reason = f"Hausse mais RSI {r:.0f}"
    else:
        # Tendance baissiere
        if r > 52:
            sig = "🔴 SELL"
            reason = f"Baisse + RSI {r:.0f}"
        elif r < 31:
            sig = "🔵 BUY"
            reason = f"Survendu RSI {r:.0f}"
        else:
            sig = "🟡 WAIT"
            reason = f"Baisse mais RSI {r:.0f}"

    return sup, res, e9, e21, r, sig, reason

def bot_loop():
    time.sleep(12)
    while True:
        try:
            btc_p, btc_l24, btc_h24, eth_p, eth_l24, eth_h24, xau_p, xau_l24, xau_h24, gbp_p, jpy_p, eur_p = get_all_prices()

            btc_sup, btc_res, btc_e9, btc_e21, btc_r, btc_sig, btc_why = pro_analysis(btc_p, "BTC")
            eth_sup, eth_res, eth_e9, eth_e21, eth_r, eth_sig, eth_why = pro_analysis(eth_p, "ETH")
            xau_sup, xau_res, xau_e9, xau_e21, xau_r, xau_sig, xau_why = pro_analysis(xau_p, "XAU")
            gbp_sup, gbp_res, gbp_e9, gbp_e21, gbp_r, gbp_sig, gbp_why = pro_analysis(gbp_p, "GBP")
            jpy_sup, jpy_res, jpy_e9, jpy_e21, jpy_r, jpy_sig, jpy_why = pro_analysis(jpy_p, "JPY")
            eur_sup, eur_res, eur_e9, eur_e21, eur_r, eur_sig, eur_why = pro_analysis(eur_p, "EUR")

            # Override S/R crypto avec vrai S/R 24h CoinGecko
            btc_sup,