import os
import psycopg2
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="MacroLens",
    page_icon="📊",
    layout="wide"
)

@st.cache_data(ttl=3600)
def load_data():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "macrolens"),
        user=os.getenv("POSTGRES_USER", os.environ.get("USER")),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )
    df = pd.read_sql("SELECT * FROM mart_sector_performance ORDER BY date", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

# ── Sidebar ──
st.sidebar.title("MacroLens")
st.sidebar.markdown("S&P 500 Sector Intelligence Pipeline")

sectors = sorted(df["sector"].unique())
selected_sectors = st.sidebar.multiselect("Sectors", sectors, default=sectors)

regimes = sorted(df["macro_regime"].unique())
selected_regimes = st.sidebar.multiselect("Macro Regime", regimes, default=regimes)

date_min = df["date"].min().date()
date_max = df["date"].max().date()
date_range = st.sidebar.date_input("Date Range", value=(date_min, date_max))

# ── Filter ──
filtered = df[
    (df["sector"].isin(selected_sectors)) &
    (df["macro_regime"].isin(selected_regimes)) &
    (df["date"] >= pd.Timestamp(date_range[0])) &
    (df["date"] <= pd.Timestamp(date_range[1]))
]

# ── Header ──
st.title("MacroLens: S&P 500 Sector Intelligence")
st.markdown("Analyzing how macroeconomic conditions drive sector performance across market cycles.")

# ── KPI Row ──
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Trading Days", f"{len(filtered):,}")
col2.metric("Sectors Tracked", filtered["sector"].nunique())
col3.metric("Avg Daily Return", f"{filtered['daily_return_pct'].mean():.3f}%")
col4.metric("Current Macro Regime", filtered.sort_values("date")["macro_regime"].iloc[-1].title() if len(filtered) > 0 else "N/A")

st.divider()

# ── Chart 1: Daily Returns by Sector ──
st.subheader("Daily Returns by Sector")
fig1 = px.line(
    filtered,
    x="date",
    y="rolling_30d_avg_return",
    color="sector",
    title="30-Day Rolling Average Return by Sector",
    labels={"rolling_30d_avg_return": "30D Avg Return (%)", "date": "Date"}
)
fig1.update_layout(hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Sector Performance by Macro Regime ──
st.subheader("Sector Performance by Macro Regime")
regime_perf = filtered.groupby(["sector", "macro_regime"])["daily_return_pct"].mean().reset_index()
fig2 = px.bar(
    regime_perf,
    x="sector",
    y="daily_return_pct",
    color="macro_regime",
    barmode="group",
    title="Average Daily Return by Sector and Macro Regime",
    labels={"daily_return_pct": "Avg Daily Return (%)", "sector": "Sector"}
)
st.plotly_chart(fig2, use_container_width=True)

# ── Chart 3: Fed Funds Rate Over Time ──
st.subheader("Macro Indicators")
macro_df = df[["date", "fed_funds_rate", "cpi", "unemployment_rate", "yield_spread_10y2y"]].drop_duplicates("date")
fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=macro_df["date"], y=macro_df["fed_funds_rate"], name="Fed Funds Rate", line=dict(color="#EF553B")))
fig3.add_trace(go.Scatter(x=macro_df["date"], y=macro_df["yield_spread_10y2y"], name="Yield Spread 10Y-2Y", line=dict(color="#636EFA")))
fig3.update_layout(title="Fed Funds Rate vs Yield Spread", hovermode="x unified")
st.plotly_chart(fig3, use_container_width=True)

# ── Chart 4: Regime Distribution ──
st.subheader("Macro Regime Distribution")
regime_counts = filtered.groupby("macro_regime")["date"].nunique().reset_index()
regime_counts.columns = ["macro_regime", "trading_days"]
fig4 = px.pie(
    regime_counts,
    names="macro_regime",
    values="trading_days",
    title="Trading Days by Macro Regime"
)
st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.caption("Data: Alpha Vantage (sector ETF prices) + FRED (macroeconomic indicators) · Pipeline: Airflow + dbt + PostgreSQL")