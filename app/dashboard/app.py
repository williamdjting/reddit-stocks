"""
Tranche Overview — main dashboard page.

Shows all active tickers grouped by current tranche with key metrics.
"""
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Reddit Pre-Breakout Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

TRANCHE_ORDER = ["pre_pop", "early", "seed", "unclassified", "insufficient_data", "noise"]
TRANCHE_LABELS = {
    "pre_pop": "🚀 Pre-Pop (Tier 3)",
    "early": "📈 Early (Tier 2)",
    "seed": "🌱 Seed (Tier 1)",
    "unclassified": "❓ Unclassified",
    "insufficient_data": "⏳ Insufficient Data",
    "noise": "🚫 Noise",
}
TRANCHE_COLORS = {
    "pre_pop": "#ef4444",
    "early": "#f97316",
    "seed": "#22c55e",
    "unclassified": "#94a3b8",
    "insufficient_data": "#64748b",
    "noise": "#475569",
}


@st.cache_data(ttl=3600)
def load_latest_stats() -> pd.DataFrame:
    from db import get_client
    db = get_client()
    rows = (
        db.table("ticker_daily_stats")
        .select(
            "ticker,stat_date,tranche,days_in_dataset,"
            "mention_count_1w,mention_count_1mo,mention_count_3mo,"
            "velocity_1w_vs_1mo,velocity_1mo_vs_3mo,velocity_3mo_vs_6mo,velocity_6mo_vs_1y,"
            "acceleration,subreddit_spread"
        )
        .order("stat_date", desc=True)
        .limit(5000)
        .execute()
        .data
    )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["stat_date"] = pd.to_datetime(df["stat_date"])
    latest = df["stat_date"].max()
    return df[df["stat_date"] == latest].copy()


@st.cache_data(ttl=3600)
def load_ticker_meta() -> pd.DataFrame:
    from db import get_client
    db = get_client()
    rows = db.table("tickers").select("symbol,market_cap,sector,current_tranche").execute().data
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def format_market_cap(cap: float | None) -> str:
    if cap is None:
        return "—"
    if cap >= 1_000_000_000:
        return f"${cap / 1_000_000_000:.1f}B"
    if cap >= 1_000_000:
        return f"${cap / 1_000_000:.0f}M"
    return f"${cap:,.0f}"


def format_velocity(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:.2f}x"


def main():
    st.title("📈 Reddit Pre-Breakout Monitor")

    try:
        stats_df = load_latest_stats()
        meta_df = load_ticker_meta()
    except EnvironmentError as e:
        st.error(str(e))
        st.stop()

    if stats_df.empty:
        st.warning("No data found. Run the pipeline first.")
        return

    stat_date = stats_df["stat_date"].iloc[0]
    st.caption(f"Data as of **{stat_date.strftime('%Y-%m-%d')}** · {len(stats_df)} tickers tracked")

    # ── Summary metrics ──────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    tranche_counts = stats_df["tranche"].value_counts()
    col1.metric("🚀 Pre-Pop", tranche_counts.get("pre_pop", 0))
    col2.metric("📈 Early", tranche_counts.get("early", 0))
    col3.metric("🌱 Seed", tranche_counts.get("seed", 0))
    col4.metric("Total Tickers", len(stats_df))

    # ── Tranche distribution chart ────────────────────────────────────────────
    st.subheader("Tranche Distribution")
    dist = (
        stats_df["tranche"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "tranche", "tranche": "count"})
    )
    dist.columns = ["tranche", "count"]
    dist["label"] = dist["tranche"].map(TRANCHE_LABELS).fillna(dist["tranche"])
    dist["color"] = dist["tranche"].map(TRANCHE_COLORS).fillna("#94a3b8")
    fig = px.bar(
        dist,
        x="label",
        y="count",
        color="tranche",
        color_discrete_map=TRANCHE_COLORS,
        labels={"label": "Tranche", "count": "Ticker Count"},
    )
    fig.update_layout(showlegend=False, height=300)
    st.plotly_chart(fig, use_container_width=True)

    # ── Tranche tables ────────────────────────────────────────────────────────
    if not meta_df.empty:
        merged = stats_df.merge(meta_df, left_on="ticker", right_on="symbol", how="left")
    else:
        merged = stats_df.copy()
        merged["market_cap"] = None
        merged["sector"] = None

    for tranche in ["pre_pop", "early", "seed"]:
        subset = merged[merged["tranche"] == tranche].copy()
        if subset.empty:
            continue

        st.subheader(TRANCHE_LABELS[tranche])
        subset = subset.sort_values("mention_count_1w", ascending=False)

        display = pd.DataFrame(
            {
                "Ticker": subset["ticker"],
                "Mentions (1W)": subset["mention_count_1w"].fillna(0).astype(int),
                "Mentions (1Mo)": subset["mention_count_1mo"].fillna(0).astype(int),
                "Vel 1W/1Mo": subset["velocity_1w_vs_1mo"].apply(format_velocity),
                "Vel 1Mo/3Mo": subset["velocity_1mo_vs_3mo"].apply(format_velocity),
                "Subreddit Spread": subset["subreddit_spread"].fillna("—"),
                "Days in Dataset": subset["days_in_dataset"],
                "Market Cap": subset["market_cap"].apply(format_market_cap),
                "Sector": subset["sector"].fillna("—"),
            }
        )
        st.dataframe(display, use_container_width=True, hide_index=True)

    with st.expander("Unclassified & Noise"):
        others = merged[merged["tranche"].isin(["unclassified", "insufficient_data", "noise"])].copy()
        if not others.empty:
            others = others.sort_values(["tranche", "mention_count_1w"], ascending=[True, False])
            display = pd.DataFrame(
                {
                    "Ticker": others["ticker"],
                    "Tranche": others["tranche"],
                    "Mentions (1W)": others["mention_count_1w"].fillna(0).astype(int),
                    "Days in Dataset": others["days_in_dataset"],
                }
            )
            st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.write("None")


main()
