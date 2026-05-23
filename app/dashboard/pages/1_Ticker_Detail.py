"""
Ticker Detail page — velocity trend, mention history, and tranche log for a single ticker.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Ticker Detail", page_icon="🔍", layout="wide")


@st.cache_data(ttl=3600)
def load_ticker_stats(symbol: str) -> pd.DataFrame:
    from db import get_client
    db = get_client()
    rows = (
        db.table("ticker_daily_stats")
        .select(
            "stat_date,tranche,days_in_dataset,"
            "mention_count_1w,mention_count_1mo,mention_count_3mo,"
            "velocity_1w_vs_1mo,velocity_1mo_vs_3mo,velocity_3mo_vs_6mo,velocity_6mo_vs_1y,"
            "acceleration,subreddit_spread"
        )
        .eq("ticker", symbol)
        .order("stat_date", desc=False)
        .execute()
        .data
    )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["stat_date"] = pd.to_datetime(df["stat_date"])
    return df


@st.cache_data(ttl=3600)
def load_tranche_log(symbol: str) -> pd.DataFrame:
    from db import get_client
    db = get_client()
    rows = (
        db.table("ticker_tranche_log")
        .select("tranche,previous_tranche,entered_at,exited_at,velocity_at_entry,mention_count_at_entry,market_cap_at_entry")
        .eq("ticker", symbol)
        .order("entered_at", desc=False)
        .execute()
        .data
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


@st.cache_data(ttl=3600)
def load_all_symbols() -> list[str]:
    from db import get_client
    db = get_client()
    rows = db.table("tickers").select("symbol").eq("is_active", True).order("symbol").execute().data
    return [r["symbol"] for r in rows] if rows else []


def main():
    st.title("🔍 Ticker Detail")

    symbols = load_all_symbols()
    if not symbols:
        st.warning("No tickers found. Run the pipeline first.")
        return

    query_symbol = st.query_params.get("ticker", "")
    default_idx = symbols.index(query_symbol) if query_symbol in symbols else 0

    symbol = st.selectbox("Select ticker", symbols, index=default_idx)

    if not symbol:
        return

    stats_df = load_ticker_stats(symbol)
    if stats_df.empty:
        st.warning(f"No stats found for {symbol}.")
        return

    latest = stats_df.iloc[-1]
    st.subheader(f"{symbol} — {latest['tranche'].replace('_', ' ').title()}")

    # ── Key metrics ───────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Days in Dataset", int(latest["days_in_dataset"] or 0))
    c2.metric("Mentions (1W)", int(latest["mention_count_1w"] or 0))
    c3.metric("Vel 1W/1Mo", f"{latest['velocity_1w_vs_1mo']:.2f}x" if latest["velocity_1w_vs_1mo"] else "—")
    c4.metric("Vel 1Mo/3Mo", f"{latest['velocity_1mo_vs_3mo']:.2f}x" if latest["velocity_1mo_vs_3mo"] else "—")
    c5.metric("Subreddit Spread", int(latest["subreddit_spread"]) if latest["subreddit_spread"] else "—")

    # ── Mention count history ─────────────────────────────────────────────────
    st.subheader("Weekly Mention Count History")
    fig_mentions = px.line(
        stats_df,
        x="stat_date",
        y="mention_count_1w",
        labels={"stat_date": "Date", "mention_count_1w": "Mentions (1W)"},
    )
    fig_mentions.update_traces(line_color="#3b82f6")
    fig_mentions.update_layout(height=300)
    st.plotly_chart(fig_mentions, use_container_width=True)

    # ── Velocity trend ────────────────────────────────────────────────────────
    st.subheader("Velocity Trends")
    vel_df = stats_df[["stat_date", "velocity_1w_vs_1mo", "velocity_1mo_vs_3mo", "velocity_3mo_vs_6mo", "velocity_6mo_vs_1y"]].dropna(
        subset=["velocity_1w_vs_1mo"], how="all"
    )
    fig_vel = go.Figure()
    vel_series = [
        ("velocity_1w_vs_1mo", "1W vs 1Mo", "#ef4444"),
        ("velocity_1mo_vs_3mo", "1Mo vs 3Mo", "#f97316"),
        ("velocity_3mo_vs_6mo", "3Mo vs 6Mo", "#22c55e"),
        ("velocity_6mo_vs_1y", "6Mo vs 1Y", "#3b82f6"),
    ]
    for col, name, color in vel_series:
        subset = vel_df.dropna(subset=[col])
        if not subset.empty:
            fig_vel.add_trace(
                go.Scatter(
                    x=subset["stat_date"],
                    y=subset[col],
                    name=name,
                    line=dict(color=color),
                )
            )
    fig_vel.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Baseline (1.0x)")
    fig_vel.update_layout(height=350, yaxis_title="Velocity (x)", xaxis_title="Date")
    st.plotly_chart(fig_vel, use_container_width=True)

    # ── Tranche history ───────────────────────────────────────────────────────
    st.subheader("Tranche History")
    log_df = load_tranche_log(symbol)
    if log_df.empty:
        st.info("No tranche transitions recorded yet.")
    else:
        st.dataframe(
            log_df.rename(
                columns={
                    "tranche": "New Tranche",
                    "previous_tranche": "From Tranche",
                    "entered_at": "Entered",
                    "exited_at": "Exited",
                    "velocity_at_entry": "Velocity at Entry",
                    "mention_count_at_entry": "Mentions at Entry",
                    "market_cap_at_entry": "Market Cap at Entry",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


main()
