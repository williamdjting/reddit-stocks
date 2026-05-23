# Engineering Review: Multi-Tranche Reddit Pre-Breakout Sentiment Monitor

**Generated:** 2026-05-23 02:50
**Verdict:** Ready with modifications

---

## Data Flow Diagram

### Daily Pipeline (GitHub Actions, 6 AM UTC)

```
GitHub Actions trigger
        │
        ▼
[Stage 1 — Apewisdom Ingest]
  GET apewisdom.io/api/v1.0/filter/all-stocks/page/{n}
  Paginate until empty page
  Validate: mention_count_24h not null, ticker not empty
  Upsert: apewisdom_snapshots (ticker, snapshot_date) ON CONFLICT DO UPDATE
  On HTTP error → log apewisdom_stale=true, CONTINUE pipeline (use prev day's data)
        │
        ▼
[Stage 2 — Reddit Ingest]  ← OPTIONAL, skip entirely if disabled
  PRAW: fetch top posts from each monitored subreddit
  Extract ticker mentions from titles/text
  Upsert: raw_mentions (ticker, post_id) ON CONFLICT DO NOTHING
  On PRAW error → skip stage, log error, CONTINUE
        │
        ▼
[Stage 3 — Ticker Registry]
  For each ticker in today's apewisdom_snapshots not in tickers table:
    Call Claude API → get aliases
    Insert tickers row with first_seen_at=today
  For all active tickers:
    Call yfinance.Ticker(symbol).info → market_cap, sector
    On yfinance error for ticker → keep cached value, set cap_verified=false
  Upsert: tickers (symbol) ON CONFLICT DO UPDATE market_cap, updated_at
        │
        ▼
[Stage 4 — Scoring Engine]
  For each active ticker:
    Read apewisdom_snapshots WHERE ticker=X ORDER BY snapshot_date DESC
    Compute days_in_dataset = count(distinct snapshot_date)  ← SEE FINDING #1
    Compute rolling mention counts for each available window
    Compute velocity ratios (adjacent windows only where both have data)
    Compute acceleration (velocity_1w_vs_1mo - velocity_1mo_vs_3mo)
    Compute subreddit_spread from raw_mentions (if available, else NULL)
  Upsert: ticker_daily_stats (ticker, stat_date) ON CONFLICT DO UPDATE
        │
        ▼
[Stage 5 — Tranche Classifier]
  For each ticker with ticker_daily_stats for today:
    Apply quality filter → may assign "noise" immediately
    Apply phase gate → may assign "insufficient_data"
    Apply tranche rules → assign seed/early/pre_pop/unclassified/noise
    Compare to tickers.current_tranche
    If changed: INSERT ticker_tranche_log row, set exited_at on previous open row
    UPDATE tickers.current_tranche
        │
        ▼
[Stage 6 — Run Logger]
  Collect stage-level counts and errors from all previous stages
  UPSERT pipeline_runs (run_date) ON CONFLICT DO UPDATE
  If status != 'success' AND previous_day.status != 'success':
    GitHub Actions exit code 1 → email notification
        │
        ▼
        DONE
```

### Dashboard Read Path

```
User opens browser
        │ HTTPS
        ▼
Streamlit Cloud (Python process, long-lived)
        │ supabase-py (anon key, read-only)
        ▼
Supabase PostgreSQL
  ├── ticker_daily_stats  → velocity scores, mention counts, tranche
  ├── tickers             → current_tranche, market_cap, aliases, first_seen_at
  ├── ticker_tranche_log  → transition history, days in current tranche
  ├── apewisdom_snapshots → raw daily counts for charts
  └── pipeline_runs       → pipeline health view
        │ query results
        ▼
Plotly charts rendered in browser
```

---

## State Machine — Tranche States

```
States: insufficient_data | unclassified | seed | early | pre_pop | noise

Initial state: insufficient_data (days_in_dataset < 90)

Valid transitions:
  insufficient_data → unclassified     (days_in_dataset reaches 90)
  insufficient_data → pre_pop          (days >= 90, high velocity from day 1)
  unclassified     → seed              (ONLY after 365 days in dataset)
  unclassified     → early             (ONLY after 180 days in dataset)
  unclassified     → pre_pop           (any time, velocity threshold met)
  unclassified     → noise             (any time, quality filter triggered)
  pre_pop          → early             (velocity normalises, enters Early range)
  pre_pop          → noise             (spike pattern confirmed as isolated)
  pre_pop          → unclassified      (velocity drops, no longer meets any criteria)
  early            → seed              (NOT VALID — seed requires longer horizon)
  early            → pre_pop           (acceleration increases again)
  early            → noise             (quality filter)
  seed             → early             (velocity accelerates, meets Early threshold)
  seed             → pre_pop           (velocity spikes, meets Pre-pop threshold)
  noise            → unclassified      (spike subsides, returns to normal)
  any              → insufficient_data (NOT VALID — days_in_dataset never decreases)

Source of truth: tickers.current_tranche (live)
History:         ticker_tranche_log (immutable append-only)
```

---

## Findings

### Finding 1 — days_in_dataset source is undefined (BLOCKER)

**The phase gate depends on `days_in_dataset`. How it is computed is not specified.**

Two possible interpretations:
- A: `COUNT(DISTINCT snapshot_date) FROM apewisdom_snapshots WHERE ticker=X`
- B: `CURRENT_DATE - tickers.first_seen_at`

These produce different results. If Apewisdom didn't return data for a ticker for 7 days
(e.g., the ticker fell off the top pages), interpretation A would give 173 days when the
ticker has been tracked for 180 calendar days. Interpretation B would give 180.

The phase gate (Tier 2 at 180 days, Tier 1 at 365 days) is the most critical classification
rule. Its inputs must be precisely defined. **Decision required before implementation.**

Recommendation: Use `CURRENT_DATE - tickers.first_seen_at::date` as the canonical source.
A ticker "entered the dataset" on first_seen_at regardless of data gaps. Store a pre-computed
`days_in_dataset` in `ticker_daily_stats` derived from `tickers.first_seen_at`, not from
counting snapshot rows.

---

### Finding 2 — Velocity formula is not precisely defined (BLOCKER)

The schema comments say:
> `velocity_1w_vs_1mo: normalised weekly rate ratio between adjacent windows`

"Normalised weekly rate ratio" is ambiguous. Two common interpretations:

**Interpretation A (ratio):**
```
velocity_1w_vs_1mo = (mention_count_1w / 1) / (mention_count_1mo / 4.33)
```
Result: >1.0 means last week was above the 1-month weekly average. <1.0 means below.

**Interpretation B (percentage change of weekly rate):**
```
weekly_rate_1mo = mention_count_1mo / 4.33
velocity_1w_vs_1mo = (mention_count_1w - weekly_rate_1mo) / weekly_rate_1mo
```
Result: positive = accelerating, negative = decelerating.

These produce different numbers and different threshold semantics. The tranche rule
"velocity_1w_vs_1mo > threshold" means something different depending on which formula
is used. **Define the exact formula in config.py before writing score_compute.py.**

---

### Finding 3 — Noise detection algorithm is not specified (BLOCKER)

The tranche `noise` is defined in the PRD as:
> *"High volume spike without sustained build (single-event pattern)"*

The schema and architecture do not specify the algorithm. Likely approaches:

- **Spike + decay test:** if mention_count_1w > threshold AND mention_count_1mo / 4.33 < 0.3 × mention_count_1w, classify as noise (spike not sustained by prior volume)
- **Lookback comparison:** if last 4 weeks before this week all had mention_count < N, and this week exceeds M×N, it's a single-event spike
- **Quality filter first:** if >80% mentions from accounts <30 days old, it's coordinated = noise

Without a specified algorithm, two developers will produce two different noise classifiers.
**Define the exact noise detection logic in config.py before implementation.**

---

### Finding 4 — ticker_daily_stats doesn't record which snapshot date was used for scoring

When `apewisdom_stale=true`, the scoring engine uses yesterday's snapshot data but writes
a `ticker_daily_stats` row with `stat_date = today`. This means the record is misleading:
it looks like today's scores were computed from today's data, but they were actually
computed from yesterday's data.

This matters for debugging (was this score computed from good or stale data?) and for ML
(if you're using the tranche log as a training set, you need to know data quality).

**Recommended fix:** Add a nullable column `apewisdom_snapshot_date date` to
`ticker_daily_stats`. When scoring from stale data, set this to yesterday's date.
When scoring from fresh data, set it to today's date (= stat_date). This adds 4 bytes
per row and makes the scoring provenance explicit.

---

### Finding 5 — Pipeline timing budget not validated

At 2,000 tickers with 0.5s delay between yfinance calls (Stage 3):
```
2,000 × 0.5s = 1,000s = 16.7 minutes for market cap refresh alone
```

For Apewisdom with 1s delay between pages and ~10 tickers per page:
```
2,000 tickers / 10 per page = 200 pages × 1s = 3.3 minutes
```

Scoring engine (Stage 4) for 2,000 tickers reading up to 730 snapshot rows each:
```
2,000 × 730 rows = 1.46M rows to read and aggregate
```

Without a database query optimization strategy (indexes are defined ✓, but batch vs
per-ticker fetching matters significantly), Stage 4 could take 30–90 minutes.

Total naive estimate: 50–120 minutes. The target is <60 minutes (to stay within the
GitHub Actions free tier budget of ~1,800 min/month).

**Required: define the Stage 4 execution strategy.** Options:
- A: Fetch per-ticker in Python loop (simple, slow)
- B: Single SQL query computing all rolling windows in the database (fast, complex SQL)
- C: Read all snapshots into a pandas DataFrame, group by ticker, compute in-memory (medium)

Option C (pandas in-memory) is likely the right call for v1 at 2,000 tickers. But the
database read of ~1.46M rows needs to be validated against Supabase free tier bandwidth
limits (2GB/month). At ~100 bytes per snapshot row: 1.46M × 100B = ~146MB per daily run.
12 months × 146MB = ~1.75GB/year. This is under the 2GB/month free tier bandwidth limit
per run, but close enough to monitor.

---

### Finding 6 — ticker_tranche_log idempotency on re-run is unspecified

The tranche log uses `exited_at IS NULL` to identify the current open tranche period.
On a re-run of the pipeline for the same date:

- Classifier reads `tickers.current_tranche` (the live value)
- Compares to newly computed tranche
- If they match: no new log entry (correct)
- If they differ: inserts new log entry with `entered_at = today` and closes previous

On a re-run, the first run may have already updated `tickers.current_tranche` and created
a log entry. The second run would then compare the already-updated current_tranche to the
newly computed tranche — and if they match (which they should, since same data), no
duplicate is created. This is correct.

**BUT:** if the pipeline is partially idempotent and Stage 3 (tranche classify) is the
only stage re-run (e.g., after a bug fix), and the previous run already created a log entry
today, the re-run needs to check: was a log entry already created with `entered_at = today`?
If yes, upsert rather than insert.

**Required fix:** Tranche log entries for `(ticker, entered_at)` should have a UNIQUE
constraint or the insert should be `ON CONFLICT (ticker, entered_at) DO UPDATE`. Currently
the schema has no such constraint on `ticker_tranche_log`.

---

### Finding 7 — Per-ticker error isolation not designed

If yfinance fails for 3 out of 2,000 tickers (HTTP error, stale data, rate limit), the
current architecture description says errors go into `pipeline_runs.errors text[]`. But
there's no design for:
- What happens to those 3 tickers' `ticker_daily_stats` rows? Written with cached market cap? Skipped entirely?
- How does the system know to retry these 3 tickers on the next run?
- Does `tickers.cap_verified` get set to false for those 3 specifically?

**Required:** Define the per-ticker error handling contract before implementation:
> "If yfinance fails for a ticker: (1) use cached market_cap from tickers table,
> (2) set cap_verified=false, (3) append `{ticker}: yfinance_failed` to pipeline_runs.errors,
> (4) continue pipeline for that ticker using cached value."

---

### Finding 8 — Phase gate enforcement point is Stage 5 only

If a ticker has `days_in_dataset = 200` (under the Tier 1 gate of 365), the tranche
classifier correctly blocks Tier 1 assignment. But the dashboard Tranche Overview also
needs to apply the same gate when deciding whether to show the "Maturing" placeholder.

The dashboard reads `tickers.current_tranche`, which is set by the classifier. Since the
classifier enforces the gate, the dashboard will correctly never show a Seed ticker before
day 365. But the "Maturing — activates [date]" placeholder requires the dashboard to know
**when** the gate will open, which requires knowing `tickers.first_seen_at`.

This is derivable from the DB but needs to be explicitly designed in the dashboard query:
```sql
SELECT
  t.first_seen_at,
  (t.first_seen_at + interval '365 days')::date AS seed_activates_on,
  (t.first_seen_at + interval '180 days')::date AS early_activates_on
FROM tickers t
LIMIT 1
```

Minor — but needs to be in the dashboard implementation spec.

---

## Test Plan

### Unit tests (must pass before PR)

| Test | What it verifies |
|------|-----------------|
| `test_insufficient_data_gate` | Ticker with days_in_dataset=89 → "insufficient_data"; days=90 → eligible |
| `test_seed_phase_gate` | Ticker with days=200 and perfect velocity → NOT "seed"; days=365 → eligible |
| `test_early_phase_gate` | Ticker with days=170 → NOT "early"; days=180 → eligible |
| `test_noise_spike_detection` | Ticker with week spike 10× prior month average, no sustained volume → "noise" |
| `test_market_cap_gate_pre_pop` | market_cap > $20B → excluded from pre_pop |
| `test_market_cap_gate_early` | market_cap > $10B → excluded from early |
| `test_market_cap_gate_seed` | market_cap > $5B → excluded from seed |
| `test_velocity_formula` | Known inputs produce exact expected velocity value |
| `test_acceleration_formula` | Known inputs produce exact expected acceleration value |
| `test_rolling_window_null_vs_zero` | Window with no data → NULL, not 0 |
| `test_quality_filter_account_age` | 85% of mentions from <30-day accounts → "noise" |
| `test_quality_filter_pump_subreddit` | 100% mentions from blocklisted subreddit → "noise" |

### Integration tests (must pass before merge)

| Test | What it verifies |
|------|-----------------|
| `test_apewisdom_upsert_idempotent` | Running ingest twice for same date produces same row count |
| `test_apewisdom_stale_flag` | On API 503: pipeline_runs.apewisdom_stale=true, existing snapshots unchanged |
| `test_ticker_daily_stats_upsert` | Re-running scoring for same date → same values, no duplicates |
| `test_tranche_log_transition_on_change` | Tranche change → 1 new log row; no change → 0 new rows |
| `test_tranche_log_no_duplicate_on_rerun` | Re-running classify twice same day → 1 log row, not 2 |
| `test_pipeline_runs_upsert` | Re-running pipeline for same run_date → 1 row in pipeline_runs |
| `test_new_ticker_auto_registration` | Ticker in apewisdom but not in tickers table → inserted with first_seen_at=today |
| `test_partial_failure_no_corruption` | Stage 4 crash → Stage 1–3 rows intact; no partial ticker_daily_stats |

### Manual verification (must be done before first pipeline run on real Supabase)

1. Run pipeline in dry-run mode (print SQL without executing) — verify all UPSERT statements use correct ON CONFLICT targets
2. Execute `schema.sql` on Supabase → confirm all indexes created, no errors
3. Run pipeline for a single day with 10 test tickers — verify all 6 tables populated correctly
4. Manually inspect `ticker_tranche_log` after 2 consecutive days — confirm open entries (exited_at IS NULL) are correct
5. Trigger yfinance failure for one ticker by using an invalid symbol — verify it uses cached value and sets cap_verified=false
6. Force `apewisdom_stale=true` by temporarily blocking the API — confirm pipeline continues and uses previous day's snapshots for scoring

### Rollback criteria

Re-run the pipeline for the same date if:
- `pipeline_runs.status = 'failed'` (Stage 4 or 5 did not complete)
- `pipeline_runs.scores_computed < 0.9 × tickers_processed` (>10% of tickers missing scores)
- Any stage produced `0` records when the previous day produced >100

The pipeline is idempotent — re-running is always safe.

---

## Required Changes

1. **Define `days_in_dataset` source precisely.** Use `CURRENT_DATE - tickers.first_seen_at::date`. Document this in `config.py` comments. Do not count snapshot rows.

2. **Define velocity formula precisely.** Add the exact formula as a Python function in `config.py` or `score_compute.py` with a docstring. The recommended interpretation: `velocity = (mention_count_short / short_weeks) / (mention_count_long / long_weeks)`. Value >1.0 = accelerating.

3. **Define noise detection algorithm.** Proposed: classify as noise if `mention_count_1w > NOISE_SPIKE_THRESHOLD AND mention_count_1mo < NOISE_SPIKE_THRESHOLD × NOISE_SUSTAINED_RATIO`. Both constants go in `config.py`. Validate against at least 3 known pump-and-dump events.

4. **Add `apewisdom_snapshot_date date` to `ticker_daily_stats`.** Set to the actual snapshot date used for scoring (today if fresh, yesterday if stale). Update schema.sql before running migrate.

5. **Add UNIQUE constraint to `ticker_tranche_log (ticker, entered_at)`.** Use `ON CONFLICT (ticker, entered_at) DO UPDATE SET tranche=EXCLUDED.tranche` on inserts. Prevents duplicate log entries on pipeline re-runs.

6. **Define pipeline timing budget.** Run Stage 3 (yfinance) in batches of 10 tickers with 0.5s between batches (not 0.5s per ticker). Run Stage 4 using a single pandas DataFrame load of all snapshots (one SQL query) rather than per-ticker queries. Document target runtime for each stage in `config.py` comments.

7. **Define per-ticker error contract for yfinance failures.** Add to `config.py`: "On yfinance failure for a ticker: use cached market_cap, set cap_verified=false, append error to pipeline_runs.errors, continue." Implement exactly this behavior in `market_cap_fetch.py`.

---

## Open Questions

1. **What is the minimum weekly mention count threshold for Pre-pop?** The PRD says ">300/week". Is this threshold applied to `mention_count_1w` from `ticker_daily_stats` or to the raw `mention_count_24h × 7` from `apewisdom_snapshots`? The former is more accurate but requires scoring to complete first. The latter can be a pre-filter. Choose one before implementing Stage 5.

2. **How should velocity be computed when one window's count is zero (not null)?** Zero is valid (ticker received zero mentions in a window). Dividing by zero produces infinity. The classifier needs a guard: if the denominator window count is 0 AND the numerator is >0, treat velocity as infinity and immediately classify Pre-pop or noise. If both are 0, treat velocity as null.

3. **Config.py enumeration:** The PRD says "all thresholds must be stored as configurable parameters, not hardcoded." Before writing a single classifier line, enumerate every threshold in config.py:
   - `TIER3_MIN_WEEKLY_MENTIONS = 300`
   - `TIER3_WOW_GROWTH_THRESHOLD = 0.50`
   - `TIER3_MIN_SUBREDDIT_SPREAD = 3`
   - `TIER3_MAX_MARKET_CAP = 20_000_000_000`
   - `TIER2_MIN_WEEKLY_MENTIONS = 50`
   - `TIER2_MAX_WEEKLY_MENTIONS = 300`
   - `TIER2_MIN_DAYS_IN_DATASET = 180`
   - `TIER2_MAX_MARKET_CAP = 10_000_000_000`
   - `TIER1_MIN_WEEKLY_MENTIONS = 5`
   - `TIER1_MAX_WEEKLY_MENTIONS = 50`
   - `TIER1_MIN_DAYS_IN_DATASET = 365`
   - `TIER1_MAX_MARKET_CAP = 5_000_000_000`
   - `QUALITY_MIN_MARKET_CAP = 50_000_000`
   - `QUALITY_MAX_NEW_ACCOUNT_RATIO = 0.80`
   - `QUALITY_MIN_ACCOUNT_AGE_DAYS = 30`
   - `INSUFFICIENT_DATA_MIN_DAYS = 90`
   This list must be complete before implementation starts.

---

## Latest file

This document supersedes: none (first engineering review)
