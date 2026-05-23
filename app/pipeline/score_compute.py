"""
Stage 4 — Scoring engine.

For each active ticker, reads all apewisdom_snapshots and computes:
  - days_in_dataset   (from tickers.first_seen_at)
  - rolling mention counts across 7 windows (NULL when data is unavailable)
  - velocity ratios across adjacent window pairs
  - acceleration (change in velocity)
  - subreddit_spread (from raw_mentions if available)

Upserts one row per ticker into ticker_daily_stats.

apewisdom_snapshot_date is set to the most recent snapshot_date used,
which differs from stat_date when Apewisdom was stale.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

import pandas as pd

from pipeline.config import WEEKS_IN_WINDOW, compute_acceleration, compute_velocity
from pipeline.db import get_client

log = logging.getLogger(__name__)

WINDOW_DAYS: dict[str, int] = {
    "1w": 7,
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "18mo": 548,
    "2y": 730,
}

VELOCITY_PAIRS = [
    ("1w", "1mo"),
    ("1mo", "3mo"),
    ("3mo", "6mo"),
    ("6mo", "1y"),
]


@dataclass
class StageResult:
    scores_computed: int = 0
    errors: list[str] = field(default_factory=list)


def _load_snapshots(db) -> pd.DataFrame:
    rows = db.table("apewisdom_snapshots").select("ticker,snapshot_date,mention_count_24h").execute().data
    if not rows:
        return pd.DataFrame(columns=["ticker", "snapshot_date", "mention_count_24h"])
    df = pd.DataFrame(rows)
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"]).dt.date
    df["mention_count_24h"] = pd.to_numeric(df["mention_count_24h"], errors="coerce").fillna(0).astype(int)
    return df


def _load_tickers(db) -> pd.DataFrame:
    rows = (
        db.table("tickers")
        .select("symbol,first_seen_at,market_cap,is_active")
        .eq("is_active", True)
        .execute()
        .data
    )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["first_seen_at"] = pd.to_datetime(df["first_seen_at"]).dt.date
    return df


def _rolling_count(
    ticker_df: pd.DataFrame, stat_date: date, days: int, days_in_dataset: int
) -> int | None:
    # Return None (not zero) when the ticker hasn't been tracked long enough
    # to have a meaningful count for this window.
    if days_in_dataset < days:
        return None
    cutoff = stat_date - timedelta(days=days)
    window = ticker_df[ticker_df["snapshot_date"] > cutoff]
    if window.empty:
        return None
    return int(window["mention_count_24h"].sum())


def _most_recent_snapshot_date(ticker_df: pd.DataFrame) -> date | None:
    if ticker_df.empty:
        return None
    return ticker_df["snapshot_date"].max()


def _load_all_subreddit_spreads(db, stat_date: date) -> dict[str, int]:
    """Single query for all tickers — avoids N+1 round-trips."""
    cutoff = stat_date - timedelta(days=30)
    rows = (
        db.table("raw_mentions")
        .select("ticker,subreddit")
        .gte("mention_date", str(cutoff))
        .execute()
        .data
    )
    spreads: dict[str, set] = {}
    for r in rows:
        spreads.setdefault(r["ticker"], set()).add(r["subreddit"])
    return {ticker: len(subs) for ticker, subs in spreads.items()}


def compute_row(
    symbol: str,
    first_seen_at: date,
    stat_date: date,
    ticker_df: pd.DataFrame,
    subreddit_spread: int | None,
) -> dict:
    days_in_dataset = (stat_date - first_seen_at).days

    counts = {
        key: _rolling_count(ticker_df, stat_date, days, days_in_dataset)
        for key, days in WINDOW_DAYS.items()
    }

    velocities = {}
    for short_key, long_key in VELOCITY_PAIRS:
        v = compute_velocity(counts[short_key], counts[long_key], short_key, long_key)
        velocities[f"velocity_{short_key}_vs_{long_key}".replace("mo", "mo").replace("1w", "1w")] = v

    # normalise key names to match schema column names
    vel_map = {
        "velocity_1w_vs_1mo": velocities.get("velocity_1w_vs_1mo"),
        "velocity_1mo_vs_3mo": velocities.get("velocity_1mo_vs_3mo"),
        "velocity_3mo_vs_6mo": velocities.get("velocity_3mo_vs_6mo"),
        "velocity_6mo_vs_1y": velocities.get("velocity_6mo_vs_1y"),
    }

    acceleration = compute_acceleration(
        vel_map["velocity_1w_vs_1mo"],
        vel_map["velocity_1mo_vs_3mo"],
    )

    snapshot_date_used = _most_recent_snapshot_date(ticker_df) or stat_date

    return {
        "ticker": symbol,
        "stat_date": str(stat_date),
        "apewisdom_snapshot_date": str(snapshot_date_used),
        "days_in_dataset": days_in_dataset,
        "mention_count_1w": counts["1w"],
        "mention_count_1mo": counts["1mo"],
        "mention_count_3mo": counts["3mo"],
        "mention_count_6mo": counts["6mo"],
        "mention_count_1y": counts["1y"],
        "mention_count_18mo": counts["18mo"],
        "mention_count_2y": counts["2y"],
        "velocity_1w_vs_1mo": vel_map["velocity_1w_vs_1mo"],
        "velocity_1mo_vs_3mo": vel_map["velocity_1mo_vs_3mo"],
        "velocity_3mo_vs_6mo": vel_map["velocity_3mo_vs_6mo"],
        "velocity_6mo_vs_1y": vel_map["velocity_6mo_vs_1y"],
        "acceleration": acceleration,
        "subreddit_spread": subreddit_spread,
        "tranche": "unclassified",  # placeholder; overwritten by Stage 5
    }


def run(stat_date: date | None = None, db=None) -> StageResult:
    if stat_date is None:
        stat_date = date.today()
    if db is None:
        db = get_client()

    result = StageResult()
    all_snapshots = _load_snapshots(db)
    tickers_df = _load_tickers(db)

    if tickers_df.empty:
        log.warning("No active tickers found — skipping scoring")
        return result

    all_spreads = _load_all_subreddit_spreads(db, stat_date)

    rows_to_upsert = []
    for _, ticker_row in tickers_df.iterrows():
        symbol = ticker_row["symbol"]
        try:
            ticker_snaps = all_snapshots[all_snapshots["ticker"] == symbol].copy()
            spread = all_spreads.get(symbol)
            row = compute_row(
                symbol=symbol,
                first_seen_at=ticker_row["first_seen_at"],
                stat_date=stat_date,
                ticker_df=ticker_snaps,
                subreddit_spread=spread,
            )
            rows_to_upsert.append(row)
        except Exception as exc:
            log.error("Scoring failed for %s: %s", symbol, exc)
            result.errors.append(f"{symbol}: scoring_error: {exc}")

    if rows_to_upsert:
        db.table("ticker_daily_stats").upsert(
            rows_to_upsert,
            on_conflict="ticker,stat_date",
        ).execute()
        result.scores_computed = len(rows_to_upsert)

    log.info("Scoring complete: %d tickers scored", result.scores_computed)
    return result
