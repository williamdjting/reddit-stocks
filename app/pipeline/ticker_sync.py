"""
Stage 3 — Ticker registry sync.

For each ticker appearing in today's apewisdom_snapshots:
  - Insert into tickers if not present (first_seen_at = today)
  - Refresh market cap via yfinance (batched)
  - On new tickers: call Claude API for alias extraction

Returns a StageResult with counts and errors.
"""
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import date

import yfinance as yf

from pipeline.config import YFINANCE_BATCH_DELAY_SEC, YFINANCE_BATCH_SIZE
from pipeline.db import get_client

log = logging.getLogger(__name__)


@dataclass
class StageResult:
    new_tickers: int = 0
    cap_updated: int = 0
    cap_failed: int = 0
    errors: list[str] = field(default_factory=list)


def _get_existing_tickers(db) -> set[str]:
    rows = db.table("tickers").select("symbol").execute().data
    return {r["symbol"] for r in rows}


def _get_today_tickers(db, snapshot_date: date) -> list[str]:
    rows = (
        db.table("apewisdom_snapshots")
        .select("ticker")
        .eq("snapshot_date", str(snapshot_date))
        .execute()
        .data
    )
    return [r["ticker"] for r in rows]


def _extract_aliases(symbol: str, name: str) -> list[str]:
    """Call Claude API to get common aliases for a ticker. Returns [] on failure."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return []
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"List common informal names and abbreviations people use on Reddit "
                        f"to refer to the stock {symbol} ({name}). "
                        f"Return only a JSON array of strings, nothing else. "
                        f'Example: ["Rocket Lab", "RKLB", "the rocket company"]'
                    ),
                }
            ],
        )
        import json

        text = msg.content[0].text.strip()
        aliases = json.loads(text)
        return [a for a in aliases if isinstance(a, str) and a != symbol]
    except Exception as exc:
        log.warning("Claude alias extraction failed for %s: %s", symbol, exc)
        return []


def _fetch_market_caps(symbols: list[str]) -> dict[str, dict]:
    """Batch-fetch market cap and sector via yfinance.Tickers (one HTTP call per batch)."""
    results: dict[str, dict] = {}
    for i in range(0, len(symbols), YFINANCE_BATCH_SIZE):
        batch = symbols[i : i + YFINANCE_BATCH_SIZE]
        try:
            tickers_obj = yf.Tickers(" ".join(batch))
            for sym in batch:
                try:
                    t = tickers_obj.tickers.get(sym)
                    if t is None:
                        results[sym] = {}
                        continue
                    fi = t.fast_info
                    mc = getattr(fi, "market_cap", None)
                    results[sym] = {
                        "market_cap": int(mc) if mc is not None else None,
                        "sector": getattr(fi, "sector", None),
                        "name": getattr(fi, "long_name", None) or sym,
                    }
                except Exception as exc:
                    log.warning("yfinance failed for %s: %s", sym, exc)
                    results[sym] = {}
        except Exception as exc:
            log.warning("yfinance batch failed for %s: %s", batch, exc)
            for sym in batch:
                results[sym] = {}
        time.sleep(YFINANCE_BATCH_DELAY_SEC)
    return results


def run(snapshot_date: date | None = None, db=None) -> StageResult:
    if snapshot_date is None:
        snapshot_date = date.today()
    if db is None:
        db = get_client()

    result = StageResult()
    existing = _get_existing_tickers(db)
    today_tickers = _get_today_tickers(db, snapshot_date)

    new_symbols = [t for t in today_tickers if t not in existing]

    # Single batch fetch covers both new-ticker registration and cap refresh
    all_active = today_tickers
    cap_data = _fetch_market_caps(all_active)

    if new_symbols:
        log.info("Registering %d new tickers", len(new_symbols))
        for sym in new_symbols:
            info = cap_data.get(sym, {})
            name = info.get("name") or sym
            aliases = _extract_aliases(sym, name)
            db.table("tickers").upsert(
                {
                    "symbol": sym,
                    "name": name,
                    "aliases": aliases,
                    "market_cap": info.get("market_cap"),
                    "sector": info.get("sector"),
                    "first_seen_at": str(snapshot_date),
                    "cap_verified": info.get("market_cap") is not None,
                    "cap_last_updated": str(snapshot_date) if info.get("market_cap") else None,
                },
                on_conflict="symbol",
            ).execute()
            result.new_tickers += 1
    updates = []
    for sym in all_active:
        info = cap_data.get(sym, {})
        if info.get("market_cap"):
            updates.append(
                {
                    "symbol": sym,
                    "name": info.get("name") or sym,
                    "market_cap": info["market_cap"],
                    "sector": info.get("sector"),
                    "cap_verified": True,
                    "cap_last_updated": str(snapshot_date),
                }
            )
            result.cap_updated += 1
        else:
            db.table("tickers").update({"cap_verified": False}).eq("symbol", sym).execute()
            result.cap_failed += 1
            result.errors.append(f"{sym}: yfinance_failed")

    if updates:
        db.table("tickers").upsert(updates, on_conflict="symbol").execute()

    log.info(
        "Ticker sync: %d new, %d cap updated, %d cap failed",
        result.new_tickers,
        result.cap_updated,
        result.cap_failed,
    )
    return result
