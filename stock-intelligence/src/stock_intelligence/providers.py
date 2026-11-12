from __future__ import annotations
from datetime import datetime, timedelta, timezone
import requests
import pandas as pd
import yfinance as yf
from .config import settings

class ProviderError(RuntimeError):
    pass

def _utc_iso(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

class MarketData:
    def history(self, ticker: str, period="3mo", interval="1d") -> pd.DataFrame:
        if settings.price_provider == "alpaca":
            return self._alpaca_history(ticker, period, interval)
        return self._yf_history(ticker, period, interval)

    def _yf_history(self, ticker, period, interval):
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            raise ProviderError(f"No price history returned for {ticker}")
        df = df.rename(columns={c: c.lower() for c in df.columns})
        df.index = pd.to_datetime(df.index)
        return df[["open", "high", "low", "close", "volume"]].dropna()

    def _alpaca_history(self, ticker, period, interval):
        if not settings.alpaca_key or not settings.alpaca_secret:
            raise ProviderError("Alpaca price provider selected but API keys are missing")
        days = {"1d": 365, "1h": 30, "1Min": 7}.get(interval, 90)
        start = datetime.now(timezone.utc) - timedelta(days=days)
        timeframe = {"1d": "1Day", "1h": "1Hour", "1Min": "1Min"}.get(interval, "1Day")
        url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars"
        headers = {"APCA-API-KEY-ID": settings.alpaca_key, "APCA-API-SECRET-KEY": settings.alpaca_secret}
        params = {"timeframe": timeframe, "start": _utc_iso(start), "limit": 10000, "adjustment": "split", "feed": settings.alpaca_feed}
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if not r.ok:
            raise ProviderError(f"Alpaca bars error {r.status_code}: {r.text[:300]}")
        rows = r.json().get("bars", [])
        if not rows:
            raise ProviderError(f"No Alpaca bars returned for {ticker}")
        df = pd.DataFrame(rows).rename(columns={"t":"timestamp","o":"open","h":"high","l":"low","c":"close","v":"volume"})
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df.set_index("timestamp")[["open","high","low","close","volume"]].astype(float)

    def market_metadata(self, ticker):
        try:
            info = yf.Ticker(ticker).get_info()
            return {
                "market_cap": info.get("marketCap"),
                "avg_volume": info.get("averageVolume") or info.get("averageDailyVolume10Day"),
                "name": info.get("shortName") or ticker
            }
        except Exception:
            return {"market_cap": None, "avg_volume": None, "name": ticker}

class NewsData:
    def fetch(self, ticker: str, limit=30):
        provider = settings.news_provider
        if provider == "none":
            return []
        if provider == "alpaca":
            return self._alpaca_news(ticker, limit)
        if provider == "finnhub":
            return self._finnhub_news(ticker)
        raise ProviderError(f"Unknown NEWS_PROVIDER={provider}")

    def _alpaca_news(self, ticker, limit):
        if not settings.alpaca_key or not settings.alpaca_secret:
            raise ProviderError("Alpaca news selected but API keys are missing")
        headers = {"APCA-API-KEY-ID": settings.alpaca_key, "APCA-API-SECRET-KEY": settings.alpaca_secret}
        params = {"symbols": ticker, "limit": limit, "sort": "desc", "include_content": "true"}
        r = requests.get("https://data.alpaca.markets/v1beta1/news", headers=headers, params=params, timeout=30)
        if not r.ok:
            raise ProviderError(f"Alpaca news error {r.status_code}: {r.text[:300]}")
        articles = []
        for a in r.json().get("news", []):
            articles.append({
                "ticker": ticker, "headline": a.get("headline", ""),
                "summary": a.get("summary", "") or a.get("content", ""),
                "source": a.get("source", "Alpaca"),
                "url": a.get("url", ""),
                "published_at": a.get("created_at", ""),
                "id": a.get("id", "")
            })
        return articles

    def _finnhub_news(self, ticker):
        if not settings.finnhub_key:
            raise ProviderError("Finnhub selected but FINNHUB_API_KEY is missing")
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=7)
        params = {"symbol": ticker, "from": start.isoformat(), "to": today.isoformat(), "token": settings.finnhub_key}
        r = requests.get("https://finnhub.io/api/v1/company-news", params=params, timeout=30)
        if not r.ok:
            raise ProviderError(f"Finnhub news error {r.status_code}: {r.text[:300]}")
        return [{
            "ticker": ticker, "headline": a.get("headline", ""),
            "summary": a.get("summary", ""), "source": a.get("source", "Finnhub"),
            "url": a.get("url", ""),
            "published_at": datetime.fromtimestamp(a["datetime"], timezone.utc).isoformat() if a.get("datetime") else "",
            "id": str(a.get("id", ""))
        } for a in r.json()]
