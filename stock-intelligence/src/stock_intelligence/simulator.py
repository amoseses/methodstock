from dataclasses import dataclass, field
from datetime import datetime, timezone
from .config import settings

@dataclass
class Portfolio:
    name: str
    cash: float = field(default_factory=lambda: settings.starting_cash)
    positions: dict = field(default_factory=dict)  # ticker -> shares, avg_cost
    trades: list = field(default_factory=list)

    def value(self, prices):
        return self.cash + sum(p["shares"] * prices.get(t, p["avg_cost"]) for t,p in self.positions.items())

    def mark_and_trade(self, ticker, price, decision, store=None):
        if price <= 0: return
        now = datetime.now(timezone.utc).isoformat()
        pos = self.positions.get(ticker)
        stop = pos and price <= pos["avg_cost"] * (1-settings.stop_loss_pct)
        take = pos and price >= pos["avg_cost"] * (1+settings.take_profit_pct)
        side = None
        reason = ""
        if pos and (decision in ("SELL","STRONG_EXIT") or stop or take):
            side = "SELL"
            reason = "signal" if decision in ("SELL","STRONG_EXIT") else ("stop_loss" if stop else "take_profit")
            shares = pos["shares"]
            fill = price * (1-settings.slippage_bps/10000)
            gross = shares * fill
            fees = settings.fee_per_trade
            self.cash += gross - fees
            del self.positions[ticker]
        elif not pos and decision in ("BUY","STRONG_BUY"):
            budget = min(self.cash, settings.starting_cash * settings.max_position_fraction)
            fill = price * (1+settings.slippage_bps/10000)
            shares = max(0, (budget-settings.fee_per_trade)/fill)
            if shares <= 0: return
            fees = settings.fee_per_trade
            self.cash -= shares*fill + fees
            self.positions[ticker] = {"shares": shares, "avg_cost": fill}
            side, reason = "BUY", "signal"
        else:
            return
        trade = {"traded_at":now,"portfolio":self.name,"ticker":ticker,"side":side,
                 "shares":shares,"price":fill,"fees":fees,"reason":reason}
        self.trades.append(trade)
        if store: store.save_trade(trade)
