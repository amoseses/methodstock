import json, sqlite3
from pathlib import Path
from datetime import datetime, timezone

class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY, scanned_at TEXT, ticker TEXT, price REAL,
            technical_score REAL, news_score REAL, combined_score REAL,
            signals_json TEXT, articles_json TEXT)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY, traded_at TEXT, portfolio TEXT, ticker TEXT,
            side TEXT, shares REAL, price REAL, fees REAL, reason TEXT)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS portfolio_state (
            name TEXT PRIMARY KEY, cash REAL NOT NULL, positions_json TEXT NOT NULL,
            updated_at TEXT NOT NULL)""")
        self.conn.commit()

    def save_scan(self, row):
        self.conn.execute("""INSERT INTO scans
        (scanned_at,ticker,price,technical_score,news_score,combined_score,signals_json,articles_json)
        VALUES (?,?,?,?,?,?,?,?)""", (
            row["scanned_at"], row["ticker"], row["price"], row["technical_score"],
            row["news_score"], row["combined_score"], json.dumps(row["signals"]),
            json.dumps(row["articles"], default=str)))
        self.conn.commit()

    def save_trade(self, trade):
        self.conn.execute("""INSERT INTO trades
        (traded_at,portfolio,ticker,side,shares,price,fees,reason)
        VALUES (?,?,?,?,?,?,?,?)""", tuple(trade[k] for k in
        ["traded_at","portfolio","ticker","side","shares","price","fees","reason"]))
        self.conn.commit()

    def load_portfolio_state(self, name):
        row = self.conn.execute(
            "SELECT cash, positions_json FROM portfolio_state WHERE name=?", (name,)
        ).fetchone()
        if not row:
            return None
        return {"cash": row[0], "positions": json.loads(row[1])}

    def save_portfolio_state(self, name, cash, positions):
        self.conn.execute(
            """INSERT INTO portfolio_state(name,cash,positions_json,updated_at)
               VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET
               cash=excluded.cash, positions_json=excluded.positions_json,
               updated_at=excluded.updated_at""",
            (name, cash, json.dumps(positions), datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()

    def scans(self):
        import pandas as pd
        return pd.read_sql_query("SELECT * FROM scans ORDER BY scanned_at DESC", self.conn)

    def trades(self):
        import pandas as pd
        return pd.read_sql_query("SELECT * FROM trades ORDER BY traded_at DESC", self.conn)

    def close(self): self.conn.close()
