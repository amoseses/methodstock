import numpy as np
import pandas as pd

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy().sort_index()
    for col in ["open","high","low","close","volume"]:
        x[col] = pd.to_numeric(x[col], errors="coerce")
    x["ema9"] = x["close"].ewm(span=9, adjust=False).mean()
    x["ema21"] = x["close"].ewm(span=21, adjust=False).mean()
    delta = x["close"].diff()
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    x["rsi"] = 100 - (100 / (1 + rs))
    # Daily data: VWAP is an approximate rolling-session proxy. Intraday data:
    # caller should pass one session for a true session VWAP.
    typical = (x["high"] + x["low"] + x["close"]) / 3
    x["vwap"] = (typical * x["volume"]).cumsum() / x["volume"].replace(0, np.nan).cumsum()
    x["volume_avg20"] = x["volume"].rolling(20, min_periods=5).mean()
    x["volume_ratio"] = x["volume"] / x["volume_avg20"]
    x["body_pct"] = (x["close"] - x["open"]) / x["open"].replace(0, np.nan)
    return x

def score_technical(df: pd.DataFrame):
    x = add_indicators(df)
    if len(x) < 25:
        raise ValueError("Need at least 25 price bars for stable indicator scoring")
    row = x.iloc[-1]
    score = 0.0
    reasons = []
    if row.ema9 > row.ema21:
        score += 25; reasons.append("EMA9 above EMA21")
    else:
        score -= 25; reasons.append("EMA9 below EMA21")
    if row.close > row.vwap:
        score += 20; reasons.append("price above rolling VWAP proxy")
    else:
        score -= 20; reasons.append("price below rolling VWAP proxy")
    if pd.notna(row.rsi):
        if 50 <= row.rsi <= 68: score += 20; reasons.append("RSI in positive momentum range")
        elif row.rsi > 75: score -= 10; reasons.append("RSI overbought")
        elif row.rsi < 30: score += 5; reasons.append("RSI oversold; possible rebound, unconfirmed")
        elif row.rsi < 45: score -= 15; reasons.append("RSI weak")
    if pd.notna(row.volume_ratio) and row.volume_ratio >= 1.3:
        score += 15 if row.close > row.open else -15
        reasons.append("elevated volume confirms candle direction")
    if row.close > row.open:
        score += 10; reasons.append("latest candle closed green")
    else:
        score -= 10; reasons.append("latest candle closed red")
    return {"technical_score": float(max(-100, min(100, score))),
            "price": float(row.close), "rsi": None if pd.isna(row.rsi) else float(row.rsi),
            "ema9": float(row.ema9), "ema21": float(row.ema21),
            "vwap": float(row.vwap), "volume_ratio": None if pd.isna(row.volume_ratio) else float(row.volume_ratio),
            "reasons": reasons, "history": x}
