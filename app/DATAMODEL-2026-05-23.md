# Data Model: Multi-Tranche Reddit Pre-Breakout Sentiment Monitor

**Generated:** 2026-05-23 02:00
**Database:** PostgreSQL 15 (Supabase)
**ORM:** None — raw SQL via supabase-py (psycopg2 under the hood)

---

## Entities

### tickers
Master registry of all tracked stock tickers. The source of truth for symbol,
company name, aliases, and current classification state.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| symbol | text | PK | Ticker symbol e.g. RKLB. Uppercase, max ~5 chars in practice. |
| name | text | NOT NULL | Full company name e.g. "Rocket Lab USA Inc" |
| aliases | text[] | NOT NULL, DEFAULT '{}' | Common informal names. Array kept short (2–6 items). |
| market_cap | bigint | NULLABLE | In USD. Null until first yfinance fetch. |
| sector | text | NULLABLE | e.g. "Industrials", "Technology" |
| current_tranche | tranche_enum | NOT NULL, DEFAULT 'insufficient_data' | Denormalised for fast dashboard queries. |
| cap_verified | boolean | NOT NULL, DEFAULT false | False if yfinance failed on last run. |
| cap_last_updated | timestamptz | NULLABLE | When market cap was last successfully fetched. |
| is_active | boolean | NOT NULL, DEFAULT true | Soft-disable without deleting history. |
| first_seen_at | timestamptz | NOT NULL, DEFAULT now() | When first mention was detected. |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |

---

### apewisdom_snapshots
Raw daily output from the Apewisdom API. Append-only — never modified after insert.
One row per ticker per day. This is the primary signal source.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| ticker | text | FK → tickers.symbol, NOT NULL | |
| snapshot_date | date | NOT NULL | The calendar date this snapshot represents. |
| mention_count_24h | integer | NOT NULL | Mentions in the last 24 hours per Apewisdom. |
| mention_count_7d | integer | NULLABLE | 7-day count if API provides it. |
| rank | integer | NULLABLE | Apewisdom daily rank (1 = most mentioned). |
| upvotes | integer | NULLABLE | Upvote aggregate if API provides it. |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

**Unique constraint:** (ticker, snapshot_date) — idempotent upserts on conflict.

---

### raw_mentions
Optional post-level context from Reddit API (PRAW). Append-only. Dropped entirely
if Reddit ToS prohibits use. The scoring engine does not depend on this table.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| ticker | text | FK → tickers.symbol, NOT NULL | |
| post_id | text | NOT NULL | Reddit post ID (e.g. "t3_abc123"). Globally unique per post. |
| subreddit | text | NOT NULL | Without r/ prefix. |
| post_title | text | NOT NULL | Full post title. |
| content_snippet | text | NULLABLE | First 500 chars of selftext. Null for link posts. |
| author_account_age_days | integer | NULLABLE | For quality filtering. Null if unavailable. |
| mention_date | date | NOT NULL | Date of the post. |
| source | text | NOT NULL, DEFAULT 'reddit_api' | 'reddit_api' or 'reddit_scrape'. |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

**Unique constraint:** (ticker, post_id) — each post counted once per ticker.

---

### ticker_daily_stats
Computed scores for every active ticker, recalculated each pipeline run.
One row per ticker per day. Can be fully rebuilt from apewisdom_snapshots.
This is the table the dashboard reads most heavily.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| ticker | text | FK → tickers.symbol, NOT NULL | |
| stat_date | date | NOT NULL | The date these stats represent. |
| days_in_dataset | integer | NOT NULL | Days since first apewisdom_snapshot for this ticker. Used for phase-gating. |
| mention_count_1w | integer | NULLABLE | Rolling 7-day sum. Null if <7 days of data. |
| mention_count_1mo | integer | NULLABLE | Rolling 30-day sum. |
| mention_count_3mo | integer | NULLABLE | Rolling 90-day sum. |
| mention_count_6mo | integer | NULLABLE | Rolling 180-day sum. |
| mention_count_1y | integer | NULLABLE | Rolling 365-day sum. |
| mention_count_18mo | integer | NULLABLE | Rolling 548-day sum. |
| mention_count_2y | integer | NULLABLE | Rolling 730-day sum. |
| velocity_1w_vs_1mo | numeric(8,4) | NULLABLE | (count_1w / 7) / (count_1mo / 30) — normalised weekly rate ratio. >1 = accelerating. |
| velocity_1mo_vs_3mo | numeric(8,4) | NULLABLE | Same ratio for 1mo vs 3mo windows. |
| velocity_3mo_vs_6mo | numeric(8,4) | NULLABLE | |
| velocity_6mo_vs_1y | numeric(8,4) | NULLABLE | |
| acceleration | numeric(8,4) | NULLABLE | Rate of change of velocity: velocity_1w_vs_1mo - velocity_1mo_vs_3mo. |
| subreddit_spread | integer | NULLABLE | Distinct subreddits in last 30 days (from raw_mentions if available, else Apewisdom metadata). |
| tranche | tranche_enum | NOT NULL | Classification output of the scoring engine for this day. |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| updated_at | timestamptz | NOT NULL, DEFAULT now() | |

**Unique constraint:** (ticker, stat_date) — idempotent upserts on conflict.

---

### ticker_tranche_log
Records every tranche transition. Append-only — a new row is written only when
a ticker moves from one tranche to another. This table accumulates the labeled
dataset for future ML: "was ticker X in Seed 18 months before it broke out?"

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| ticker | text | FK → tickers.symbol, NOT NULL | |
| tranche | tranche_enum | NOT NULL | The tranche being entered. |
| previous_tranche | tranche_enum | NULLABLE | The tranche being exited. Null on first classification. |
| entered_at | date | NOT NULL | Date this tranche was entered. |
| exited_at | date | NULLABLE | Date this tranche was exited. Null = currently in this tranche. |
| velocity_at_entry | numeric(8,4) | NULLABLE | velocity_1w_vs_1mo at time of entry. Context for ML feature. |
| mention_count_at_entry | integer | NULLABLE | mention_count_1w at time of entry. |
| market_cap_at_entry | bigint | NULLABLE | Market cap at time of entry. |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

**Note:** When a ticker exits a tranche, the existing open row is updated
(`exited_at` set to today) and a new row is inserted for the new tranche.
This is the one exception to the append-only rule — `exited_at` is updated in place.

---

### pipeline_runs
Reliability log for every daily pipeline execution. One row per calendar day.
The dashboard can surface this to show data freshness. Used to detect silent failures.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | uuid | PK, DEFAULT gen_random_uuid() | |
| run_date | date | UNIQUE, NOT NULL | The date the pipeline ran for. |
| started_at | timestamptz | NOT NULL | |
| completed_at | timestamptz | NULLABLE | Null if still running or failed before completion. |
| status | run_status_enum | NOT NULL | 'success', 'partial', 'failed' |
| tickers_processed | integer | NULLABLE | How many tickers were active this run. |
| apewisdom_records | integer | NULLABLE | Rows written to apewisdom_snapshots. |
| reddit_records | integer | NULLABLE | Rows written to raw_mentions (null if stage skipped). |
| scores_computed | integer | NULLABLE | Rows written to ticker_daily_stats. |
| tranches_updated | integer | NULLABLE | Rows appended to ticker_tranche_log. |
| apewisdom_stale | boolean | NOT NULL, DEFAULT false | True if Apewisdom stage was skipped; previous day's data used. |
| errors | text[] | NOT NULL, DEFAULT '{}' | Error messages from any failed stage. |
| duration_ms | integer | NULLABLE | Total wall-clock time in milliseconds. |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |

---

## Enums

```sql
CREATE TYPE tranche_enum AS ENUM (
  'seed',               -- Tier 1: 12+ months, 5-50/wk, low cap
  'early',              -- Tier 2: 6+ months, 50-300/wk
  'pre_pop',            -- Tier 3: >300/wk or >50% WoW growth
  'noise',              -- High volume, single-event spike, no sustained build
  'insufficient_data',  -- <90 days in dataset
  'unclassified'        -- Active ticker, 90+ days, but no tranche rule matched
);

CREATE TYPE run_status_enum AS ENUM (
  'success',   -- All stages completed, no errors
  'partial',   -- Some stages completed, some skipped or errored
  'failed'     -- Pipeline aborted, data may be incomplete
);
```

---

## Relationships

```
tickers          1 ──< N   apewisdom_snapshots   (ticker FK, ON DELETE RESTRICT)
tickers          1 ──< N   raw_mentions           (ticker FK, ON DELETE RESTRICT)
tickers          1 ──< N   ticker_daily_stats     (ticker FK, ON DELETE RESTRICT)
tickers          1 ──< N   ticker_tranche_log     (ticker FK, ON DELETE RESTRICT)
pipeline_runs              (standalone — no FK to tickers, logs the run as a whole)
```

**ON DELETE RESTRICT on all ticker FKs:** A ticker with associated data cannot
be deleted. Use `is_active = false` to soft-disable instead. This protects the
historical dataset from accidental deletion.

---

## Indexes

| Index | Table | Columns | Purpose |
|---|---|---|---|
| PK | tickers | symbol | Primary key lookup |
| PK | apewisdom_snapshots | id | Primary key |
| UNIQUE | apewisdom_snapshots | (ticker, snapshot_date) | Idempotent upserts; fetch ticker history |
| IDX | apewisdom_snapshots | snapshot_date DESC | Fetch all tickers for a given date |
| PK | raw_mentions | id | Primary key |
| UNIQUE | raw_mentions | (ticker, post_id) | Idempotent upserts; deduplication |
| IDX | raw_mentions | (ticker, mention_date DESC) | Ticker post history |
| PK | ticker_daily_stats | id | Primary key |
| UNIQUE | ticker_daily_stats | (ticker, stat_date) | Idempotent upserts |
| IDX | ticker_daily_stats | (stat_date DESC, tranche) | Dashboard: today's tickers per tranche |
| IDX | ticker_daily_stats | (tranche, velocity_1w_vs_1mo DESC) | Dashboard: sort by velocity within tranche |
| IDX | ticker_daily_stats | (ticker, stat_date DESC) | Ticker detail chart (time series) |
| PK | ticker_tranche_log | id | Primary key |
| IDX | ticker_tranche_log | (ticker, entered_at DESC) | Ticker tranche history |
| IDX | ticker_tranche_log | (tranche, entered_at DESC) | ML queries: all tickers that entered Seed in period X |
| IDX | ticker_tranche_log | exited_at | Find currently-open tranche records (WHERE exited_at IS NULL) |
| UNIQUE | pipeline_runs | run_date | One run per day; idempotent upsert |
| IDX | tickers | current_tranche | Filter active tickers by tranche |

---

## ERD

```
┌─────────────────────────────────────────────────────────┐
│                        tickers                          │
├─────────────────────────────────────────────────────────┤
│ 🔑 symbol           text PK                             │
│    name             text NOT NULL                       │
│    aliases          text[]                              │
│    market_cap       bigint                              │
│    sector           text                                │
│    current_tranche  tranche_enum NOT NULL               │
│    cap_verified     boolean                             │
│    is_active        boolean                             │
│    first_seen_at    timestamptz                         │
│    created_at       timestamptz                         │
│    updated_at       timestamptz                         │
└──────────────┬──────────────────────────────────────────┘
               │ 1
               │
       ┌───────┴────────────────────────────────────────┐
       │                                                 │
       │ N                  │ N              │ N         │ N
       ▼                    ▼                ▼           ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────┐
│apewisdom_       │ │raw_mentions  │ │ticker_daily  │ │ticker_tranche  │
│snapshots        │ │(optional)    │ │_stats        │ │_log            │
├─────────────────┤ ├──────────────┤ ├──────────────┤ ├────────────────┤
│🔑 id     uuid   │ │🔑 id  uuid  │ │🔑 id  uuid   │ │🔑 id  uuid    │
│→  ticker text   │ │→  ticker txt│ │→  ticker text│ │→  ticker text  │
│   snap_date date│ │   post_id   │ │   stat_date  │ │   tranche      │
│   count_24h int │ │   subreddit │ │   days_in_db │ │   prev_tranche │
│   count_7d  int │ │   title     │ │   count_1w   │ │   entered_at   │
│   rank      int │ │   snippet   │ │   count_1mo  │ │   exited_at    │
│   upvotes   int │ │   acct_age  │ │   count_3mo  │ │   velocity_    │
│   created_at    │ │   mention_  │ │   count_6mo  │ │     at_entry   │
│                 │ │     date    │ │   count_1y   │ │   count_       │
│ UNIQUE:         │ │   source    │ │   count_18mo │ │     at_entry   │
│ (ticker,        │ │   created_at│ │   count_2y   │ │   cap_         │
│  snapshot_date) │ │             │ │   velocity_  │ │     at_entry   │
│                 │ │ UNIQUE:     │ │     1w_1mo   │ │   created_at   │
│                 │ │ (ticker,    │ │   velocity_  │ │                │
│                 │ │  post_id)   │ │     1mo_3mo  │ │ exited_at=NULL │
│                 │ │             │ │   accel.     │ │ = current      │
│                 │ │             │ │   sub_spread │ │                │
│                 │ │             │ │   tranche    │ │                │
│                 │ │             │ │ UNIQUE:      │ │                │
│                 │ │             │ │ (ticker,     │ │                │
│                 │ │             │ │  stat_date)  │ │                │
└─────────────────┘ └──────────────┘ └──────────────┘ └────────────────┘

┌─────────────────────────────────────────┐
│              pipeline_runs              │
│         (no FK — standalone log)        │
├─────────────────────────────────────────┤
│ 🔑 id                uuid               │
│    run_date           date UNIQUE        │
│    started_at         timestamptz        │
│    completed_at       timestamptz        │
│    status             run_status_enum    │
│    tickers_processed  integer            │
│    apewisdom_records  integer            │
│    reddit_records     integer            │
│    scores_computed    integer            │
│    tranches_updated   integer            │
│    apewisdom_stale    boolean            │
│    errors             text[]             │
│    duration_ms        integer            │
│    created_at         timestamptz        │
└─────────────────────────────────────────┘
```

---

## Design Decisions

**1. ticker.symbol as natural primary key, not UUID**
Stock ticker symbols are globally unique, immutable in practice, and short.
Using the symbol as PK avoids a join in every query that starts with a symbol
lookup. The downside (company re-uses an old symbol) is extremely rare and
manageable with `is_active = false` on the old record.

**2. aliases stored as text[] array in tickers, not a separate table**
Aliases are always read with the ticker (never queried independently).
Arrays of 2–6 strings are idiomatic in PostgreSQL and avoid a join.
If alias count grows beyond ~10 per ticker, extract to a join table then.

**3. All velocity columns are nullable, not zero**
A NULL velocity means "insufficient data for this window" — not "zero velocity."
Zero and null are semantically different: a ticker with zero mentions in the last
year is different from a ticker that has only been in the dataset for 2 weeks.
The pipeline must propagate nulls correctly, and the dashboard must render them
as "N/A", not "0".

**4. ticker_tranche_log.exited_at is updatable (one exception to append-only)**
The tranche log is conceptually append-only, but open-ended intervals
(exited_at IS NULL = currently in this tranche) require updating one field when
a ticker transitions. Alternative was two separate tables (open_tranches and
closed_tranches) but that adds query complexity. The update is narrow and safe:
only exited_at on the currently-open row.

**5. current_tranche denormalized onto tickers**
The dashboard's tranche overview query is: "give me all tickers in each tranche,
sorted by velocity, as of today." Without denormalization, this requires joining
ticker_daily_stats every time. With current_tranche on tickers, the tranche filter
is a single table scan. Kept in sync by the classify_tranches.py stage.

**6. subreddit_spread on ticker_daily_stats, not computed at query time**
Counting distinct subreddits from raw_mentions per ticker per day is a GROUP BY
query that gets expensive at 2,000 tickers × 730 days. Pre-computing it in the
pipeline and storing it as a column keeps dashboard queries fast. If raw_mentions
is not available (PRAW disabled), subreddit_spread is NULL — the dashboard shows
"N/A" rather than crashing.

**7. pipeline_runs has no FK to tickers**
The pipeline log records the run as a whole, not per-ticker outcomes. A per-ticker
run log would be useful for debugging but adds a 2,000-row-per-day write volume
that isn't needed at this scale. Add it when there are >5,000 tickers.

---

## Latest file

This document supersedes: *(none — first data model)*
