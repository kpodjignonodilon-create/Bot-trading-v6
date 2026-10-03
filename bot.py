import requests, time, urllib.parse

PHONE = "22957142465"
APIKEY = "MET_TA_CLE_ICI"  # Ex: 1234567 que CallMeBot t'a donné

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

def send_whatsapp(msg):
    try:
        text = urllib.parse.quote(msg)
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={text}&apikey={APIKEY}"
        r = requests.get(url, timeout=15)
        print(f"WhatsApp envoyé: {r.text}")
    except Exception as e:
        print(e)

def get_signal(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=10).json()
        price = float(r['lastPrice'])
        change = float(r['priceChangePercent'])
        if change > 2.5:
            return f"🚀 {symbol} HAUSSIER +{change:.2f}% Prix: {price}"
        elif change < -2.5:
            return f"📉 {symbol} BAISSIER {change:.2f}% Prix: {price}"
        return None
    except:
        return None

send_whatsapp("✅ BOT V6 WHATSAPP LANCE - BTC/ETH/SOL/BNB")
print("BOT LANCE")

while True:
    for sym in SYMBOLS:
        sig = get_signal(sym)
        if sig:
            send_whatsapp(sig)
    time.sleep(60)