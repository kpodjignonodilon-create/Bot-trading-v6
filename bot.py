import requests, time, threading, asyncio
from telegram import Bot
import datetime

TOKEN = "7866939003:AAEuN5N5F6J3N5mP7p7v4L4Z3p4Q4R4S4T4"
CHAT_ID = "7407505945"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

bot = Bot(token=TOKEN)

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
    except Exception as e:
        print(e)
        return None

async def loop():
    await bot.send_message(chat_id=CHAT_ID, text="✅ BOT V6 MULTI ACTIF - Surveillance BTC/ETH/SOL")
    while True:
        for sym in SYMBOLS:
            sig = get_signal(sym)
            if sig:
                await bot.send_message(chat_id=CHAT_ID, text=sig)
                print(sig)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(loop())