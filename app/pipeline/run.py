"""
Pipeline orchestrator.

Sequences all pipeline stages in order, captures per-stage results,
and writes a final pipeline_runs record. Each stage is isolated:
a crash in Stage N does not corrupt Stages 1 through N-1.

Usage:
    python -m pipeline.run                  # run for today
    python -m pipeline.run 2026-05-22       # run for a specific date (re-run)
"""
import logging
import sys
import time
from datetime import date, datetime, timezone

from pipeline import apewisdom_ingest, score_compute, ticker_sync, tranche_classify
from pipeline.db import get_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log"),
    ],
)
log = logging.getLogger(__name__)


def run(run_date: date | None = None, db=None) -> int:
    """
    Run the full pipeline. Returns exit code (0 = success, 1 = failure).
    """
    if run_date is None:
        run_date = date.today()
    if db is None:
        db = get_client()

    started_at = datetime.now(timezone.utc)
    all_errors: list[str] = []
    status = "success"

    tickers_processed = 0
    apewisdom_records = 0
    apewisdom_stale = False
    scores_computed = 0
    tranches_updated = 0

    log.info("=== Pipeline starting for %s ===", run_date)

    # ── Stage 1: Apewisdom ingest ──────────────────────────────────────────
    log.info("Stage 1: Apewisdom ingest")
    try:
        r1 = apewisdom_ingest.run(snapshot_date=run_date, db=db)
        apewisdom_records = r1.records_written
        apewisdom_stale = r1.stale
        all_errors.extend(r1.errors)
        if r1.stale:
            log.warning("Stage 1 stale — will score from previous day's snapshots")
    except Exception as exc:
        log.error("Stage 1 crashed: %s", exc)
        all_errors.append(f"stage1: {exc}")
        status = "partial"

    # ── Stage 2: Reddit ingest (optional — skip if env vars absent) ────────
    log.info("Stage 2: Reddit ingest (optional)")
    try:
        import os

        if os.environ.get("REDDIT_CLIENT_ID"):
            try:
                from pipeline import reddit_ingest
                r2 = reddit_ingest.run(snapshot_date=run_date, db=db)
                all_errors.extend(r2.errors)
            except ImportError:
                log.info("Stage 2 skipped — reddit_ingest module not available")
        else:
            log.info("Stage 2 skipped — REDDIT_CLIENT_ID not set")
    except Exception as exc:
        log.warning("Stage 2 failed (non-fatal): %s", exc)
        all_errors.append(f"stage2_optional: {exc}")

    # ── Stage 3: Ticker registry ───────────────────────────────────────────
    log.info("Stage 3: Ticker registry")
    try:
        r3 = ticker_sync.run(snapshot_date=run_date, db=db)
        tickers_processed = r3.new_tickers + r3.cap_updated + r3.cap_failed
        all_errors.extend(r3.errors)
    except Exception as exc:
        log.error("Stage 3 crashed: %s", exc)
        all_errors.append(f"stage3: {exc}")
        status = "partial"

    # ── Stage 4: Scoring engine ────────────────────────────────────────────
    log.info("Stage 4: Scoring engine")
    try:
        r4 = score_compute.run(stat_date=run_date, db=db)
        scores_computed = r4.scores_computed
        all_errors.extend(r4.errors)
        if scores_computed == 0:
            log.error("Stage 4: 0 scores computed — possible silent failure")
            all_errors.append("stage4: 0 scores computed")
            status = "partial"
    except Exception as exc:
        log.error("Stage 4 crashed: %s", exc)
        all_errors.append(f"stage4: {exc}")
        status = "partial"

    # ── Stage 5: Tranche classifier ────────────────────────────────────────
    log.info("Stage 5: Tranche classifier")
    try:
        r5 = tranche_classify.run(stat_date=run_date, db=db)
        tranches_updated = r5.tranches_updated
        all_errors.extend(r5.errors)
    except Exception as exc:
        log.error("Stage 5 crashed: %s", exc)
        all_errors.append(f"stage5: {exc}")
        status = "partial"

    # ── Stage 6: Run logger ────────────────────────────────────────────────
    completed_at = datetime.now(timezone.utc)
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)
    log.info("Stage 6: Writing pipeline_runs record (%s, %dms)", status, duration_ms)
    try:
        db.table("pipeline_runs").upsert(
            {
                "run_date": str(run_date),
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "status": status,
                "tickers_processed": tickers_processed,
                "apewisdom_records": apewisdom_records,
                "reddit_records": 0,
                "scores_computed": scores_computed,
                "tranches_updated": tranches_updated,
                "apewisdom_stale": apewisdom_stale,
                "errors": all_errors,
                "duration_ms": duration_ms,
            },
            on_conflict="run_date",
        ).execute()
    except Exception as exc:
        log.error("Stage 6 (logging) failed: %s", exc)

    log.info(
        "=== Pipeline complete: %s | %d records | %d scores | %d tranches | %dms ===",
        status,
        apewisdom_records,
        scores_computed,
        tranches_updated,
        duration_ms,
    )

    return 0 if status == "success" else 1


if __name__ == "__main__":
    target_date = None
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    sys.exit(run(run_date=target_date))
