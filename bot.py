import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V16 FINAL PROPRE - Live"

LOCK_FILE = "/tmp/last_send_v16.txt"

def can_send():
    try:
        if not os.path.exists(LOCK_FILE): return True
        with open(LOCK_FILE, 'r') as f:
            last=float(f.read().strip() or 0)
        if time.time() - last < 5400: # 90 min bloque doublon
            print(f"Doublon bloqué, dernier il y a {(time.time()-last)/60:.0f}min")
            return False
        return True
    except: return True

def mark_sent():
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(time.time()))
    except: pass

def send_whatsapp(msg):
    if not can_send(): return False
    try:
        url=f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
        mark_sent()
        print("Envoyé")
        return True
    except Exception as e:
        print(e)
        return False

def get_binance_data(symbol):
    # Retourne prix actuel, plus bas 24h (support), plus haut 24h (resistance)
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}', timeout=10).json()
        cur=float(r['lastPrice'])
        low=float(r['lowPrice'])
        high=float(r['highPrice'])
        return cur, low, high
    except:
        return None, None, None

def get_xau_real():
    # XAU via Gold-API + Binance PAXG pour niveaux
    price=4141.0
    low, high = None, None
    try:
        r=requests.get('https://api.gold-api.com/price/XAU', timeout=10).json()
        price=float(r['price'])
    except: pass

    try:
        b=requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=PAXGUSDT', timeout=10).json()
        low=float(b['lowPrice'])
        high=float(b['highPrice'])
        if price<3000: price=float(b['lastPrice'])
    except:
        low=price*0.995
        high=price*1.005

    return price, low, high

def get_fx_rate(base,to):
    try:
        r=requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=10).json()
        return float(r['rates'][to])
    except: return 1.0

def get_signal(cur,sup,res):
    # Logique pro: proche du support = BUY, proche resistance = SELL
    if cur <= sup*1.001: return "🔵 BUY"
    if cur >= res*0.999: return "🔴 SELL"
    return "🟡 WAIT"

def bot_loop():
    time.sleep(10)
    while True:
        try:
            # 1. BTC
            btc_cur, btc_low, btc_high = get_binance_data("BTCUSDT")
            if not btc_cur: btc_cur, btc_low, btc_high = 84800, 83500, 86200

            # 2. ETH
            eth_cur, eth_low, eth_high = get_binance_data("ETHUSDT")
            if not eth_cur: eth_cur, eth_low, eth_high = 2680, 2620, 2740

            # 3. XAU - VRAI PRIX
            xau_cur, xau_low, xau_high = get_xau_real()

            # 4. FOREX
            gbp=1/get_fx_rate('USD','GBP')
            uj=get_fx_rate('USD','JPY')
            eu=get_fx_rate('EUR','USD')

            msg=f"📊 SIGNAL MULTI ODILON\n\n"
            msg+=f"BTC/USD: {btc_cur:.2f}$\n Sup: {btc_low:.2f} | Res: {btc_high:.2f}\n {get_signal(btc_cur,btc_low,btc_high)}\n\n"
            msg+=f"ETH/USD: {eth_cur:.2f}$\n Sup: {eth_low:.2f} | Res: {eth_high:.2f}\n {get_signal(eth_cur,eth_low,eth_high)}\n\n"
            msg+=f"XAU/USD: {xau_cur:.2f}$\n Sup: {xau_low:.2f} | Res: {xau_high:.2f}\n {get_signal(xau_cur,xau_low,xau_high)}\n\n"
            msg+=f"GBP/USD: {gbp:.4f}\n Sup: {gbp*0.995:.4f} | Res: {gbp*1.005:.4f}\n {get_signal(gbp,gbp*0.995,gbp*1.005)}\n\n"
            msg+=f"USD/JPY: {uj:.2f}\n Sup: {uj*0.995:.2f} | Res: {uj*1.005:.2f}\n {get_signal(uj,uj*0.995,uj*1.005)}\n\n"
            msg+=f"EUR/USD: {eu:.4f}\n Sup: {eu*0.995:.4f} | Res: {eu*1.005:.4f}\n {get_signal(eu,eu*0.995,eu*1.005)}\n\n"
            msg+=f"⏰ {time.strftime('%H:%M')}"

            send_whatsapp(msg)

        except Exception as e:
            print(f"Erreur: {e}")

        time.sleep(7200) # 2h

if os.environ.get("BOT_STARTED")!="1":
    os.environ["BOT_STARTED"]="1"
    threading.Thread(target=bot_loop, daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))