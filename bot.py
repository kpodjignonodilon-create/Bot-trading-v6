import requests, time

# TON NUMERO WHATSAPP
NUMERO = "+229XXXXXXXX"  # Mets ton numéro avec +229

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def get_signal(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=10).json()
        price = float(r['lastPrice'])
        change = float(r['priceChangePercent'])
        if change > 2.5:
            return f"🚀 {symbol} HAUSSIER +{change:.2f}% | Prix: {price}"
        elif change < -2.5:
            return f"📉 {symbol} BAISSIER {change:.2f}% | Prix: {price}"
        else:
            return None
    except:
        return None

print("✅ BOT V6 WHATSAPP LANCE")
while True:
    for sym in SYMBOLS:
        sig = get_signal(sym)
        if sig:
            print(sig) # Ici on affichera, et Render enverra sur WhatsApp via API
    time.sleep(60)