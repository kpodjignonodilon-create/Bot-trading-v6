import os
import time
import urllib.parse
import threading
from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests
from flask import Flask

# ============================================================
# EDUCATIONAL / PAPER-ANALYSIS BOT
# ------------------------------------------------------------
# This bot sends market-analysis messages only. It does NOT
# place orders. It is designed around the concepts learned:
# - Support / Resistance
# - Market structure (HH, HL, LH, LL)
# - Price Action confirmation
# - EMA 50 as a trend/context filter
# - EMA 9 / EMA 21 as optional momentum context
# - RSI as a secondary filter, NOT as an automatic signal
# - WAIT when the market is unclear
#
# IMPORTANT:
# Do not put API keys directly in this file. Use environment
# variables on your hosting platform (e.g. GitHub/Render).
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Educational Trading Analysis Bot - OK"


# -----------------------------
# Configuration
# -----------------------------

PHONE = os.getenv("PHONE", "")
APIKEY = os.getenv("APIKEY", "")

SEND_INTERVAL_SECONDS = int(os.getenv("SEND_INTERVAL_SECONDS", "7200"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "12"))

# Analysis periods
EMA_FAST = 9
EMA_SIGNAL = 21
EMA_TREND = 50
RSI_PERIOD = 14

# A minimum amount of history is required for EMA 50 and
# structure calculations.
HISTORY_LENGTH = 120


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


# -----------------------------
# WhatsApp
# -----------------------------

LOCK_FILE = "/tmp/last_send_v25.txt"


def can_send() -> bool:
    """Rate-limit WhatsApp messages."""
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                last = float(f.read().strip() or 0)

            return (time.time() - last) >= SEND_INTERVAL_SECONDS

        return True
    except (OSError, ValueError):
        return True


def mark_sent() -> None:
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        f.write(str(time.time()))


def send_whatsapp(message: str) -> bool:
    """
    Sends a message through CallMeBot.
    No trading order is placed.
    """
    if not PHONE or not APIKEY:
        print("WhatsApp not configured: PHONE/APIKEY missing.")
        return False

    if not can_send():
        print("WhatsApp rate limit active.")
        return False

    try:
        params = {
            "phone": PHONE,
            "text": message,
            "apikey": APIKEY,
        }

        response = requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        if response.ok:
            mark_sent()
            return True

        print(f"WhatsApp HTTP error: {response.status_code}")
        return False

    except requests.RequestException as exc:
        print(f"WhatsApp error: {exc}")
        return False


# -----------------------------
# Data acquisition
# -----------------------------

def get_crypto_prices() -> dict:
    """
    Gets current prices and 24h high/low for BTC, ETH and PAXG.
    """
    fallback = {
        "BTC": (112500.0, 111200.0, 113800.0),
        "ETH": (2650.0, 2610.0, 2690.0),
        "XAU": (4141.0, 4105.0, 4175.0),
    }

    result = dict(fallback)

    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": "bitcoin,ethereum,pax-gold",
            "order": "market_cap_desc",
            "per_page": 3,
            "page": 1,
        }

        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": "EducationalTradingAnalysisBot/1.0"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        for coin in response.json():
            mapping = {
                "bitcoin": "BTC",
                "ethereum": "ETH",
                "pax-gold": "XAU",
            }

            symbol = mapping.get(coin.get("id"))
            if symbol:
                result[symbol] = (
                    float(coin["current_price"]),
                    float(coin["low_24h"]),
                    float(coin["high_24h"]),
                )

    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        print(f"Crypto data error: {exc}. Using fallback values.")

    return result


def get_fx_prices() -> dict:
    """
    Gets USD-based FX rates and converts them to:
    GBP/USD, USD/JPY, EUR/USD.
    """
    fallback = {
        "GBP": (1.3220, 1.30, 1.34),
        "JPY": (157.82, 155.0, 160.0),
        "EUR": (1.1251, 1.10, 1.15),
    }

    result = dict(fallback)

    try:
        response = requests.get(
            "https://open.er-api.com/v6/latest/USD",
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        rates = response.json()["rates"]

        gbp_usd = 1.0 / float(rates["GBP"])
        eur_usd = 1.0 / float(rates["EUR"])
        usd_jpy = float(rates["JPY"])

        # The API provides USD->currency. We don't have true
        # 24h highs/lows here, so we use a narrow contextual
        # range around the current value rather than pretending
        # these are real 24h levels.
        result["GBP"] = (
            gbp_usd,
            gbp_usd * 0.997,
            gbp_usd * 1.003,
        )
        result["EUR"] = (
            eur_usd,
            eur_usd * 0.997,
            eur_usd * 1.003,
        )
        result["JPY"] = (
            usd_jpy,
            usd_jpy * 0.997,
            usd_jpy * 1.003,
        )

    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        print(f"FX data error: {exc}. Using fallback values.")

    return result


def build_history(price: float, symbol: str) -> List[float]:
    """
    Creates deterministic synthetic history from the current price.

    IMPORTANT:
    This is NOT real historical market data.
    Therefore EMA/RSI/structure values for these assets are
    educational approximations, not trading-grade signals.

    Replace this function with real OHLC historical candles
    before relying on the analysis for serious research.
    """
    import hashlib
    import random

    seed_text = f"{symbol}-{int(price)}"
    seed = int(hashlib.sha256(seed_text.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    closes = []
    current = price * 0.985

    for _ in range(HISTORY_LENGTH):
        current *= 1.0 + rng.uniform(-0.0035, 0.0035)
        closes.append(current)

    closes[-1] = price
    return closes


# -----------------------------
# Indicators
# -----------------------------

def ema(values: List[float], period: int) -> float:
    """Calculate EMA using SMA initialization."""
    if len(values) < period:
        raise ValueError(f"Need at least {period} values for EMA.")

    multiplier = 2.0 / (period + 1.0)
    current = sum(values[:period]) / period

    for price in values[period:]:
        current = (price * multiplier) + (
            current * (1.0 - multiplier)
        )

    return current


def rsi_calc(values: List[float], period: int = RSI_PERIOD) -> float:
    """Wilder-style RSI calculation."""
    if len(values) <= period:
        raise ValueError("Not enough values for RSI.")

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


# -----------------------------
# Price Action / structure
# -----------------------------

def find_recent_pivots(
    values: List[float],
    window: int = 2,
) -> Tuple[List[int], List[int]]:
    """
    Finds simple local swing highs/lows.
    This is a simplified educational structure detector.
    """
    highs = []
    lows = []

    for i in range(window, len(values) - window):
        left = values[i - window:i]
        right = values[i + 1:i + window + 1]

        if values[i] > max(left) and values[i] > max(right):
            highs.append(i)

        if values[i] < min(left) and values[i] < min(right):
            lows.append(i)

    return highs, lows


def detect_structure(values: List[float]) -> str:
    """
    Uses the two most recent swing highs and lows to classify
    basic HH/HL or LH/LL structure.
    """
    highs, lows = find_recent_pivots(values)

    if len(highs) < 2 or len(lows) < 2:
        return "NON CLAIRE"

    h1, h2 = highs[-2], highs[-1]
    l1, l2 = lows[-2], lows[-1]

    higher_high = values[h2] > values[h1]
    higher_low = values[l2] > values[l1]

    lower_high = values[h2] < values[h1]
    lower_low = values[l2] < values[l1]

    if higher_high and higher_low:
        return "HAUSSIÈRE (HH + HL)"

    if lower_high and lower_low:
        return "BAISSIÈRE (LH + LL)"

    return "MIXTE / NON CLAIRE"


def trend_from_ema(
    price: float,
    ema9_value: float,
    ema21_value: float,
    ema50_value: float,
    previous_ema50: float,
    tolerance: float = 0.0005,
) -> str:
    """
    EMA 50 is the main context filter.

    We do not call a tiny change "uptrend" or "downtrend".
    A tolerance prevents noise from creating false direction.
    """
    ema50_change = (ema50_value - previous_ema50) / previous_ema50

    if (
        price > ema50_value
        and ema50_change > tolerance
    ):
        return "HAUSSIÈRE"

    if (
        price < ema50_value
        and ema50_change < -tolerance
    ):
        return "BAISSIÈRE"

    return "NON CLAIRE"


def price_action_confirmation(values: List[float]) -> str:
    """
    Very simple candle-style confirmation using the last three
    closing prices. This is intentionally conservative because
    this bot currently receives close-only synthetic history,
    not real OHLC candles.
    """
    if len(values) < 3:
        return "AUCUNE"

    prev2, prev1, current = values[-3], values[-2], values[-1]

    if current > prev1 > prev2:
        return "MOMENTUM HAUSSIER"

    if current < prev1 < prev2:
        return "MOMENTUM BAISSIER"

    return "AUCUNE"


# -----------------------------
# Complete analysis
# -----------------------------

def pro_analysis(
    market: MarketData,
) -> Analysis:
    closes = market.closes

    e9 = ema(closes, EMA_FAST)
    e21 = ema(closes, EMA_SIGNAL)
    e50 = ema(closes, EMA_TREND)
    rsi = rsi_calc(closes)

    # Calculate a previous EMA 50 to estimate direction.
    previous_e50 = ema(closes[:-1], EMA_TREND)

    structure = detect_structure(closes)

    trend = trend_from_ema(
        price=market.price,
        ema9_value=e9,
        ema21_value=e21,
        ema50_value=e50,
        previous_ema50=previous_e50,
    )

    confirmation = price_action_confirmation(closes)

    # Support/resistance from recent closes.
    # For real analysis, these should come from actual OHLC
    # swing levels/zones, not only closes.
    recent = closes[-24:]
    support = min(recent)
    resistance = max(recent)

    # --------------------------------------------------------
    # Signal logic
    # --------------------------------------------------------
    #
    # We deliberately require several pieces of evidence:
    # 1. EMA 50 context
    # 2. Structure
    # 3. Price-action confirmation
    #
    # RSI is only a secondary context filter.
    # It is NOT allowed to create a BUY/SELL by itself.
    # --------------------------------------------------------

    bullish_context = (
        trend == "HAUSSIÈRE"
        and structure == "HAUSSIÈRE (HH + HL)"
        and e9 > e21
    )

    bearish_context = (
        trend == "BAISSIÈRE"
        and structure == "BAISSIÈRE (LH + LL)"
        and e9 < e21
    )

    if bullish_context and confirmation == "MOMENTUM HAUSSIER":
        signal = "🟢 ACHAT POTENTIEL"
        reason = (
            "EMA50 haussière + structure HH/HL + "
            "EMA9>EMA21 + confirmation haussière."
        )

    elif bearish_context and confirmation == "MOMENTUM BAISSIER":
        signal = "🔴 VENTE POTENTIELLE"
        reason = (
            "EMA50 baissière + structure LH/LL + "
            "EMA9<EMA21 + confirmation baissière."
        )

    else:
        signal = "🟡 ATTENTE"
        reason = (
            "Les confirmations ne sont pas suffisamment alignées. "
            "On attend plutôt qu'une configuration plus claire apparaisse."
        )

    # RSI is informative only.
    if rsi >= 70:
        rsi_context = "RSI élevé"
    elif rsi <= 30:
        rsi_context = "RSI faible"
    else:
        rsi_context = "RSI neutre"

    reason += f" {rsi_context} ({rsi:.0f})."

    return Analysis(
        symbol=market.symbol,
        price=market.price,
        support=support,
        resistance=resistance,
        ema9=e9,
        ema21=e21,
        ema50=e50,
        rsi=rsi,
        trend=trend,
        structure=structure,
        signal=signal,
        confirmation=confirmation,
        reason=reason,
    )


# -----------------------------
# Formatting
# -----------------------------

def fmt_price(symbol: str, price: float) -> str:
    if symbol in {"GBP", "EUR"}:
        return f"{price:.4f}"
    if symbol == "JPY":
        return f"{price:.2f}"
    return f"{price:.2f}"


def format_analysis(a: Analysis) -> str:
    return (
        f"📌 {a.symbol}: {fmt_price(a.symbol, a.price)}\n"
        f"   S: {fmt_price(a.symbol, a.support)} | "
        f"R: {fmt_price(a.symbol, a.resistance)}\n"
        f"   EMA9: {fmt_price(a.symbol, a.ema9)} | "
        f"EMA21: {fmt_price(a.symbol, a.ema21)} | "
        f"EMA50: {fmt_price(a.symbol, a.ema50)}\n"
        f"   RSI: {a.rsi:.0f}\n"
        f"   Tendance EMA50: {a.trend}\n"
        f"   Structure: {a.structure}\n"
        f"   Confirmation: {a.confirmation}\n"
        f"   ➜ {a.signal}\n"
        f"   Pourquoi: {a.reason}"
    )


# -----------------------------
# Build market data
# -----------------------------

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

        markets.append(
            MarketData(
                symbol=symbol,
                price=price,
                low_24h=low,
                high_24h=high,
                closes=closes,
            )
        )

    return markets


# -----------------------------
# Bot loop
# -----------------------------

def build_message(analyses: List[Analysis]) -> str:
    lines = [
        "📊 ANALYSE TECHNIQUE — EDUCATIONAL BOT",
        "",
        "Méthode:",
        "EMA50 + structure + S/R + Price Action",
        "EMA9/21 et RSI = contexte secondaire",
        "",
        "⚠️ Aucun ordre n'est exécuté par ce bot.",
        "🟡 ATTENTE = confirmations insuffisantes.",
        "",
    ]

    for analysis in analyses:
        lines.append(format_analysis(analysis))
        lines.append("")

    lines.append(
        f"⏰ {time.strftime('%Y-%m-%d %H:%M')} GMT+1"
    )

    return "\n".join(lines)


def bot_loop() -> None:
    # Give Flask time to start on hosting platforms.
    time.sleep(10)

    while True:
        try:
            markets = create_market_data()
            analyses = [pro_analysis(market) for market in markets]

            message = build_message(analyses)
            print(message)

            send_whatsapp(message)

        except Exception as exc:
            # Keep the server alive if one analysis fails.
            print(f"Bot loop error: {exc}")

        time.sleep(SEND_INTERVAL_SECONDS)


# -----------------------------
# Start only one background loop
# -----------------------------

if os.environ.get("BOT_STARTED") != "1":
    os.environ["BOT_STARTED"] = "1"
    threading.Thread(
        target=bot_loop,
        daemon=True,
        name="analysis-bot",
    ).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)