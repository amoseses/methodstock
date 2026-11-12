import pandas as pd
from stock_intelligence.indicators import add_indicators

def test_indicators_columns():
    idx=pd.date_range("2025-01-01",periods=40,freq="D")
    df=pd.DataFrame({"open":range(10,50),"high":range(11,51),"low":range(9,49),
                     "close":range(10,50),"volume":[1000]*40},index=idx)
    x=add_indicators(df)
    for col in ("ema9","ema21","rsi","vwap","volume_ratio"):
        assert col in x.columns
