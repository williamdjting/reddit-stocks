"""
Stage 5 — Tranche classifier.

Reads ticker_daily_stats for today and applies:
  1. Quality filter  → may immediately assign 'noise'
  2. Phase gate      → assigns 'insufficient_data' if dataset is too young
  3. Tranche rules   → assigns seed / early / pre_pop / unclassified

On tranche change: appends a row to ticker_tranche_log and updates tickers.current_tranche.
Idempotent: safe to re-run; ticker_tranche_log uses ON CONFLICT on (ticker, entered_at).
"""
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

from pipeline.config import (
    INSUFFICIENT_DATA_MIN_DAYS,
    NOISE_SPIKE_ABS_THRESHOLD,
    NOISE_SUSTAINED_RATIO,
    PUMP_SUBREDDIT_BLOCKLIST,
    QUALITY_MAX_NEW_ACCOUNT_RATIO,
    QUALITY_MIN_ACCOUNT_AGE_DAYS,
    QUALITY_MIN_MARKET_CAP,
    TIER1_MAX_MARKET_CAP,
    TIER1_MAX_WEEKLY_MENTIONS,
    TIER1_MIN_DAYS_IN_DATASET,
    TIER1_MIN_VELOCITY_3MO_VS_6MO,
    TIER1_MIN_VELOCITY_6MO_VS_1Y,
    TIER1_MIN_WEEKLY_MENTIONS,
    TIER2_MAX_MARKET_CAP,
    TIER2_MAX_WEEKLY_MENTIONS,
    TIER2_MIN_DAYS_IN_DATASET,
    TIER2_MIN_VELOCITY_1MO_VS_3MO,
    TIER2_MIN_VELOCITY_3MO_VS_6MO,
    TIER2_MIN_WEEKLY_MENTIONS,
    TIER3_MAX_MARKET_CAP,
    TIER3_MIN_SUBREDDIT_SPREAD,
    TIER3_MIN_WEEKLY_MENTIONS,
    TIER3_WOW_GROWTH_THRESHOLD,
)
from pipeline.db import get_client

log = logging.getLogger(__name__)


@dataclass
class StageResult:
    tranches_updated: int = 0
    transitions_logged: int = 0
    errors: list[str] = field(default_factory=list)


def _is_noise_spike(row: dict, raw_mention_stats: dict) -> bool:
    """True if the ticker shows a coordinated or single-event spike with no sustained build.

    Three independent signals each trigger noise on their own:
    1. Volume spike with no prior monthly build (single-event pattern)
    2. High ratio of mentions from accounts younger than the age threshold
    3. All or most mentions originating from a known pump subreddit
    """
    weekly = row.get("mention_count_1w") or 0
    monthly = row.get("mention_count_1mo") or 0

    # Signal 1: spike without sustained build
    if weekly >= NOISE_SPIKE_ABS_THRESHOLD:
        monthly_weekly_avg = monthly / 4.33 if monthly else 0
        if monthly_weekly_avg < weekly * NOISE_SUSTAINED_RATIO:
            return True

    # Signal 2: high new-account ratio (coordinate pump)
    new_account_ratio = raw_mention_stats.get("new_account_ratio", 0.0)
    if new_account_ratio > QUALITY_MAX_NEW_ACCOUNT_RATIO:
        return True

    # Signal 3: dominant mention source is a blocked pump subreddit
    dominant_sub = raw_mention_stats.get("dominant_subreddit")
    if dominant_sub and dominant_sub in PUMP_SUBREDDIT_BLOCKLIST:
        return True

    return False


def _classify(row: dict, market_cap: int | None, raw_mention_stats: dict) -> str:
    weekly = row.get("mention_count_1w") or 0
    days = row.get("days_in_dataset", 0)

    # Quality gate: market cap too low
    if market_cap is not None and market_cap < QUALITY_MIN_MARKET_CAP:
        return "noise"

    # Noise spike detection
    if _is_noise_spike(row, raw_mention_stats):
        return "noise"

    # Phase gate: insufficient data
    if days < INSUFFICIENT_DATA_MIN_DAYS:
        return "insufficient_data"

    v_1w_1mo = row.get("velocity_1w_vs_1mo")
    v_1mo_3mo = row.get("velocity_1mo_vs_3mo")
    v_3mo_6mo = row.get("velocity_3mo_vs_6mo")
    v_6mo_1y = row.get("velocity_6mo_vs_1y")

    # Tier 3 — Pre-pop (active from Day 1, no phase gate beyond INSUFFICIENT_DATA_MIN_DAYS)
    if (
        market_cap is None or market_cap <= TIER3_MAX_MARKET_CAP
    ):
        wow_growth = v_1w_1mo if v_1w_1mo is not None else 0
        spread = row.get("subreddit_spread") or 0
        if weekly >= TIER3_MIN_WEEKLY_MENTIONS and spread >= TIER3_MIN_SUBREDDIT_SPREAD:
            return "pre_pop"
        if wow_growth >= TIER3_WOW_GROWTH_THRESHOLD and spread >= TIER3_MIN_SUBREDDIT_SPREAD:
            return "pre_pop"

    # Tier 2 — Early (phase gate: 180 days)
    if (
        days >= TIER2_MIN_DAYS_IN_DATASET
        and TIER2_MIN_WEEKLY_MENTIONS <= weekly <= TIER2_MAX_WEEKLY_MENTIONS
        and (market_cap is None or market_cap <= TIER2_MAX_MARKET_CAP)
        and (v_1mo_3mo is not None and v_1mo_3mo >= TIER2_MIN_VELOCITY_1MO_VS_3MO)
        and (v_3mo_6mo is not None and v_3mo_6mo >= TIER2_MIN_VELOCITY_3MO_VS_6MO)
    ):
        return "early"

    # Tier 1 — Seed (phase gate: 365 days)
    if (
        days >= TIER1_MIN_DAYS_IN_DATASET
        and TIER1_MIN_WEEKLY_MENTIONS <= weekly <= TIER1_MAX_WEEKLY_MENTIONS
        and (market_cap is None or market_cap <= TIER1_MAX_MARKET_CAP)
        and (v_6mo_1y is not None and v_6mo_1y >= TIER1_MIN_VELOCITY_6MO_VS_1Y)
        and (v_3mo_6mo is not None and v_3mo_6mo >= TIER1_MIN_VELOCITY_3MO_VS_6MO)
    ):
        return "seed"

    return "unclassified"


def _load_today_stats(db, stat_date: date) -> list[dict]:
    return (
        db.table("ticker_daily_stats")
        .select("*")
        .eq("stat_date", str(stat_date))
        .execute()
        .data
    )


def _load_ticker_meta(db) -> dict[str, dict]:
    rows = db.table("tickers").select("symbol,current_tranche,market_cap").execute().data
    return {r["symbol"]: r for r in rows}


def _load_raw_mention_stats(db, ticker: str, stat_date: date) -> dict:
    """Return quality-filter signals derived from raw_mentions (if table is populated)."""
    try:
        rows = (
            db.table("raw_mentions")
            .select("author_account_age_days,subreddit")
            .eq("ticker", ticker)
            .gte("mention_date", str(stat_date - timedelta(days=7)))
            .execute()
            .data
        )
        if not rows:
            return {}
        total = len(rows)
        new_account = sum(
            1
            for r in rows
            if r.get("author_account_age_days") is not None
            and r["author_account_age_days"] < QUALITY_MIN_ACCOUNT_AGE_DAYS
        )
        subs = [r["subreddit"] for r in rows if r.get("subreddit")]
        dominant = max(set(subs), key=subs.count) if subs else None
        return {
            "new_account_ratio": new_account / total if total else 0.0,
            "dominant_subreddit": dominant,
        }
    except Exception:
        return {}


def run(stat_date: date | None = None, db=None) -> StageResult:
    if stat_date is None:
        stat_date = date.today()
    if db is None:
        db = get_client()

    result = StageResult()
    today_stats = _load_today_stats(db, stat_date)
    ticker_meta = _load_ticker_meta(db)

    if not today_stats:
        log.warning("No ticker_daily_stats found for %s — skipping classification", stat_date)
        return result

    for row in today_stats:
        symbol = row["ticker"]
        try:
            meta = ticker_meta.get(symbol, {})
            market_cap = meta.get("market_cap")
            previous_tranche = meta.get("current_tranche", "unclassified")
            raw_stats = _load_raw_mention_stats(db, symbol, stat_date)

            new_tranche = _classify(row, market_cap, raw_stats)

            # Update ticker_daily_stats tranche field
            db.table("ticker_daily_stats").update({"tranche": new_tranche}).eq(
                "ticker", symbol
            ).eq("stat_date", str(stat_date)).execute()

            # Update tickers.current_tranche
            db.table("tickers").update({"current_tranche": new_tranche}).eq(
                "symbol", symbol
            ).execute()
            result.tranches_updated += 1

            # Log transition only when tranche actually changes
            if new_tranche != previous_tranche:
                db.table("ticker_tranche_log").upsert(
                    {
                        "ticker": symbol,
                        "tranche": new_tranche,
                        "previous_tranche": previous_tranche,
                        "entered_at": str(stat_date),
                        "exited_at": None,
                        "velocity_at_entry": row.get("velocity_1w_vs_1mo"),
                        "mention_count_at_entry": row.get("mention_count_1w"),
                        "market_cap_at_entry": market_cap,
                    },
                    on_conflict="ticker,entered_at",
                ).execute()

                # Close previous open log entry
                db.table("ticker_tranche_log").update({"exited_at": str(stat_date)}).eq(
                    "ticker", symbol
                ).eq("tranche", previous_tranche).is_("exited_at", "null").execute()

                result.transitions_logged += 1
                log.info("%s: %s → %s", symbol, previous_tranche, new_tranche)

        except Exception as exc:
            log.error("Classification failed for %s: %s", symbol, exc)
            result.errors.append(f"{symbol}: classify_error: {exc}")

    log.info(
        "Classification complete: %d updated, %d transitions",
        result.tranches_updated,
        result.transitions_logged,
    )
    return result
