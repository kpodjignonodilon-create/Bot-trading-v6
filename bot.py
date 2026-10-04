import os
import time
import threading
import hashlib
import random
from dataclasses import dataclass
from typing import List
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "V30 FORMULAIRE ODILON - OK - /test"

@app.route("/test")
def test_route():
    threading.Thread(target=send_once_force, daemon=True).start()
    return "Test lance! Formulaire Odilon 6 symboles"

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")
SEND_INTERVAL_SECONDS = int(os.getenv("SEND_INTERVAL_SECONDS", "7200"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "12"))

EMA_FAST = 9
EMA_SIGNAL = 21
EMA_TREND = 50
RSI_PERIOD = 14
HISTORY_LENGTH = 50

@dataclass
class MarketData:
    symbol: str
    price: float
    low_24h: float
    high_24h: float
    closes: List[float]

@dataclass
class Analysis:
    symbol: str
    price: float
    support: float
    resistance: float
    ema9: float
    ema21: float
    ema50: float
    signal: str

LOCK_FILE = "/tmp/last_send_v30.txt"

def can_send(force=False) -> bool:
    if force:
        return True
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                last = float(f.read().strip() or 0)
            return (time.time() - last) >= SEND_INTERVAL_SECONDS
        return True
    except:
        return True

def mark_sent() -> None:
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        f.write(str(time.time()))

def send_whatsapp(message: str, force=False) -> bool:
    if not PHONE or not APIKEY:
        print("PHONE/APIKEY manquant")
        return False
    if not can_send(force):
        print("Rate limit 2h actif")
        return False
    try:
        params = {"phone": PHONE, "text": message, "apikey": APIKEY}
        r = requests.get("https://api.callmebot.com/whatsapp.php", params=params, timeout=REQUEST_TIMEOUT)
        print(f"CallMeBot: {r.text[:200]}")
        if r.ok:
            mark_sent()
            return True
        print(f"HTTP {r.status_code}")
        return False
    except Exception as e:
        print(f"WA error: {e}")
        return False

def get_crypto_prices() -> dict:
    fallback = {
        "BTC": (112500.0, 111200.0, 113800.0),
        "ETH": (2650.0, 2610.0, 2690.0),
        "XAU": (4141.0, 4105.0, 4175.0),
    }
    result = dict(fallback)
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": "bitcoin,ethereum,pax-gold", "per_page": 3, "page": 1}
        r = requests.get(url, params=params, headers={"User-Agent": "Bot/1.0"}, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        for coin in r.json():
            mapping = {"bitcoin": "BTC", "ethereum": "ETH", "pax-gold": "XAU"}
            sym = mapping.get(coin.get("id"))
            if sym:
                result[sym] = (float(coin["current_price"]), float(coin["low_24h"]), float(coin["high_24h"]))
    except Exception as e:
        print(f"Crypto fallback: {e}")
    return result

def get_fx_prices() -> dict:
    fallback = {
        "GBP": (1.3220, 1.30, 1.34),
        "JPY": (157.82, 155.0, 160.0),
        "EUR": (1.1251, 1.10, 1.15),
    }
    result = dict(fallback)
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        rates = r.json()["rates"]
        result["GBP"] = (1.0 / float(rates["GBP"]), 0, 0)
        result["EUR"] = (1.0 / float(rates["EUR"]), 0, 0)
        result["JPY"] = (float(rates["JPY"]), 0, 0)
    except Exception as e:
        print(f"FX fallback: {e}")
    return result

def build_history(price: float, symbol: str) -> List[float]:
    seed = int(hashlib.sha256(f"{symbol}-{int(price*100)}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    closes = []
    current = price * 0.9995
    for _ in range(HISTORY_LENGTH):
        current *= 1.0 + rng.uniform(-0.0008, 0.0008)
        closes.append(current)
    closes[-1] = price
    return closes

def ema(values: List[float], period: int) -> float:
    multiplier = 2.0 / (period + 1.0)
    current = sum(values[:period]) / period
    for p in values[period:]:
        current = (p * multiplier) + (current * (1.0 - multiplier))
    return current

def rsi_calc(values: List[float], period: int = RSI_PERIOD) -> float:
    gains = []
    losses = []
    for i in range(1, len(values)):
        ch = values[i] - values[i-1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def find_recent_pivots(values: List[float], window: int = 2):
    highs = []
    lows = []
    for i in range(window, len(values) - window):
        left = values[i-window:i]
        right = values[i+1:i+window+1]
        if values[i] > max(left) and values[i] > max(right):
            highs.append(i)
        if values[i] < min(left) and values[i] < min(right):
            lows.append(i)
    return highs, lows

def detect_structure(values: List[float]) -> str:
    highs, lows = find_recent_pivots(values)
    if len(highs) < 2 or len(lows) < 2:
        return "NON CLAIRE"
    h1, h2 = highs[-2], highs[-1]
    l1, l2 = lows[-2], lows[-1]
    if values[h2] > values[h1] and values[l2] > values[l1]:
        return "HAUSSIERE"
    if values[h2] < values[h1] and values[l2] < values[l1]:
        return "BAISSIERE"
    return "MIXTE"

def trend_from_ema(price, e50, prev_e50, tol=0.0005):
    ch = (e50 - prev_e50) / prev_e50
    if price > e50 and ch > tol:
        return "HAUSSIERE"
    if price < e50 and ch < -tol:
        return "BAISSIERE"
    return "NON CLAIRE"

def price_action_confirmation(values: List[float]) -> str:
    if len(values) < 3:
        return "AUCUNE"
    p2, p1, c = values[-3], values[-2], values[-1]
    if c > p1 > p2:
        return "MOMENTUM HAUSSIER"
    if c < p1 < p2:
        return "MOMENTUM BAISSIER"
    return "AUCUNE"

def pro_analysis(market: MarketData) -> Analysis:
    closes = market.closes
    e9 = ema(closes, EMA_FAST)
    e21 = ema(closes, EMA_SIGNAL)
    e50 = ema(closes, EMA_TREND)
    prev_e50 = ema(closes[:-1], EMA_TREND)
    structure = detect_structure(closes)
    trend = trend_from_ema(market.price, e50, prev_e50)
    confirmation = price_action_confirmation(closes)
    recent = closes[-20:]
    support = min(recent)
    resistance = max(recent)

    bullish = (trend == "HAUSSIERE" and structure == "HAUSSIERE" and e9 > e21)
    bearish = (trend == "BAISSIERE" and structure == "BAISSIERE" and e9 < e21)

    if bullish and confirmation == "MOMENTUM HAUSSIER":
        signal = "ACHAT"
    elif bearish and confirmation == "MOMENTUM BAISSIER":
        signal = "VENTE"
    else:
        signal = "WAIT"

    return Analysis(
        symbol=market.symbol,
        price=market.price,
        support=support,
        resistance=resistance,
        ema9=e9,
        ema21=e21,
        ema50=e50,
        signal=signal
    )

def fmt_price(symbol: str, price: float) -> str:
    if symbol in {"GBP", "EUR"}:
        return f"{price:.4f}"
    if symbol == "JPY":
        return f"{price:.2f}"
    return f"{price:.2f}"

def format_analysis(a: Analysis) -> str:
    names = {"BTC": "BTC/USD", "ETH": "ETH/USD", "XAU": "XAU/USD", "GBP": "GBP/USD", "JPY": "USD/JPY", "EUR": "EUR/USD"}
    full = names.get(a.symbol, a.symbol)

    if "ACHAT" in a.signal:
        decision = "🔵 BUY"
    elif "VENTE" in a.signal:
        decision = "🔴 SELL"
    else:
        decision = "🟡 WAIT"

    return (
        f"{full}: {fmt_price(a.symbol, a.price)}\n"
        f" Sup: {fmt_price(a.symbol, a.support)} | Res: {fmt_price(a.symbol, a.resistance)}\n"
        f" EMA9:{fmt_price(a.symbol, a.ema9)} EMA21:{fmt_price(a.symbol, a.ema21)}\n"
        f" {decision}"
    )

def create_market_data() -> List[MarketData]:
    crypto = get_crypto_prices()
    fx = get_fx_prices()
    raw = [
        ("BTC", *crypto["BTC"]),
        ("ETH", *crypto["ETH"]),
        ("XAU", *crypto["XAU"]),
        ("GBP", *fx["GBP"]),
        ("JPY", *fx["JPY"]),
        ("EUR", *fx["EUR"]),
    ]
    markets = []
    for symbol, price, low, high in raw:
        closes = build_history(price, symbol)
        markets.append(MarketData(symbol=symbol, price=price, low_24h=low, high_24h=high, closes=closes))
    return markets

def build_message(analyses: List[Analysis]) -> str:
    lines = ["📊 SIGNAL MULTI ODILON - OPPORTUNITE!", ""]
    for a in analyses:
        lines.append(format_analysis(a))
        lines.append("")
    lines.append(f"⏰ {time.strftime('%H:%M')} GMT+1")
    return "\n".join(lines)

def send_once_force():
    try:
        markets = create_market_data()
        analyses = [pro_analysis(m) for m in markets]
        msg = build_message(analyses)
        print(msg)
        print(f"Longueur: {len(msg)} caracteres")
        send_whatsapp(msg, force=True)
    except Exception as e:
        print(f"Force error: {e}")

def bot_loop() -> None:
    time.sleep(10)
    print("Bot V30 demarre - Formulaire Odilon")
    while True:
        try:
            markets = create_market_data()
            analyses = [pro_analysis(m) for m in markets]
            msg = build_message(analyses)
            print(msg)
            send_whatsapp(msg)
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(SEND_INTERVAL_SECONDS)

threading.Thread(target=bot_loop, daemon=True, name="bot-v30").start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)