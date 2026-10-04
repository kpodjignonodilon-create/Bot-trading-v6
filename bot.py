import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V11 FILTRE BUY/SELL - Live"

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
        if r['bitcoin']['usd']>0: return r
    except: pass
    try:
        b = requests.get('https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT"]', timeout=10).json()
        pr={i['symbol']:float(i['price']) for i in b}
        return {"bitcoin":{"usd":pr.get("BTCUSDT",0)},"ethereum":{"usd":pr.get("ETHUSDT",0)}}
    except: return {"bitcoin":{"usd":84800},"ethereum":{"usd":2680}}

def get_xau():
    try:
        return float(requests.get('https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT', timeout=10).json()['price'])
    except: return 2650.0

def get_fx(b,t):
    try: return float(requests.get(f"https://open.er-api.com/v6/latest/{b}", timeout=10).json()['rates'][t])
    except: return 1.0

def make_line(sym, cur, sup, res, decimals=2):
    if cur < sup*1.02: signal="🔵 BUY"
    elif cur > res*0.98: signal="🔴 SELL"
    else: signal="🟡 WAIT"
    f = f"{cur:.{decimals}f}"
    s = f"{sup:.{decimals}f}"
    r = f"{res:.{decimals}f}"
    return f"{sym}: {f}$\n Sup: {s} | Res: {r}\n {signal}", signal

def bot_loop():
    time.sleep(10)
    while True:
        with lock:
            try:
                c=get_crypto()
                btc=float(c['bitcoin']['usd']); eth=float(c['ethereum']['usd'])
                xau=get_xau()
                gbp=get_fx('USD','GBP'); gbp=1/gbp if gbp>0 else 1.32
                uj=get_fx('USD','JPY'); eu=get_fx('EUR','USD')

                lines=[]
                l,s = make_line("BTC/USD", btc, btc*0.97, btc*1.03); lines.append((l,s))
                l,s = make_line("ETH/USD", eth, eth*0.97, eth*1.03); lines.append((l,s))
                l,s = make_line("XAU/USD", xau, xau*0.99, xau*1.01); lines.append((l,s))

                gbp_sup=gbp*0.99; gbp_res=gbp*1.01
                gsig="🔵 BUY" if gbp<1.26 else "🔴 SELL" if gbp>1.34 else "🟡 WAIT"
                lines.append((f"GBP/USD: {gbp:.4f}\n Sup: {gbp_sup:.4f} | Res: {gbp_res:.4f}\n {gsig}", gsig))

                lines.append((f"USD/JPY: {uj:.2f}\n Sup: {uj*0.99:.2f} | Res: {uj*1.01:.2f}\n 🟡 WAIT", "🟡 WAIT"))
                lines.append((f"EUR/USD: {eu:.4f}\n Sup: {eu*0.99:.4f} | Res: {eu*1.01:.4f}\n 🟡 WAIT", "🟡 WAIT"))

                # FILTRE: est-ce qu'il y a au moins 1 BUY ou SELL?
                has_signal = any("BUY" in sig or "SELL" in sig for _,sig in lines)

                if has_signal:
                    msg="📊 SIGNAL MULTI ODILON - OPPORTUNITÉ!\n\n" + "\n\n".join([l for l,_ in lines]) + f"\n\n⏰ {time.strftime('%H:%M')}"
                    send_whatsapp(msg)
                    last_send[0]=time.time()
                else:
                    print(f"{time.strftime('%H:%M')} - Tout en WAIT, pas d'envoi")

            except Exception as e: print(e)
        time.sleep(7200) # verifie toutes les 2h

if os.environ.get("BOT_STARTED")!="1":
    os.environ["BOT_STARTED"]="1"
    threading.Thread(target=bot_loop, daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))