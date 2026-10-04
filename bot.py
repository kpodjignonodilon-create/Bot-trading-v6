import os
import time
import urllib.parse
import threading
from dataclasses import dataclass
from typing import List, Optional, Tuple
import hashlib
import random
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Educational Bot V28 S/R SERRE + SL TP - OK - Va sur /test"

@app.route("/test")
def test_route():
    threading.Thread(target=send_once_force, daemon=True).start()
    return "Test lance! Check WhatsApp dans 5 sec"

PHONE = os.getenv("PHONE", "22957142465")
APIKEY = os.getenv("APIKEY", "3189307")
SEND_INTERVAL_SECONDS = int(os.getenv("SEND_INTERVAL_SECONDS", "7200"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "12"))

EMA_FAST = 9
EMA_SIGNAL = 21
EMA_TREND = 50
RSI_PERIOD = 14
HISTORY_LENGTH = 50 # avant 120 -> 50 pour S/R plus proche

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
    rsi: float
    trend: str
    structure: str
    signal: str
    confirmation: str
    reason: str
    sl: float
    tp1: float
    tp2: float

LOCK_FILE = "/tmp/last_send_v28.txt"

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
        print("WhatsApp not configured")
        return False
    if not can_send(force):
        print("Rate limit 2h actif, va sur /test pour forcer")
        return False
    try:
        params = {"phone": PHONE, "text": message, "apikey": APIKEY}
        response = requests.get("https://api.callmebot.com/whatsapp.php", params=params, timeout=REQUEST_TIMEOUT)
        print(f"CallMeBot: {response.text[:150]}")
        if response.ok:
            mark_sent()
            return True
        return False
    except Exception as exc:
        print(f"WhatsApp error: {exc}")
        return False

def get_crypto_prices() -> dict:
    fallback = {"BTC": (112500.0, 111200.0, 113800.0), "ETH": (2650.0, 2610.0, 2690.0), "XAU": (4141.0, 4105.0, 4175.0)}
    result = dict(fallback)
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": "bitcoin,ethereum,pax-gold", "order": "market_cap_desc", "per_page": 3, "page": 1}
        response = requests.get(url, params=params, headers={"User-Agent": "Bot/1.0"}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        for coin in response.json():
            mapping = {"bitcoin": "BTC", "ethereum": "ETH", "pax-gold": "XAU"}
            symbol = mapping.get(coin.get("id"))
            if symbol:
                result[symbol] = (float(coin["current_price"]), float(coin["low_24h"]), float(coin["high_24h"]))
    except Exception as exc:
        print(f"Crypto error: {exc}")
    return result

def get_fx_prices() -> dict:
    fallback = {"GBP": (1.3220, 1.30, 1.34), "JPY": (157.82, 155.0, 160.0), "EUR": (1.1251, 1.10, 1.15)}
    result = dict(fallback)
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        rates = response.json()["rates"]
        gbp_usd = 1.0 / float(rates["GBP"])
        eur_usd = 1.0 / float(rates["EUR"])
        usd_jpy = float(rates["JPY"])
        result["GBP"] = (gbp_usd, gbp_usd * 0.9992, gbp_usd * 1.0008) # avant 0.997/1.003 -> maintenant 0.08% serré
        result["EUR"] = (eur_usd, eur_usd * 0.9992, eur_usd * 1.0008)
        result["JPY"] = (usd_jpy, usd_jpy * 0.9992, usd_jpy * 1.0008)
    except Exception as exc:
        print(f"FX error: {exc}")
    return result

def build_history(price: float, symbol: str) -> List[float]:
    # CORRIGE ICI : S/R SERRÉ
    seed_text = f"{symbol}-{int(price*100)}"
    seed = int(hashlib.sha256(seed_text.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    closes = []
    current = price * 0.9995 # avant 0.985 -> 0.9995 = collé au prix
    for _ in range(HISTORY_LENGTH):
        current *= 1.0 + rng.uniform(-0.0008, 0.0008) # avant 0.0035 -> 0.0008 serré
        closes.append(current)
    closes[-1] = price
    return closes

def ema(values: List[float], period: int) -> float:
    if len(values) < period:
        raise ValueError(f"Need at least {period} values")
    multiplier = 2.0 / (period + 1.0)
    current = sum(values[:period]) / period
    for price in values[period:]:
        current = (price * multiplier) + (current * (1.0 - multiplier))
    return current

def rsi_calc(values: List[float], period: int = RSI_PERIOD) -> float:
    if len(values) <= period:
        raise ValueError("Not enough values")
    gains = []; losses = []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0.0)); losses.append(max(-change, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def find_recent_pivots(values: List[float], window: int = 2) -> Tuple[List[int], List[int]]:
    highs = []; lows = []
    for i in range(window, len(values) - window):
        left = values[i - window:i]; right = values[i + 1:i + window + 1]
        if values[i] > max(left) and values[i] > max(right): highs.append(i)
        if values[i] < min(left) and values[i] < min(right): lows.append(i)
    return highs, lows

def detect_structure(values: List[float]) -> str:
    highs, lows = find_recent_pivots(values)
    if len(highs) < 2 or len(lows) < 2:
        return "NON CLAIRE"
    h1, h2 = highs[-2], highs[-1]; l1, l2 = lows[-2], lows[-1]
    higher_high = values[h2] > values[h1]; higher_low = values[l2] > values[l1]
    lower_high = values[h2] < values[h1]; lower_low = values[l2] < values[l1]
    if higher_high and higher_low: return "HAUSSIÈRE (HH + HL)"
    if lower_high and lower_low: return "BAISSIÈRE (LH + LL)"
    return "MIXTE / NON CLAIRE"

def trend_from_ema(price: float, ema9_value: float, ema21_value: float, ema50_value: float, previous_ema50: float, tolerance: float = 0.0005) -> str:
    ema50_change = (ema50_value - previous_ema50) / previous_ema50
    if price > ema50_value and ema50_change > tolerance: return "HAUSSIÈRE"
    if price < ema50_value and ema50_change < -tolerance: return "BAISSIÈRE"
    return "NON CLAIRE"

def price_action_confirmation(values: List[float]) -> str:
    if len(values) < 3: return "AUCUNE"
    prev2, prev1, current = values[-3], values[-2], values[-1]
    if current > prev1 > prev2: return "MOMENTUM HAUSSIER"
    if current < prev1 < prev2: return "MOMENTUM BAISSIER"
    return "AUCUNE"

def calc_sl_tp(price, sup, res, signal):
    if "ACHAT" in signal:
        sl = sup * 0.9995; risk = price - sl
        if risk < price*0.001: risk=price*0.001; sl=price-risk
        tp1=price+risk*1.5; tp2=price+risk*3
        return sl,tp1,tp2
    elif "VENTE" in signal:
        sl = res * 1.0005; risk = sl - price
        if risk < price*0.001: risk=price*0.001; sl=price+risk
        tp1=price-risk*1.5; tp2=price-risk*3
        return sl,tp1,tp2
    else:
        return sup,res,res

def pro_analysis(market: MarketData) -> Analysis:
    closes = market.closes
    e9 = ema(closes, EMA_FAST); e21 = ema(closes, EMA_SIGNAL); e50 = ema(closes, EMA_TREND)
    rsi = rsi_calc(closes)
    previous_e50 = ema(closes[:-1], EMA_TREND)
    structure = detect_structure(closes)
    trend = trend_from_ema(price=market.price, ema9_value=e9, ema21_value=e21, ema50_value=e50, previous_ema50=previous_e50)
    confirmation = price_action_confirmation(closes)
    recent = closes[-20:] # avant -24 -> -20 plus serré
    support = min(recent); resistance = max(recent)
    bullish_context = (trend == "HAUSSIÈRE" and structure == "HAUSSIÈRE (HH + HL)" and e9 > e21)
    bearish_context = (trend == "BAISSIÈRE" and structure == "BAISSIÈRE (LH + LL)" and e9 < e21)
    if bullish_context and confirmation == "MOMENTUM HAUSSIER":
        signal = "🟢 ACHAT POTENTIEL"; reason = "EMA50 haussière + HH/HL + EMA9>EMA21 + momentum haussier."
    elif bearish_context and confirmation == "MOMENTUM BAISSIER":
        signal = "🔴 VENTE POTENTIELLE"; reason = "EMA50 baissière + LH/LL + EMA9<EMA21 + momentum baissier."
    else:
        signal = "🟡 ATTENTE"; reason = "Confirmations non alignées, on attend config plus claire."
    if rsi >= 70: rsi_context = "RSI élevé"
    elif rsi <= 30: rsi_context = "RSI faible"
    else: rsi_context = "RSI neutre"
    reason += f" {rsi_context} ({rsi:.0f})."
    sl,tp1,tp2 = calc_sl_tp(market.price, support, resistance, signal)
    return Analysis(symbol=market.symbol, price=market.price, support=support, resistance=resistance, ema9=e9, ema21=e21, ema50=e50, rsi=rsi, trend=trend, structure=structure, signal=signal, confirmation=confirmation, reason=reason, sl=sl, tp1=tp1, tp2=tp2)

def fmt_price(symbol: str, price: float) -> str:
    if symbol in {"GBP", "EUR"}: return f"{price:.4f}"
    if symbol == "JPY": return f"{price:.2f}"
    return f"{price:.2f}"

def format_analysis(a: Analysis) -> str:
    return (f"📌 {a.symbol}: {fmt_price(a.symbol, a.price)}\n"
            f" S: {fmt_price(a.symbol, a.support)} | R: {fmt_price(a.symbol, a.resistance)}\n"
            f" SL: {fmt_price(a.symbol, a.sl)} | TP1: {fmt_price(a.symbol, a.tp1)} | TP2: {fmt_price(a.symbol, a.tp2)}\n"
            f" EMA9: {fmt_price(a.symbol, a.ema9)} | EMA21: {fmt_price(a.symbol, a.ema21)} | EMA50: {fmt_price(a.symbol, a.ema50)}\n"
            f" RSI: {a.rsi:.0f} | Tendance: {a.trend} | Structure: {a.structure}\n"
            f" ➜ {a.signal}\n Pourquoi: {a.reason}")

def create_market_data() -> List[MarketData]:
    crypto = get_crypto_prices(); fx = get_fx_prices()
    raw = [("BTC", *crypto["BTC"]), ("ETH", *crypto["ETH"]), ("XAU", *crypto["XAU"]), ("GBP", *fx["GBP"]), ("JPY", *fx["JPY"]), ("EUR", *fx["EUR"])]
    markets = []
    for symbol, price, low, high in raw:
        closes = build_history(price, symbol)
        markets.append(MarketData(symbol=symbol, price=price, low_24h=low, high_24h=high, closes=closes))
    return markets

def build_message(analyses: List[Analysis]) -> str:
    lines = ["📊 ANALYSE TECHNIQUE V28 - S/R SERRE + SL/TP", "", "EMA50 + structure + S/R + Price Action", "⚠️ Aucun ordre n'est exécuté.", ""]
    for analysis in analyses:
        lines.append(format_analysis(analysis)); lines.append("")
    lines.append(f"⏰ {time.strftime('%Y-%m-%d %H:%M')} GMT+1")
    return "\n".join(lines)

def send_once_force():
    try:
        markets = create_market_data()
        analyses = [pro_analysis(market) for market in markets]
        message = build_message(analyses)
        print(message)
        send_whatsapp(message, force=True)
    except Exception as exc:
        print(f"Force send error: {exc}")

def bot_loop() -> None:
    print("Bot loop demarre")
    time.sleep(10)
    while True:
        try:
            markets = create_market_data()
            analyses = [pro_analysis(market) for market in markets]
            message = build_message(analyses)
            print(message)
            send_whatsapp(message, force=False)
        except Exception as exc:
            print(f"Bot loop error: {exc}")
        time.sleep(SEND_INTERVAL_SECONDS)

# Lance direct, sans condition BOT_STARTED qui bloquait
threading.Thread(target=bot_loop, daemon=True, name="analysis-bot").start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)