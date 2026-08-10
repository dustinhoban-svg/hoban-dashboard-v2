import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from data.market_data import get_market_data
from data.fred_data import get_fred_data, get_fred_history
from data.snapshots import init_db, save_daily_snapshot, load_snapshot_history

init_db()

st.set_page_config(
    page_title="Hoban Financial Terminal",
    layout="wide"
)

st.title("📊 Hoban Financial Terminal")
st.caption("Market Pulse v0.3")

# --- Fetch data once ---
market = get_market_data()
fred_data = get_fred_data()

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

bs = fred_data.get("Fed Balance Sheet")
rrp = fred_data.get("Reverse Repo")
tga = fred_data.get("Treasury General Account")
ff = fred_data.get("Fed Funds Rate")
y10 = fred_data.get("10Y Treasury")
y2 = fred_data.get("2Y Treasury")
hy_spread = fred_data.get("High Yield Credit Spread")
breakeven = fred_data.get("10Y Breakeven Inflation")
cpi = fred_data.get("CPI")
unemployment = fred_data.get("Unemployment Rate")
claims = fred_data.get("Initial Jobless Claims")

if y10 is not None and y2 is not None:
    spread = (y10 - y2) * 100
    curve_label = "🟢 Steepening" if spread > 0 else "🔴 Inverted"
else:
    spread = None
    curve_label = "Unknown"

save_daily_snapshot(fred_data, vix)

# --- Sidebar controls ---
st.sidebar.header("Trend Chart Controls")
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
selected_label = st.sidebar.selectbox("Choose an indicator", list(trend_series_options.keys()))
default_start = date.today() - timedelta(days=365)
date_range = st.sidebar.date_input(
    "Date range",
    value=(default_start, date.today()),
    max_value=date.today()
)

# --- Tabs ---
tab_overview, tab_macro, tab_real, tab_trends, tab_history = st.tabs(
    ["Overview", "Macro Detail", "Real Rates", "Trends", "Snapshot History"]
)

with tab_overview:
    st.subheader("Overall Read")
    st.write(f"**{regime} equity risk conditions, {curve_label if spread is not None else 'curve data unavailable'}**")

    if bs is not None and rrp is not None and tga is not None:
        net_liquidity = bs - rrp - tga
        st.write(f"**Net Liquidity (Fed BS − RRP − TGA):** ${net_liquidity/1e6:.2f}T")
        st.caption("Rising net liquidity tends to support risk assets; falling net liquidity tends to pressure them.")
    else:
        st.write("Net liquidity: insufficient data")

    if spread is not None:
        if spread < 0:
            st.write("🔴 **Yield curve inverted** — historically a recession signal, though lead time varies widely (6-24 months).")
        elif spread < 50:
            st.write("🟡 **Yield curve flat/mildly positive** — market pricing modest growth expectations.")
        else:
            st.write("🟢 **Yield curve steep** — market pricing stronger growth or inflation expectations ahead.")

    st.divider()
    st.subheader("Market Snapshot")
    cols = st.columns(3)
    for i, (name, price) in enumerate(market.items()):
        value = f"{price:.2f}" if price is not None else "Unavailable"
        cols[i % 3].metric(name, value)

    st.divider()
    st.metric("Current Environment", regime)

with tab_macro:
    st.subheader("Macro Environment")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Liquidity**")
        st.metric("Fed Balance Sheet", f"${bs/1e6:.2f}T" if bs else "N/A")
        st.metric("Reverse Repo", f"${rrp:.0f}B" if rrp else "N/A")
        st.metric("TGA", f"${tga:.0f}B" if tga else "N/A")
    with col2:
        st.markdown("**Rates**")
        st.metric("Fed Funds", f"{ff:.2f}%" if ff else "N/A")
        st.metric("10Y", f"{y10:.2f}%" if y10 else "N/A")
        st.metric("2Y", f"{y2:.2f}%" if y2 else "N/A")
    with col3:
        st.markdown("**Curve**")
        if spread is not None:
            st.metric("2s10s Spread", f"{spread:+.0f} bps", delta=curve_label)
        else:
            st.metric("2s10s Spread", "N/A")

    st.divider()
    st.subheader("Credit, Inflation & Labor")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("**Credit**")
        st.metric("HY Credit Spread", f"{hy_spread:.2f}%" if hy_spread else "N/A")
        st.caption("Widening = credit stress / risk-off. Tightening = risk-on.")
    with col5:
        st.markdown("**Inflation**")
        st.metric("10Y Breakeven", f"{breakeven:.2f}%" if breakeven else "N/A")
        st.metric("CPI Index", f"{cpi:.1f}" if cpi else "N/A")
    with col6:
        st.markdown("**Labor**")
        st.metric("Unemployment", f"{unemployment:.1f}%" if unemployment else "N/A")
        st.metric("Jobless Claims", f"{claims:,.0f}" if claims else "N/A")

with tab_trends:
    st.subheader("Historical Trends")
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

with tab_real:
    st.subheader("Real Rates")

    real_5y = fred_data.get("5Y Real Rate")
    real_10y = fred_data.get("10Y Real Rate")
    real_20y = fred_data.get("20Y Real Rate")
    real_30y = fred_data.get("30Y Real Rate")
    breakeven_5y = fred_data.get("5Y Breakeven Inflation")
    breakeven_10y = fred_data.get("10Y Breakeven Inflation")

    st.markdown("**Real Yield Curve**")
    rcol1, rcol2, rcol3, rcol4 = st.columns(4)
    rcol1.metric("5Y Real", f"{real_5y:.2f}%" if real_5y is not None else "N/A")
    rcol2.metric("10Y Real", f"{real_10y:.2f}%" if real_10y is not None else "N/A")
    rcol3.metric("20Y Real", f"{real_20y:.2f}%" if real_20y is not None else "N/A")
    rcol4.metric("30Y Real", f"{real_30y:.2f}%" if real_30y is not None else "N/A")

    st.divider()
    st.markdown("**Nominal = Real + Breakeven Inflation**")
    acol1, acol2 = st.columns(2)
    with acol1:
        st.write("**5Y**")
        if real_5y is not None and breakeven_5y is not None:
            st.write(f"Nominal ≈ {real_5y + breakeven_5y:.2f}% (Real {real_5y:.2f}% + Breakeven {breakeven_5y:.2f}%)")
        else:
            st.write("Insufficient data")
    with acol2:
        st.write("**10Y**")
        if real_10y is not None and breakeven_10y is not None:
            st.write(f"Nominal ≈ {real_10y + breakeven_10y:.2f}% (Real {real_10y:.2f}% + Breakeven {breakeven_10y:.2f}%)")
        else:
            st.write("Insufficient data")

    st.divider()
    st.markdown("**Real Rate Curve Slope (30Y − 5Y)**")
    if real_30y is not None and real_5y is not None:
        real_spread = (real_30y - real_5y) * 100
        slope_label = "Steepening" if real_spread > 0 else "Flattening/Inverted"
        st.metric("Real 30Y-5Y Spread", f"{real_spread:+.0f} bps", delta=slope_label)
        st.caption("A steep real curve prices stronger long-run growth expectations net of inflation; a flat/inverted real curve suggests the market sees weaker growth ahead.")
    else:
        st.write("Insufficient data for real curve slope")

with tab_history:
    st.subheader("Snapshot History")
    history_df = load_snapshot_history()
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.write("No snapshots saved yet.")
