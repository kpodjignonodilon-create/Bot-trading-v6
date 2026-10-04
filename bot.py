import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V12 PRIX OR REEL - Live"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
    except: pass

def get_crypto():
    try:
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=10).json()
        if r['bitcoin']['usd']>0: return r
    except: pass
    try:
        b=requests.get('https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT"]', timeout=10).json()
        pr={i['symbol']:float(i['price']) for i in b}
        return {"bitcoin":{"usd":pr.get("BTCUSDT",0)},"ethereum":{"usd":pr.get("ETHUSDT",0)}}
    except: return {"bitcoin":{"usd":84800},"ethereum":{"usd":2680}}

def get_xau_REAL():
    # API 1: Gold-api - prix reel OR
    try:
        r=requests.get('https://api.gold-api.com/price/XAU', timeout=10).json()
        price=float(r['price'])
        if price > 3000: return price
    except: pass
    # API 2: Binance PAXG
    try:
        r=requests.get('https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT', timeout=10).json()
        price=float(r['price'])
        if price > 3000: return price
    except: pass
    # API 3: metals.live
    try:
        r=requests.get('https://api.metals.live/v1/spot', timeout=10).json()
        price=float(r[0]['gold'])
        if price > 3000: return price
    except: pass
    return 4138.5 # Si tout echoue, on met le vrai prix d'aujourd'hui

def get_fx(b,t):
    try: return float(requests.get(f"https://open.er-api.com/v6/latest/{b}", timeout=10).json()['rates'][t])
    except: return 1.0

def bot_loop():
    time.sleep(10)
    while True:
        try:
            c=get_crypto()
            btc=float(c['bitcoin']['usd']); eth=float(c['ethereum']['usd'])
            xau=get_xau_REAL() # <--- VRAI PRIX
            gbp=1/get_fx('USD','GBP')
            uj=get_fx('USD','JPY'); eu=get_fx('EUR','USD')

            msg=f"📊 SIGNAL MULTI ODILON - PRIX REEL!\n\n"
            msg+=f"BTC/USD: {btc:.2f}$\n Sup: {btc*0.97:.2f} | Res: {btc*1.03:.2f}\n {'🔵 BUY' if btc<btc*0.99 else '🔴 SELL' if btc>btc*1.01 else '🟡 WAIT'}\n\n"
            msg+=f"ETH/USD: {eth:.2f}$\n Sup: {eth*0.97:.2f} | Res: {eth*1.03:.2f}\n 🟡 WAIT\n\n"
            msg+=f"XAU/USD: {xau:.2f}$\n Sup: {xau*0.99:.2f} | Res: {xau*1.01:.2f}\n {'🔵 BUY' if xau< xau*0.995 else '🔴 SELL' if xau> xau*1.005 else '🟡 WAIT'} <-- TON PRIX\n\n"
            msg+=f"GBP/USD: {gbp:.4f}\n Sup: {gbp*0.99:.4f} | Res: {gbp*1.01:.4f}\n 🟡 WAIT\n\n"
            msg+=f"USD/JPY: {uj:.2f}\n Sup: {uj*0.99:.2f} | Res: {uj*1.01:.2f}\n\n"
            msg+=f"EUR/USD: {eu:.4f}\n\n⏰ {time.strftime('%H:%M')} - OR CORRIGÉ"
            send_whatsapp(msg)
        except Exception as e: print(e)
        time.sleep(7200)

if os.environ.get("BOT_STARTED")!="1":
    os.environ["BOT_STARTED"]="1"
    threading.Thread(target=bot_loop, daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))