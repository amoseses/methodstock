import random
from .config import settings

def select_universe(tickers, market_data, count=None, seed=None):
    count = count or settings.stocks_per_run
    eligible = []
    rejected = []
    for ticker in dict.fromkeys(t.upper() for t in tickers if t):
        meta = market_data.market_metadata(ticker)
        cap, volume = meta.get("market_cap"), meta.get("avg_volume")
        if settings.universe_mode == "all_candidates":
            eligible.append(ticker)
            continue
        if cap is None or volume is None:
            rejected.append({"ticker": ticker, "reason": "missing market-cap/volume metadata"})
            continue
        if settings.min_market_cap <= cap <= settings.max_market_cap and volume >= settings.min_avg_volume:
            eligible.append(ticker)
        else:
            rejected.append({"ticker": ticker, "reason": "outside market-cap or volume screen"})
    if not eligible:
        raise RuntimeError("No eligible stocks. Check metadata/provider or set UNIVERSE_MODE=all_candidates.")
    rng = random.Random(seed)
    chosen = rng.sample(eligible, min(count, len(eligible)))
    return chosen, {"eligible_count": len(eligible), "rejected": rejected, "seed": seed}
