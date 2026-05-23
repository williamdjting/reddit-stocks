"""
Stage 1 — Apewisdom ingest.

Fetches all pages from the Apewisdom public API and upserts daily snapshot
rows into apewisdom_snapshots. Idempotent: safe to re-run for the same date.

Returns a StageResult with counts and any errors encountered.
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import date

import requests

from pipeline.config import APEWISDOM_PAGE_DELAY_SEC
from pipeline.db import get_client

log = logging.getLogger(__name__)

APEWISDOM_BASE = "https://apewisdom.io/api/v1.0/filter/all-stocks/page/{page}"
REQUEST_TIMEOUT = 15  # seconds


@dataclass
class StageResult:
    records_written: int = 0
    pages_fetched: int = 0
    stale: bool = False
    errors: list[str] = field(default_factory=list)


def fetch_page(page: int, session: requests.Session) -> list[dict] | None:
    url = APEWISDOM_BASE.format(page=page)
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as exc:
        log.warning("Apewisdom page %d failed: %s", page, exc)
        return None


def run(snapshot_date: date | None = None, db=None) -> StageResult:
    if snapshot_date is None:
        snapshot_date = date.today()
    if db is None:
        db = get_client()

    result = StageResult()
    session = requests.Session()
    session.headers["User-Agent"] = "reddit-stocks-monitor/0.1"

    page = 1
    consecutive_failures = 0

    while True:
        rows = fetch_page(page, session)

        if rows is None:
            consecutive_failures += 1
            if consecutive_failures >= 3:
                log.error("Apewisdom: 3 consecutive page failures — marking stale")
                result.stale = True
                result.errors.append(f"apewisdom: failed on page {page} after 3 attempts")
                break
            time.sleep(APEWISDOM_PAGE_DELAY_SEC)
            continue

        if not rows:
            break  # empty page = end of results

        consecutive_failures = 0
        records = [
            {
                "ticker": r["ticker"].upper().strip(),
                "snapshot_date": str(snapshot_date),
                "mention_count_24h": int(r.get("mentions") or 0),
                "mention_count_7d": int(r.get("mentions_24h_ago") or 0) or None,
                "rank": int(r.get("rank") or page * 10),
                "upvotes": int(r.get("upvotes") or 0) or None,
            }
            for r in rows
            if r.get("ticker")
        ]

        if records:
            db.table("apewisdom_snapshots").upsert(
                records,
                on_conflict="ticker,snapshot_date",
            ).execute()
            result.records_written += len(records)

        result.pages_fetched += 1
        log.info("Apewisdom page %d: %d records", page, len(records))
        page += 1
        time.sleep(APEWISDOM_PAGE_DELAY_SEC)

    if result.stale:
        log.warning(
            "Apewisdom ingest stale for %s — pipeline will use previous day's data",
            snapshot_date,
        )
    else:
        log.info(
            "Apewisdom ingest complete: %d records across %d pages",
            result.records_written,
            result.pages_fetched,
        )

    return result
