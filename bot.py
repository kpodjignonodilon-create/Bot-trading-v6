import os, time, requests, urllib.parse, threading, math
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V17 PRO EMA+RSI - Live"

LOCK_FILE = "/tmp/last_send_v17.txt"

def can_send():
    try:
        if not os.path.exists(LOCK_FILE): return True
        with open(LOCK_FILE, 'r') as f:
            last=float(f.read().strip() or 0)
        if time.time() - last < 5400:
            print(f"Doublon bloqué")
            return False
        return True
    except: return True

def mark_sent():
    with open(LOCK_FILE, 'w') as f:
        f.write(str(time.time()))

def send_whatsapp(msg):
    if not can_send(): return False
    try:
        url=f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
        mark_sent()
        print("Envoyé")
        return True
    except: return False

def get_klines(symbol, interval="15m", limit=100):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}', timeout=10).json()
        closes=[float(c[4]) for c in r]
        return closes
    except:
        return []

def ema(values, period):
    if len(values) < period: return None
    k=2/(period+1)
    ema_val=sum(values[:period])/period
    for price in values[period:]:
        ema_val=price*k + ema_val*(1-k)
    return ema_val

def rsi(values, period=14):
    if len(values) < period+1: return 50
    gains, losses = 0, 0
    for i in range(1, period+1):
        diff=values[-i]-values[-i-1]
        if diff>=0: gains+=diff
        else: losses+=-diff
    if losses==0: return 70
    rs=gains/losses
    return 100 - (100/(1+rs))

def get_fx_rate(base,to):
    try:
        r=requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=10).json()
        return float(r['rates'][to])
    except: return 1.0

def analyze(symbol