import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V13 FINAL PROPRE - Live"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
        print("Envoyé")
    except Exception as e:
        print(e)

def get_crypto():
    try:
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=10).json()
        if r.get('bitcoin',{}).get('usd',0)>0: return r
    except: pass
    try:
        b=requests.get('https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT"]', timeout=10).json()
        pr={i['symbol']:float(i['price']) for i in b}
        return {"bitcoin":{"usd":pr.get("BTCUSDT",84800)},"ethereum":{"usd":pr.get("ETHUSDT",2680)}}
    except:
        return {"bitcoin":{"usd":84800},"ethereum":{"usd":2680}}

def get_xau_REAL():
    try:
        r=requests.get('https://api.gold-api.com/price/XAU', timeout=10).json()
        p=float(r['price'])
        if p>3000: return p
    except: pass
    try:
        r=requests.get('https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT', timeout=10).json()
        p=float(r['price'])
        if p>3000: return p
    except: pass
    return 4140.0

def get_fx(base,to):
    try:
        r=requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=10).json()
        return float(r['rates'][to])
    except: return 1.0

def signal(cur, sup, res):
    if cur <= sup: return "🔵 BUY"
    if cur >= res: return "🔴 SELL"
    return "🟡 WAIT"

def bot_loop():
    time.sleep(10)
    while True:
        try:
            c=get_crypto()
            btc=float(c['bitcoin']['usd'])
            eth=float(c['ethereum']['usd'])
            xau=get_xau_REAL()
            gbp=1/get_fx('USD','GBP')
            uj=get_fx('USD','JPY')
            eu=get_fx('EUR','USD')

            # Calcul Support / Resistance
            btc_sup, btc_res = btc*0.97, btc*1.03
            eth_sup, eth_res = eth*0.97, eth*1.03
            xau_sup, xau_res = xau*0.99, xau*1.01
            gbp_sup, gbp_res = gbp*0.99, gbp*1.01
            uj_sup, uj_res = uj*0.99, uj*1.01
            eu_sup, eu_res = eu*0.99, eu*1.01

            msg=f"📊 SIGNAL MULTI ODILON\n\n"
            msg+=f"BTC/USD: {btc:.2f}$\n Sup: {btc_sup:.2f} | Res: {btc_res:.2f}\n {signal(btc,btc_sup,btc_res)}\n\n"
            msg+=f"ETH/USD: {eth:.2f}$\n Sup: {eth_sup:.2f} | Res: {eth_res:.2f}\n {signal(eth,eth_sup,eth_res)}\n\n"
            msg+=f"XAU/USD: {xau:.2f}$\n Sup: {xau_sup:.2f} | Res: {xau_res:.2f}\n {signal(xau,xau_sup,xau_res)}\n\n"
            msg+=f"GBP/USD: {gbp:.4f}\n Sup: {gbp_sup:.4f} | Res: {gbp_res:.4f}\n {signal(gbp,gbp_sup,gbp_res)}\n\n"
            msg+=f"USD/JPY: {uj:.2f}\n Sup: {uj_sup:.2f} | Res: {uj_res:.2f}\n {signal(uj,uj_sup,uj_res)}\n\n"
            msg+=f"EUR/USD: {eu:.4f}\n Sup: {eu_sup:.4f} | Res: {eu_res:.4f}\n {signal(eu,eu_sup,eu_res)}\n\n"
            msg+=f"⏰ {time.strftime('%H:%M')} - Prochain dans 2H"

            send_whatsapp(msg)

        except Exception as e:
            print(f"Erreur: {e}")

        time.sleep(7200)

if os.environ.get("BOT_STARTED")!="1":
    os.environ["BOT_STARTED"]="1"
    threading.Thread(target=bot_loop, daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))