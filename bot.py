import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V15 OPPORTUNISTE - Live"

LOCK_FILE = "/tmp/last_send.txt"

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
        requests.get(url, timeout=15)
        mark_sent()
        return True
    except: return False

def get_crypto():
    try:
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=10).json()
        if r['bitcoin']['usd']>0: return r
    except: pass
    return {"bitcoin":{"usd":84800},"ethereum":{"usd":2680}}

def get_xau():
    try:
        r=requests.get('https://api.gold-api.com/price/XAU', timeout=10).json()
        p=float(r['price'])
        if p>3000: return p
    except: pass
    return 4141.80

def get_fx(b,t):
    try: return float(requests.get(f"https://open.er-api.com/v6/latest/{b}", timeout=10).json()['rates'][t])
    except: return 1.0

def bot_loop():
    time.sleep(15)
    while True:
        try:
            c=get_crypto()
            btc=float(c['bitcoin']['usd']); eth=float(c['ethereum']['usd'])
            xau=get_xau()
            gbp=1/get_fx('USD','GBP'); uj=get_fx('USD','JPY'); eu=get_fx('EUR','USD')

            # BANDES SERREES POUR OPPORTUNITE
            btc_sup, btc_res = btc*0.992, btc*1.008  # 0.8%
            eth_sup, eth_res = eth*0.992, eth*1.008
            xau_sup, xau_res = xau*0.997, xau*1.003  # 0.3% = 12$ pour l'OR
            gbp_sup, gbp_res = gbp*0.998, gbp*1.002
            uj_sup, uj_res = uj*0.998, uj*1.002
            eu_sup, eu_res = eu*0.998, eu*1.002

            signals=[]
            def check(sym,cur,sup,res,dec=2):
                if cur <= sup:
                    signals.append(f"{sym}: {cur:.{dec}f}\n Sup: {sup:.{dec}f} | Res: {res:.{dec}f}\n 🔵 BUY OPPORTUNITÉ")
                elif cur >= res:
                    signals.append(f"{sym}: {cur:.{dec}f}\n Sup: {sup:.{dec}f} | Res: {res:.{dec}f}\n 🔴 SELL OPPORTUNITÉ")

            check("BTC/USD",btc,btc_sup,btc_res)
            check("ETH/USD",eth,eth_sup,eth_res)
            check("XAU/USD",xau,xau_sup,xau_res)
            check("GBP/USD",gbp,gbp_sup,gbp_res,4)
            check("USD/JPY",uj,uj_sup,uj_res)
            check("EUR/USD",eu,eu_sup,eu_res,4)

            if signals: # ENVOIE UNIQUEMENT SI OPPORTUNITE
                msg="📊 SIGNAL MULTI ODILON - MOMENT OPPORTUN! 🚨\n\n" + "\n\n".join(signals) + f"\n\n⏰ {time.strftime('%H:%M')}"
                send_whatsapp(msg)
            else:
                print(f"{time.strftime('%H:%M')} - Pas d'opportunité, silence")

        except Exception as e: print(e)
        time.sleep(3600) # verifie toutes les 1h

if os.environ.get("BOT_STARTED")!="1":
    os.environ["BOT_STARTED"]="1"
    threading.Thread(target=bot_loop, daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))