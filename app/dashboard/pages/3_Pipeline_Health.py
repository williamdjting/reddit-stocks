"""
Pipeline Health page — run history, error logs, and data freshness monitoring.
"""
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Pipeline Health", page_icon="🔧", layout="wide")

STATUS_COLORS = {"success": "#22c55e", "partial": "#f97316", "failed": "#ef4444"}


@st.cache_data(ttl=300)
def load_pipeline_runs(limit: int = 30) -> pd.DataFrame:
    from db import get_client
    db = get_client()
    rows = (
        db.table("pipeline_runs")
        .select(
            "run_date,status,tickers_processed,apewisdom_records,scores_computed,"
            "tranches_updated,apewisdom_stale,errors,duration_ms,started_at,completed_at"
        )
        .order("run_date", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["run_date"] = pd.to_datetime(df["run_date"])
    df["duration_s"] = (df["duration_ms"] / 1000).round(1)
    return df


def main():
    st.title("🔧 Pipeline Health")

    runs_df = load_pipeline_runs()

    if runs_df.empty:
        st.warning("No pipeline runs found.")
        return

    latest = runs_df.iloc[0]
    st.subheader(f"Latest Run — {latest['run_date'].strftime('%Y-%m-%d')}")

    status_color = STATUS_COLORS.get(latest["status"], "#94a3b8")
    st.markdown(
        f"**Status:** <span style='color:{status_color};font-weight:bold'>{latest['status'].upper()}</span>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Apewisdom Records", int(latest["apewisdom_records"] or 0))
    c2.metric("Scores Computed", int(latest["scores_computed"] or 0))
    c3.metric("Tranches Updated", int(latest["tranches_updated"] or 0))
    c4.metric("Tickers Processed", int(latest["tickers_processed"] or 0))
    c5.metric("Duration", f"{latest['duration_s']}s")

    if latest.get("apewisdom_stale"):
        st.warning("⚠️ Apewisdom was stale on this run — used previous day's snapshot data.")

    errors = latest.get("errors") or []
    if errors:
        st.error(f"**{len(errors)} error(s) recorded:**")
        for err in errors:
            st.code(err)
    else:
        st.success("No errors recorded.")

    # ── Run history chart ─────────────────────────────────────────────────────
    st.subheader("Run History (Last 30 Days)")
    display_runs = runs_df.sort_values("run_date")

    fig = px.bar(
        display_runs,
        x="run_date",
        y="scores_computed",
        color="status",
        color_discrete_map=STATUS_COLORS,
        labels={"run_date": "Date", "scores_computed": "Tickers Scored"},
        title="Tickers Scored per Run",
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    fig_dur = px.line(
        display_runs,
        x="run_date",
        y="duration_s",
        labels={"run_date": "Date", "duration_s": "Duration (seconds)"},
        title="Pipeline Duration",
    )
    fig_dur.update_traces(line_color="#3b82f6")
    fig_dur.update_layout(height=250)
    st.plotly_chart(fig_dur, use_container_width=True)

    # ── Raw run log ───────────────────────────────────────────────────────────
    with st.expander("Raw Run Log"):
        table = runs_df[["run_date", "status", "apewisdom_records", "scores_computed", "tranches_updated", "duration_s", "apewisdom_stale"]].copy()
        table["run_date"] = table["run_date"].dt.strftime("%Y-%m-%d")
        st.dataframe(table, use_container_width=True, hide_index=True)

    # ── Data freshness check ──────────────────────────────────────────────────
    st.subheader("Data Freshness")
    from datetime import date
    today = date.today()
    last_run_date = runs_df["run_date"].max().date()
    days_stale = (today - last_run_date).days
    if days_stale == 0:
        st.success("✅ Data is current (ran today).")
    elif days_stale == 1:
        st.info(f"ℹ️ Last run was yesterday ({last_run_date}).")
    else:
        st.error(f"🚨 Data is {days_stale} days stale. Last run: {last_run_date}. Check GitHub Actions.")


main()
