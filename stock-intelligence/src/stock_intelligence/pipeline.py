from datetime import datetime, timezone
from pathlib import Path
import json, random
import pandas as pd
from .config import settings, DEFAULT_TICKERS
from .providers import MarketData, NewsData
from .selection import select_universe
from .indicators import score_technical
from .news import score_news
from .signals import generate_signals
from .storage import Store
from .simulator import Portfolio

def run_scan(tickers=None, seed=None):
    market, news_provider = MarketData(), NewsData()
    tickers = tickers or DEFAULT_TICKERS
    chosen, selection_meta = select_universe(tickers, market, seed=seed)
    store = Store(settings.database_path)
    scanned_at = datetime.now(timezone.utc)
    portfolios = [Portfolio("news"), Portfolio("technical"), Portfolio("combined")]
    for portfolio in portfolios:
        saved = store.load_portfolio_state(portfolio.name)
        if saved:
            portfolio.cash = saved["cash"]
            portfolio.positions = saved["positions"]
    output = []
    errors = []
    latest_prices = {}
    for ticker in chosen:
        try:
            hist = market.history(ticker, period="3mo", interval="1d")
            tech = score_technical(hist)
            try:
                articles = news_provider.fetch(ticker)
                news = score_news(articles, as_of=scanned_at)
            except Exception as e:
                articles = []
                news = {"news_score": 0.0, "major_negative": False,
                        "article_count": 0, "articles": [], "news_status": f"unavailable: {e}"}
            signals = generate_signals(tech["technical_score"], news["news_score"], news["major_negative"])
            row = {"scanned_at": scanned_at.isoformat(), "ticker": ticker, "price": tech["price"],
                   "technical_score": tech["technical_score"], "news_score": news["news_score"],
                   "combined_score": signals["combined"]["score"], "signals": signals,
                   "articles": news["articles"], "news_status": news["news_status"],
                   "technical_reasons": tech["reasons"], "rsi": tech["rsi"]}
            store.save_scan(row)
            latest_prices[ticker] = tech["price"]
            portfolios[0].mark_and_trade(ticker, tech["price"], signals["news"]["decision"], store)
            portfolios[1].mark_and_trade(ticker, tech["price"], signals["technical"]["decision"], store)
            portfolios[2].mark_and_trade(ticker, tech["price"], signals["combined"]["decision"], store)
            output.append(row)
        except Exception as e:
            errors.append({"ticker":ticker,"error":str(e)})
    for p in portfolios:
        for t, pos in p.positions.items():
            latest_prices.setdefault(t, pos["avg_cost"])
        store.save_portfolio_state(p.name, p.cash, p.positions)
    result = {"scanned_at": scanned_at.isoformat(), "selected_tickers": chosen,
              "selection": selection_meta, "results": output, "errors": errors,
              "portfolio_snapshots": [{"name":p.name,"cash":p.cash,"equity":p.value(latest_prices),
                                       "open_positions":p.positions} for p in portfolios]}
    reports = Path(settings.reports_dir); reports.mkdir(parents=True, exist_ok=True)
    (reports/"latest_scan.json").write_text(json.dumps(result, indent=2, default=str))
    if output:
        pd.DataFrame([{k:v for k,v in r.items() if k not in ("signals","articles","technical_reasons")} for r in output]).to_csv(
            reports/f"signals_{scanned_at.date()}.csv", index=False)
    trades = store.trades()
    trades.to_csv(reports/"trades.csv", index=False)
    store.close()
    return result

def run_backtest(tickers=None, period="2y"):
    # Technical-only historical backtest. Historical point-in-time news is not
    # supplied by the current-news APIs, so news/combined backtests are omitted.
    import yfinance as yf
    from .indicators import add_indicators
    from pathlib import Path
    tickers = tickers or DEFAULT_TICKERS[:40]
    rows=[]
    for ticker in tickers:
        try:
            df=yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=True)
            if len(df)<60: continue
            df=df.rename(columns={c:c.lower() for c in df.columns})
            x=add_indicators(df)
            cash=10000.0; shares=0.0; entry=0.0; equity=[]
            for i in range(30,len(x)-1):
                r=x.iloc[i]; next_open=float(x.iloc[i+1]["open"])
                score=0
                score += 1 if r.ema9>r.ema21 else -1
                score += 1 if r.close>r.vwap else -1
                score += 1 if pd.notna(r.rsi) and 50<r.rsi<68 else 0
                if shares==0 and score>=2:
                    shares=(cash*0.10)/next_open; cash-=shares*next_open; entry=next_open
                elif shares>0 and (score<=-1 or next_open<=entry*.95 or next_open>=entry*1.10):
                    cash+=shares*next_open; shares=0; entry=0
                equity.append(cash+shares*float(r.close))
            final=cash+shares*float(x.iloc[-1].close)
            rows.append({"ticker":ticker,"final_value":final,"return_pct":(final/10000-1)*100,
                         "observations":len(equity)})
        except Exception as e:
            rows.append({"ticker":ticker,"error":str(e)})
    out=pd.DataFrame(rows)
    Path(settings.reports_dir).mkdir(parents=True,exist_ok=True)
    out.to_csv(Path(settings.reports_dir)/"technical_backtest.csv",index=False)
    return out
