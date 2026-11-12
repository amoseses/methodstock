import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

DEFAULT_TICKERS = [x.strip().upper() for x in os.getenv("UNIVERSE_TICKERS", "").split(",") if x.strip()]

@dataclass
class Settings:
    price_provider: str = os.getenv("PRICE_PROVIDER", "yfinance").lower()
    news_provider: str = os.getenv("NEWS_PROVIDER", "alpaca").lower()
    alpaca_key: str = os.getenv("ALPACA_API_KEY", "")
    alpaca_secret: str = os.getenv("ALPACA_SECRET_KEY", "")
    alpaca_feed: str = os.getenv("ALPACA_DATA_FEED", "iex")
    finnhub_key: str = os.getenv("FINNHUB_API_KEY", "")
    min_market_cap: float = float(os.getenv("MIN_MARKET_CAP", "2000000000"))
    max_market_cap: float = float(os.getenv("MAX_MARKET_CAP", "10000000000"))
    min_avg_volume: int = int(os.getenv("MIN_AVG_DAILY_VOLUME", "200000"))
    stocks_per_run: int = int(os.getenv("STOCKS_PER_RUN", "16"))
    combined_tech_weight: float = float(os.getenv("COMBINED_TECH_WEIGHT", "0.60"))
    starting_cash: float = float(os.getenv("PAPER_STARTING_CASH", "10000"))
    max_position_fraction: float = float(os.getenv("MAX_POSITION_FRACTION", "0.10"))
    stop_loss_pct: float = float(os.getenv("STOP_LOSS_PCT", "0.05"))
    take_profit_pct: float = float(os.getenv("TAKE_PROFIT_PCT", "0.10"))
    slippage_bps: float = float(os.getenv("SLIPPAGE_BPS", "5"))
    fee_per_trade: float = float(os.getenv("FEE_PER_TRADE", "0"))
    database_path: str = os.getenv("DATABASE_PATH", "data/stock_intelligence.sqlite3")
    reports_dir: str = os.getenv("REPORTS_DIR", "reports")
    universe_mode: str = os.getenv("UNIVERSE_MODE", "strict")

settings = Settings()
