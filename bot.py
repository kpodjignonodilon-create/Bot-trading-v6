import os, time, requests, urllib.parse, threading, datetime, random
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V20 FULL PRO - 6 symboles"

LOCK_FILE = "/tmp/last_send_v20.txt"

def can_send():
    try:
        if not os.path.exists(LOCK_FILE): return True
        with open(LOCK_FILE, 'r') as f:
            last=float(f.read().strip() or 0)
        if time.time() - last < 5400: return False
        return True
    except: return True

def mark_sent():
    with open(LOCK_FILE, 'w') as f: f.write(str(time.time()))

def send_whatsapp(msg):
    if not can_send(): return False
    try:
        url=f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=12)
        mark_sent()
        return True
    except: return False

def get_crypto(symbol):
    price=low=high=0; closes=[]
    try:
        r=requests.get(f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={symbol}", timeout=10).json()
        price=float(r['lastPrice']); low=float(r['lowPrice']); high=float(r['highPrice'])
    except: pass
    try:
        r2=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=15m&limit=100", timeout=10).json()
        closes=[float(c[4]) for c in r2]
    except: closes=[]
    if not closes and price>0:
        closes=[price*(1+random.uniform(-0.003,0.003)) for _ in range(100)]
        closes[-1]=price
    if low==0 and price>0:
        low=price*0.996; high=price*1.004
    return price, low, high, closes

def get_forex(base,to):
    price=0; closes=[]
    try:
        # prix actuel
        r=requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=10).json()
        price=float(r['rates'][to])
        # historique 100 jours pour EMA/RSI
        end=datetime.date.today()
        start=end - datetime.timedelta(days=120)
        url=f"https://api.frankfurter.app/{start}..{end}?from={base}&to={to}"
        rh=requests.get(url, timeout=10).json()
        if 'rates' in rh:
            closes=[v[to] for k,v in sorted(rh['rates'].items())][-100:]
        if not closes:
            closes=[price*(1+random.uniform(-0.002,0.002)) for _ in range(100)]
            closes[-1]=price
    except:
        closes=[price*(1+random.uniform(-0.002,0.002)) for _ in range(100)] if price else []
    low=min(closes[-24:]) if len(closes)>=24 else price*0.998
    high=max(closes[-24:]) if len(closes)>=24 else price*1.002
    return price, low, high, closes

def ema(values, period):
    if len(values) < period: return values[-1] if values else 0
    k=2/(period+1)
    e=sum(values[:period])/period
    for p in values[period:]: e=p*k + e*(1-k)
    return e

def rsi(values, period=14):
    if len(values) < period+1: return 50
    g=l=0
    for i in range(1, period+1):
        d=values[-i]-values[-i-1]
        if d>=0: g+=d
        else: l+=-d
    if l==0: return 68
    return 100 - (100/(1+g/l))

def get_signal(closes):
    if len(closes)<20: return "🟡 WAIT", 50, 0, "Calcul..."
    e9=ema(closes,9); e21=ema(closes,21); r=rsi(closes,14)
    if e9>e21:
        if 30<=r<=52: return "🔵 BUY", r, e9, f"Hausse RSI {r:.0f}"
        elif r>70: return "🔴 SELL", r, e9, f"Surachete {r:.0f}"
        else: return "🟡 WAIT", r, e9, f"Hausse RSI {r:.0f}"
    else:
        if 48<=r<=70: return "🔴 SELL", r, e9, f"Baisse RSI {r:.0f}"
        elif r<30: return "🔵 BUY", r, e9, f"Survendu {r:.0f}"
        else: return "🟡 WAIT", r, e9, f"Baisse RSI {r:.0f}"

def bot_loop():
    time.sleep(10)
    while True:
        try:
            btc_p, btc_l, btc_h, btc_c = get_crypto("BTCUSDT")
            eth_p, eth_l, eth_h, eth_c = get_crypto("ETHUSDT")
            xau_p, xau_l, xau_h, xau_c = get_crypto("PAXGUSDT")

            gbp_p, gbp_l, gbp_h, gbp_c = get_forex("GBP","USD")
            # pour GBP/USD on veut GBP vers USD, frankfurter est inverse donc on inverse
            # On refait simple via USD->GBP inverse
            gbp_p = 1/get_forex("USD","GBP")[0] if get_forex("USD","GBP")[0]!=0 else gbp_p
            # Pour simplifier on garde le get_forex USD->...
            usd_gbp_p, usd_gbp_l, usd_gbp_h, usd_gbp_c = get_forex("USD","GBP")
            gbp_p = 1/usd_gbp_p if usd_gbp_p else 1.32
            gbp_l = 1/usd_gbp_h if usd_gbp_h else gbp_p*0.998
            gbp_h = 1/usd_gbp_l if usd_gbp_l else gbp_p*1.002
            gbp_c = [1/x