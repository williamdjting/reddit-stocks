"""
Daily Digest page — new tranche entries and significant velocity moves from the latest run.
"""
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Daily Digest", page_icon="📋", layout="wide")

ACTIONABLE_TRANCHES = ["pre_pop", "early", "seed"]


@st.cache_data(ttl=3600)
def load_recent_transitions(days: int = 7) -> pd.DataFrame:
    from db import get_client
    from datetime import date, timedelta
    db = get_client()
    cutoff = str(date.today() - timedelta(days=days))
    rows = (
        db.table("ticker_tranche_log")
        .select("ticker,tranche,previous_tranche,entered_at,velocity_at_entry,mention_count_at_entry,market_cap_at_entry")
        .gte("entered_at", cutoff)
        .in_("tranche", ACTIONABLE_TRANCHES)
        .order("entered_at", desc=True)
        .execute()
        .data
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


@st.cache_data(ttl=3600)
def load_top_movers(stat_date_str: str) -> pd.DataFrame:
    from db import get_client
    db = get_client()
    rows = (
        db.table("ticker_daily_stats")
        .select("ticker,tranche,mention_count_1w,velocity_1w_vs_1mo,velocity_1mo_vs_3mo,subreddit_spread")
        .eq("stat_date", stat_date_str)
        .in_("tranche", ACTIONABLE_TRANCHES)
        .order("velocity_1w_vs_1mo", desc=True)
        .limit(20)
        .execute()
        .data
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


@st.cache_data(ttl=3600)
def load_latest_stat_date() -> str | None:
    from db import get_client
    db = get_client()
    rows = (
        db.table("ticker_daily_stats")
        .select("stat_date")
        .order("stat_date", desc=True)
        .limit(1)
        .execute()
        .data
    )
    return rows[0]["stat_date"] if rows else None


def format_market_cap(cap) -> str:
    if cap is None:
        return "—"
    cap = float(cap)
    if cap >= 1_000_000_000:
        return f"${cap / 1_000_000_000:.1f}B"
    if cap >= 1_000_000:
        return f"${cap / 1_000_000:.0f}M"
    return f"${cap:,.0f}"


def main():
    st.title("📋 Daily Digest")

    latest_date = load_latest_stat_date()
    if not latest_date:
        st.warning("No pipeline data found.")
        return

    st.caption(f"Most recent pipeline run: **{latest_date}**")

    lookback = st.sidebar.slider("Transition lookback (days)", min_value=1, max_value=30, value=7)

    # ── New tranche entries ───────────────────────────────────────────────────
    st.subheader("🆕 New Tranche Entries")
    transitions_df = load_recent_transitions(days=lookback)

    if transitions_df.empty:
        st.info(f"No new actionable tranche entries in the last {lookback} days.")
    else:
        transitions_df["entered_at"] = pd.to_datetime(transitions_df["entered_at"]).dt.strftime("%Y-%m-%d")
        transitions_df["market_cap_at_entry"] = transitions_df["market_cap_at_entry"].apply(format_market_cap)
        transitions_df["velocity_at_entry"] = transitions_df["velocity_at_entry"].apply(
            lambda v: f"{v:.2f}x" if v is not None else "—"
        )
        transitions_df["mention_count_at_entry"] = transitions_df["mention_count_at_entry"].fillna(0).astype(int)

        display = transitions_df.rename(
            columns={
                "ticker": "Ticker",
                "tranche": "New Tranche",
                "previous_tranche": "Previous Tranche",
                "entered_at": "Date",
                "velocity_at_entry": "Velocity at Entry",
                "mention_count_at_entry": "Mentions (1W)",
                "market_cap_at_entry": "Market Cap",
            }
        )
        st.dataframe(display, use_container_width=True, hide_index=True)

    # ── Top velocity movers ───────────────────────────────────────────────────
    st.subheader("⚡ Top Velocity Movers (Today)")
    movers_df = load_top_movers(latest_date)

    if movers_df.empty:
        st.info("No actionable tickers in today's data.")
    else:
        movers_df["velocity_1w_vs_1mo"] = movers_df["velocity_1w_vs_1mo"].apply(
            lambda v: f"{v:.2f}x" if v is not None else "—"
        )
        movers_df["velocity_1mo_vs_3mo"] = movers_df["velocity_1mo_vs_3mo"].apply(
            lambda v: f"{v:.2f}x" if v is not None else "—"
        )
        movers_df["mention_count_1w"] = movers_df["mention_count_1w"].fillna(0).astype(int)
        movers_df["subreddit_spread"] = movers_df["subreddit_spread"].fillna("—")
        display = movers_df.rename(
            columns={
                "ticker": "Ticker",
                "tranche": "Tranche",
                "mention_count_1w": "Mentions (1W)",
                "velocity_1w_vs_1mo": "Vel 1W/1Mo",
                "velocity_1mo_vs_3mo": "Vel 1Mo/3Mo",
                "subreddit_spread": "Subreddit Spread",
            }
        )
        st.dataframe(display, use_container_width=True, hide_index=True)


main()
