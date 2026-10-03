import os, time, requests, urllib.parse, threading
from flask import Flask

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "9300299")

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot V8 LIGHT Odilon - Live"

def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
        requests.get(url, timeout=15)
        print("Envoyé")
    except Exception as e:
        print(e)

def get_btc():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10).json()
        return float(r['price'])
    except: return 0

def bot_loop():
    send_whatsapp("🚀 BOT V8 LIGHT LANCE - BTC + USDJPY toutes les 5 min")
    while True:
        try:
            btc = get_btc()
            # USDJPY on prend un prix fixe simulé pour test, après on remettra vrai analyse
            msg = f"📊 SIGNAL ODILON V8 LIGHT\n\nBTC: {btc:.2f} $\nUSD/JPY: Analyse en cours...\nHeure: {time.strftime('%H:%M')}"
            send_whatsapp(msg)
        except Exception as e:
            print(e)
        time.sleep(300)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)