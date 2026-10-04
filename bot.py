import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V10 OR+GBP - Live"

last_send = [0]
lock = threading.Lock()

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
    except: pass

def get_crypto():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=10).json()
        if r.get('bitcoin',{}).get('usd',0) > 0: return r
    except: pass
    try:
        b = requests.get('https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT"]', timeout=10).json()
        pr = {i['symbol']: float(i['price']) for i in b}
        return {"bitcoin":{"usd":pr.get("BTCUSDT",0)},"ethereum":{"usd":pr.get("ETHUSDT",0)}}
    except:
        return {"bitcoin":{"usd":84800},"ethereum":{"usd":2680}}

def get_xau():
    try:
        # PAXG = Gold sur Binance
        r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT', timeout=10).json()
        return float(r['price'])
    except: return 2650.0

def get_fx(base, to):
    try:
        r = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=10).json()
        return float(r['rates'][to])
    except: return 1.0

def sup_res_fallback(cur):
    return cur*0.97, cur*1.03

def fmt_price(sym, cur, sup, res):
    cons = "🔵 BUY" if cur < sup*1.02 else "🔴 SELL" if cur > res*0.98 else "🟡 WAIT"
    return f"{sym}: {cur:.2f}$\n Sup: {sup:.2f} | Res: {res:.2f}\n {cons}"

def bot_loop():
    time.sleep(10)
    while True:
        now = time.time()
        if now - last_send[0] < 6600:
            time.sleep(60); continue
        with lock:
            last_send[0]=now
            try:
                crypto = get_crypto()
                btc = float(crypto['bitcoin']['usd'])
                eth = float(crypto['ethereum']['usd'])
                xau = get_xau()
                gbp = get_fx('GBP','USD') # GBP/USD direct
                # Si GBP/USD inverse, on prend USD->GBP et inverse
                if gbp < 0.5:
                    gbp = 1/get_fx('USD','GBP')
                uj = get_fx('USD','JPY')
                eu = get_fx('EUR','USD')

                # Support/Resistance simple 3% pour OR et Forex
                msg = f"📊 SIGNAL MULTI ODILON\n\n"
                msg += fmt_price("BTC/USD", btc, btc*0.97, btc*1.03)+"\n\n"
                msg += fmt_price("ETH/USD", eth, eth*0.97, eth*1.03)+"\n\n"
                msg += fmt_price("XAU/USD", xau, xau*0.99, xau*1.01)+"\n\n"
                msg += f"GBP/USD: {gbp:.4f}\n Sup: {gbp*0.99:.4f} | Res: {gbp*1.01:.4f}\n {'🔵 BUY' if gbp<1.26 else '🔴 SELL' if gbp>1.34 else '🟡 WAIT'}\n\n"
                msg += f"USD/JPY: {uj:.2f}\n Sup: {uj*0.99:.2f} | Res: {uj*1.01:.2f}\n 🟡 WAIT\n\n"
                msg += f"EUR/USD: {eu:.4f}\n Sup: {eu*0.99:.4f} | Res: {eu*1.01:.4f}\n 🟡 WAIT\n\n"
                msg += f"⏰ {time.strftime('%H:%M')} - Prochain dans 2H"
                send_whatsapp(msg)
            except: pass
        time.sleep(7200)

if os.environ.get("BOT_STARTED")!= "1":
    os.environ["BOT_STARTED"]="1"
    threading.Thread(target=bot_loop, daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))