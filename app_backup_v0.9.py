import streamlit as st
from data.market_data import get_market_data
from data.fred_data import get_fred_data
from data.snapshots import init_db, save_daily_snapshot, load_snapshot_history

init_db()
st.set_page_config(
    page_title="Hoban Financial Terminal",
    layout="wide"
)

st.title("📊 Hoban Financial Terminal")
st.caption("Market Pulse v0.3")

market = get_market_data()

st.subheader("Market Snapshot")

cols = st.columns(3)

for i, (name, price) in enumerate(market.items()):

    if price is not None:
        value = f"{price:.2f}"
    else:
        value = "Unavailable"

    cols[i % 3].metric(
        name,
        value
    )


st.divider()

st.subheader("Market Regime")

vix = market.get("VIX")

if vix is not None:
    if vix < 20:
        regime = "🟢 Risk On"
    elif vix > 30:
        regime = "🔴 Risk Off"
    else:
        regime = "🟡 Neutral"
else:
    regime = "Unknown"

st.metric(
    "Current Environment",
    regime
)
st.divider()
st.subheader("Macro Environment")

fred_data = get_fred_data()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Liquidity**")
    bs = fred_data.get("Fed Balance Sheet")
    rrp = fred_data.get("Reverse Repo")
    tga = fred_data.get("Treasury General Account")
    st.metric("Fed Balance Sheet", f"${bs/1e6:.2f}T" if bs else "N/A")
    st.metric("Reverse Repo", f"${rrp:.0f}B" if rrp else "N/A")
    st.metric("TGA", f"${tga:.0f}B" if tga else "N/A")

with col2:
    st.markdown("**Rates**")
    ff = fred_data.get("Fed Funds Rate")
    y10 = fred_data.get("10Y Treasury")
    y2 = fred_data.get("2Y Treasury")
    st.metric("Fed Funds", f"{ff:.2f}%" if ff else "N/A")
    st.metric("10Y", f"{y10:.2f}%" if y10 else "N/A")
    st.metric("2Y", f"{y2:.2f}%" if y2 else "N/A")

with col3:
    st.markdown("**Curve**")
    if y10 is not None and y2 is not None:
        spread = (y10 - y2) * 100
        curve_label = "🟢 Steepening" if spread > 0 else "🔴 Inverted"
        st.metric("2s10s Spread", f"{spread:+.0f} bps", delta=curve_label)
    else:
        spread = None
        st.metric("2s10s Spread", "N/A")
st.subheader("Credit, Inflation & Labor")
col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("**Credit**")
    hy_spread = fred_data.get("High Yield Credit Spread")
    st.metric("HY Credit Spread", f"{hy_spread:.2f}%" if hy_spread else "N/A")
    st.caption("Widening = credit stress / risk-off. Tightening = risk-on.")

with col5:
    st.markdown("**Inflation**")
    breakeven = fred_data.get("10Y Breakeven Inflation")
    cpi = fred_data.get("CPI")
    st.metric("10Y Breakeven", f"{breakeven:.2f}%" if breakeven else "N/A")
    st.metric("CPI Index", f"{cpi:.1f}" if cpi else "N/A")

with col6:
    st.markdown("**Labor**")
    unemployment = fred_data.get("Unemployment Rate")
    claims = fred_data.get("Initial Jobless Claims")
    st.metric("Unemployment", f"{unemployment:.1f}%" if unemployment else "N/A")
    st.metric("Jobless Claims", f"{claims:,.0f}" if claims else "N/A")

st.divider()
st.subheader("Interpretation")

# Liquidity trend (simple version: is the balance sheet growing or shrinking
# relative to reverse repo + TGA draining reserves)
if bs is not None and rrp is not None and tga is not None:
    net_liquidity = bs - rrp - tga
    st.write(f"**Net Liquidity (Fed BS − RRP − TGA):** ${net_liquidity/1e6:.2f}T")
    st.caption("Rising net liquidity tends to support risk assets; falling net liquidity tends to pressure them.")
else:
    st.write("Net liquidity: insufficient data")

# Curve interpretation
if spread is not None:
    if spread < 0:
        st.write("🔴 **Yield curve inverted** — historically a recession signal, though lead time varies widely (6-24 months).")
    elif spread < 50:
        st.write("🟡 **Yield curve flat/mildly positive** — market pricing modest growth expectations.")
    else:
        st.write("🟢 **Yield curve steep** — market pricing stronger growth or inflation expectations ahead.")

# Combine with existing VIX-based regime for a single risk read
st.divider()
st.write(f"**Overall Read:** {regime} equity risk conditions, {curve_label if spread is not None else 'curve data unavailable'}")

save_daily_snapshot(fred_data, vix)

st.divider()
st.subheader("Snapshot History")
history_df = load_snapshot_history()
if not history_df.empty:
    st.dataframe(history_df, use_container_width=True)
else:
    st.write("No snapshots saved yet.")


st.divider()
st.subheader("Historical Trends")

import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from data.fred_data import get_fred_history

trend_series_options = {
    "Fed Balance Sheet": "WALCL",
    "Reverse Repo": "RRPONTSYD",
    "Treasury General Account": "WTREGEN",
    "Fed Funds Rate": "FEDFUNDS",
    "10Y Treasury": "DGS10",
    "2Y Treasury": "DGS2",
    "High Yield Credit Spread": "BAMLH0A0HYM2",
    "CPI": "CPIAUCSL",
    "10Y Breakeven Inflation": "T10YIE",
    "Unemployment Rate": "UNRATE",
    "Initial Jobless Claims": "ICSA"
}

selected_label = st.selectbox("Choose an indicator", list(trend_series_options.keys()))

default_start = date.today() - timedelta(days=365)
date_range = st.date_input(
    "Date range",
    value=(default_start, date.today()),
    max_value=date.today()
)

if len(date_range) == 2:
    start, end = date_range
    series_id = trend_series_options[selected_label]
    history = get_fred_history(series_id, start_date=str(start), end_date=str(end))

    if not history.empty:
        df = history.reset_index()
        df.columns = ["Date", selected_label]
        fig = px.line(df, x="Date", y=selected_label, title=f"{selected_label} Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No data available for this range.")

