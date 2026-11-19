import json
import sys
from pathlib import Path

# Make the project's src/ package importable when Streamlit runs this file
# directly from the dashboard/ subdirectory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
import plotly.express as px
import streamlit as st

from stock_intelligence.config import settings
from stock_intelligence.pipeline import run_scan

st.set_page_config(page_title="Stock Intelligence", layout="wide")
st.title("Stock Intelligence")
st.caption("Current market/news research • Local paper portfolios • Not investment advice")

if st.button("Run current stock scan", type="primary"):
    with st.spinner("Fetching market data and news, then scoring stocks..."):
        try:
            result = run_scan()
            st.success(f"Scan complete: {len(result['results'])} stocks analyzed.")
        except Exception as e:
            st.error(str(e))

p = Path(settings.reports_dir) / "latest_scan.json"
if p.exists():
    data = json.loads(p.read_text())
    st.caption(f"Last scan: {data['scanned_at']}")
    if data["results"]:
        df = pd.DataFrame([{
            "Ticker": r["ticker"],
            "Price": r["price"],
            "Technical": r["technical_score"],
            "News": r["news_score"],
            "Combined": r["combined_score"],
            "Signal": r["signals"]["combined"]["decision"],
            "News status": r["news_status"],
        } for r in data["results"]])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.plotly_chart(
            px.bar(df, x="Ticker", y="Combined", title="Combined signal scores"),
            use_container_width=True,
        )
        ticker = st.selectbox("Inspect ticker", df["Ticker"].tolist())
        item = next(r for r in data["results"] if r["ticker"] == ticker)
        st.subheader(f"{ticker} — {item['signals']['combined']['decision']}")
        st.write("Technical rationale:", ", ".join(item["technical_reasons"]))
        st.write("News status:", item["news_status"])
        st.subheader("Recent articles")
        if item["articles"]:
            for article in item["articles"]:
                st.markdown(
                    f"**{article['headline']}**  \n"
                    f"{article.get('source', '')} · {article.get('published_at', '')}  \n"
                    f"{article.get('summary', '')[:600]}  \n"
                    f"[Open article]({article.get('url', '')})"
                )
        else:
            st.info("No current articles returned. Check your news provider/API key.")
    if data.get("errors"):
        st.warning(f"{len(data['errors'])} tickers had data errors.")
else:
    st.info("No scan yet. Configure .env and click Run current stock scan.")
