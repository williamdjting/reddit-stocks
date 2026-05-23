# Architecture: Multi-Tranche Reddit Pre-Breakout Sentiment Monitor

**Generated:** 2026-05-23 01:30

## Overview

A daily-batch Python pipeline ingests Reddit stock mention data from Apewisdom
(primary) and optionally Reddit API (secondary, subject to ToS), computes
multi-horizon velocity and tranche scores, and stores everything in Supabase
(PostgreSQL). A Streamlit dashboard reads directly from Supabase to display
tranche classifications, ticker trajectories, and daily digest views. The entire
system runs unattended via GitHub Actions cron — no manual intervention required.

---

## Constraints

| Constraint | Value | Implication |
|---|---|---|
| Users at launch | 1 (personal tool) | No auth, no multi-tenancy, no rate limiting needed |
| Users at 12 months | 1–500 (if SaaS) | Supabase free tier handles this; upgrade path is clear |
| Team size | 1 (solo founder) | Minimal ops overhead is a hard requirement |
| Pipeline latency | Daily batch, <4h | No streaming, no queues, sequential stages are fine |
| Dashboard latency | <3s page load | Pre-aggregated scores in DB, no real-time computation |
| Availability | Dashboard can have brief downtime; pipeline must run daily | GitHub Actions has 99.9%+ reliability; acceptable for daily cron |
| Budget ceiling | $200/month total | Free tiers cover everything except Claude API (~$5–15/mo) |
| Compliance | Reddit ToS, no GDPR/HIPAA | Rate-limit all Reddit calls; no PII stored |

---

## Components

```
Component: Apewisdom Ingester
Purpose:   Fetches daily aggregate mention counts and rankings for all tracked
           tickers across subreddits from the Apewisdom public API.
Tech:      Python, requests
Owns:      apewisdom_snapshots table (append-only, never modified)
Exposes:   Nothing — writes to DB
Depends:   Apewisdom API, Supabase

Component: Reddit Ingester [OPTIONAL — subject to ToS review]
Purpose:   Fetches top post titles and excerpts per subreddit to provide
           human-readable context in the ticker detail view.
Tech:      Python, PRAW
Owns:      raw_mentions table
Exposes:   Nothing — writes to DB
Depends:   Reddit API, Supabase
Note:      Entire pipeline functions without this component. If Reddit API
           ToS prohibits use case, this component is permanently removed.

Component: Ticker Registry
Purpose:   Maintains the master list of tracked tickers, refreshes daily
           market cap, and resolves company name aliases for new tickers.
Tech:      Python, yfinance, Anthropic Claude API
Owns:      tickers table
Exposes:   Nothing — writes to DB
Depends:   yfinance, Claude API, Supabase

Component: Scoring Engine
Purpose:   Reads raw mention history and computes rolling mention counts
           across 7 time windows, velocity, acceleration, and subreddit
           diversity score for every active ticker.
Tech:      Python, pandas
Owns:      ticker_daily_stats table
Exposes:   Nothing — writes to DB
Depends:   Supabase (reads apewisdom_snapshots)

Component: Tranche Classifier
Purpose:   Applies phase-gated tranche rules to each ticker's daily scores
           and records transitions in the tranche log.
Tech:      Python
Owns:      ticker_tranche_log table; updates tickers.current_tranche
Exposes:   Nothing — writes to DB
Depends:   Supabase (reads ticker_daily_stats)

Component: Pipeline Orchestrator
Purpose:   Sequences all pipeline stages, logs run outcomes, and surfaces
           failures via GitHub Actions native email notification.
Tech:      GitHub Actions YAML (cron schedule)
Owns:      pipeline_runs table (reliability log)
Exposes:   workflow_dispatch (manual trigger)
Depends:   All pipeline components, Supabase

Component: Database
Purpose:   Single persistent store for all raw ingestion data, computed
           scores, ticker metadata, tranche history, and pipeline logs.
Tech:      Supabase (managed PostgreSQL)
Owns:      All data
Exposes:   PostgreSQL connection string, supabase-py SDK
Depends:   Nothing

Component: Dashboard
Purpose:   Read-only web interface showing tranche overview, ticker detail
           with historical charts, and daily digest of signal changes.
Tech:      Streamlit, supabase-py, Plotly
Owns:      Nothing (read-only)
Exposes:   Web UI (Streamlit Cloud URL)
Depends:   Supabase
```

---

## Data Flow

### Daily Pipeline (GitHub Actions, 6 AM UTC)

```
┌─────────────────────────────────────────────────────────────────┐
│                   GitHub Actions — daily cron                    │
│                                                                  │
│  Stage 1          Stage 2*           Stage 3                    │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Apewisdom  │  │    Reddit    │  │    Ticker Registry    │  │
│  │  Ingester   │  │   Ingester   │  │  yfinance + Claude    │  │
│  │             │  │   (PRAW)     │  │  API (new tickers     │  │
│  │ apewisdom   │  │ raw_mentions │  │  only)                │  │
│  │ _snapshots  │  │   (context   │  │  tickers table        │  │
│  │             │  │    only)     │  │                       │  │
│  └──────┬──────┘  └──────┬───────┘  └───────────┬───────────┘  │
│         │                │ (optional)            │              │
│  Stage 4 ───────────────────────────────────────┘              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Scoring Engine                        │    │
│  │  Reads apewisdom_snapshots → rolling windows (1w to 2y) │    │
│  │  Computes: velocity · acceleration · subreddit_spread    │    │
│  │  Writes: ticker_daily_stats (upsert by ticker + date)    │    │
│  └───────────────────────────┬─────────────────────────────┘    │
│                              │                                   │
│  Stage 5                     │                                   │
│  ┌───────────────────────────▼─────────────────────────────┐    │
│  │                  Tranche Classifier                      │    │
│  │  Reads ticker_daily_stats → applies phase-gated rules   │    │
│  │  Tier 3 (Day 1+) · Tier 2 (Month 6+) · Tier 1 (Mo 12+) │    │
│  │  Writes: tickers.current_tranche                        │    │
│  │  Appends: ticker_tranche_log (on transition only)       │    │
│  └───────────────────────────┬─────────────────────────────┘    │
│                              │                                   │
│  Stage 6                     │                                   │
│  ┌───────────────────────────▼─────────────────────────────┐    │
│  │                   Run Logger                             │    │
│  │  Upserts: pipeline_runs (status, counts, errors, ms)    │    │
│  │  On failure: GitHub Actions sends email notification     │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ upserts / appends
                    ┌──────────▼───────────┐
                    │   Supabase           │
                    │   (PostgreSQL)       │
                    │ ─────────────────── │
                    │ apewisdom_snapshots  │◀── append-only
                    │ raw_mentions*        │◀── append-only (optional)
                    │ tickers              │◀── upsert daily
                    │ ticker_daily_stats   │◀── upsert by ticker+date
                    │ ticker_tranche_log   │◀── append on transition
                    │ pipeline_runs        │◀── upsert by run_date
                    └──────────┬───────────┘
                               │ reads (supabase-py)
                    ┌──────────▼───────────┐
                    │  Streamlit Dashboard  │
                    │  (Streamlit Cloud)   │
                    │ ─────────────────── │
                    │ Tranche Overview     │
                    │ (3 columns, sorted   │
                    │  by velocity)        │
                    │                      │
                    │ Ticker Detail View   │
                    │ (charts + excerpts)  │
                    │                      │
                    │ Daily Digest View    │
                    │ (new entries +       │
                    │  transitions)        │
                    └──────────────────────┘

* Stage 2 (Reddit Ingester) is optional and dropped if ToS prohibits it.
  All other stages function fully without it.
```

### Dashboard Read Path (user opens browser)

```
User → Streamlit Cloud → supabase-py → Supabase (PostgreSQL)
                                     → ticker_daily_stats  (charts)
                                     → tickers             (metadata)
                                     → ticker_tranche_log  (history)
                                     → apewisdom_snapshots (raw counts)
                      ← Plotly charts rendered in browser
```

---

## Integration Points

```
Service:       Apewisdom API
URL:           https://apewisdom.io/api/v1.0/filter/all-stocks/page/{n}
Purpose:       Daily aggregate mention counts per ticker across subreddits
Data in:       GET request, page parameter
Data out:      JSON — ticker, mentions_24h, mentions_7d, rank, upvotes
Rate limit:    Unknown (unofficial, no documented limit) — add 1s delay between pages
Failure mode:  HTTP error or timeout → log failure, skip stage, continue pipeline
               Scores computed on most recent successful snapshot
Fallback:      Previous day's apewisdom_snapshots used for current-day velocity calc
               Flag in pipeline_runs: apewisdom_stale = true

Service:       Reddit API (PRAW) [OPTIONAL]
Purpose:       Post titles/excerpts for context only (~100 calls/day)
Data in:       Subreddit name, limit, sort
Data out:      Post title, selftext snippet, author account age, created_utc
Rate limit:    60 requests/minute (free tier personal use)
Failure mode:  Auth failure or rate limit → skip stage, Apewisdom-only mode
Fallback:      Dashboard shows "context unavailable" in excerpt section
               Full classification still works — context is cosmetic only

Service:       yfinance (Yahoo Finance)
Purpose:       Daily market cap and sector per ticker
Data in:       Ticker symbol list
Data out:      market_cap, sector, longName
Rate limit:    Unofficial — add 0.5s delay between tickers; batch where possible
Failure mode:  Yahoo changes API format (happens ~1x/year) → use cached market_cap
               Flag ticker as cap_verified = false; alert in pipeline_runs
Fallback:      Last known market cap retained; tranche gates applied to cached value

Service:       Anthropic Claude API
Purpose:       Alias extraction for new tickers only (company name → $SYMBOL mapping)
Data in:       Company name string
Data out:      Ticker symbol, common aliases array
Usage:         Called only for tickers not yet in the tickers table — very infrequent
Failure mode:  API error or quota → skip alias extraction; ticker tracked by symbol only
Fallback:      Exact symbol match still works; aliases added on next successful run

Service:       Supabase (PostgreSQL)
Purpose:       Primary and only data store — all pipeline reads and writes
Data in/out:   All application data
Rate limit:    Free tier: 500MB storage, 2GB bandwidth/month, 50MB file uploads
Failure mode:  Connection failure → entire pipeline fails; logged; email sent
Fallback:      None — Supabase is the critical path. Use paid plan ($25/mo) before
               hitting free tier limits (~6 months at current data rate estimate)

Service:       GitHub Actions
Purpose:       Daily cron scheduler for pipeline
Failure mode:  GitHub outage (rare) → pipeline misses a day; no data loss
               Next day runs normally; idempotent design means no gap in data
Fallback:      workflow_dispatch allows manual trigger from GitHub UI
```

---

## Architectural Decisions

### ADR-001: Apewisdom as primary source, Reddit API as optional secondary

**Decision:** Apewisdom API is the sole required data source for mention counts.
Reddit API (PRAW) is optional and dropped if ToS review prohibits the use case.

**Reason:** Apewisdom already aggregates Reddit mention counts across subreddits —
it solves the counting problem without direct Reddit API dependency. Reddit's 2023
API policy changes introduced commercial use restrictions and rate limits that make
direct scraping or heavy API use risky for a product that may eventually charge users.
The Apewisdom signal is sufficient for velocity and tranche scoring.

**Rejected alternative:** Direct Reddit API as primary. Creates ToS risk for the
commercial SaaS path and requires managing auth credentials, rate limits, and ToS
compliance across API versions.

**Reversibility:** High — Reddit ingester can be added later once ToS path is clear.
The raw_mentions table schema is already in place.

---

### ADR-002: GitHub Actions for scheduling, not a dedicated worker

**Decision:** GitHub Actions cron job as the pipeline scheduler.

**Reason:** A dedicated worker (Railway, Render, Fly.io) adds $5–20/month of
infrastructure, requires server management, and is overkill for one daily job
that runs for <4 hours. GitHub Actions free tier provides 2,000 minutes/month —
a 2-hour daily pipeline uses ~60 minutes/day = 1,800 minutes/month, within the
free tier. Pipeline logs are visible in the GitHub UI without any additional tooling.

**Rejected alternative:** Celery + Redis, Airflow — far too heavy for a single
daily batch job run by one person. Render/Railway cron — adds a hosting cost and
another service to manage.

**Reversibility:** High — if the pipeline grows beyond GitHub Actions limits,
moving to a dedicated scheduler is a config change, not an architecture rewrite.

---

### ADR-003: Supabase over raw PostgreSQL or SQLite

**Decision:** Supabase (managed PostgreSQL).

**Reason:** Supabase provides managed Postgres with a Python SDK, a built-in
table viewer (useful for debugging the pipeline), automatic backups, and a REST
API that Streamlit can query directly. The free tier covers the first ~6 months
of data volume. SQLite would be simpler but cannot be accessed from Streamlit
Cloud (no shared filesystem). Raw PostgreSQL on a VPS adds server management
overhead the founder wants to avoid.

**Rejected alternative:** SQLite — no remote access for Streamlit Cloud.
PlanetScale — MySQL dialect, worse fit for time-series aggregations.

**Reversibility:** Medium — migrating away from Supabase requires a data export
and new connection config, but the schema is standard PostgreSQL.

---

### ADR-004: Separate raw and computed tables, never one big table

**Decision:** Raw ingestion tables (apewisdom_snapshots, raw_mentions) are
separate from computed tables (ticker_daily_stats, ticker_tranche_log).

**Reason:** Raw data is the ground truth. Computed scores are a function of
raw data and the scoring algorithm. Separating them means: (1) the scoring
algorithm can be changed and rerun without re-scraping anything; (2) raw data
is never accidentally overwritten by a scoring bug; (3) ticker_tranche_log
accumulates over time as a labeled training set for future ML — this only works
if raw and computed are never conflated.

**Rejected alternative:** One wide denormalized table with raw counts and computed
scores in the same row. Easier to query but makes recomputation risky and destroys
the ML training set value of the tranche history.

**Reversibility:** Low — schema separation is baked into the pipeline from day one.

---

### ADR-005: Phase-gated tranche activation

**Decision:** Tier 2 and Tier 1 tranches do not activate until the dataset has
6 and 12 months of data respectively, regardless of what the velocity scores say.

**Reason:** A ticker that appeared in the dataset 3 weeks ago cannot be classified
as a "2-year Seed signal" — there is no data to support the claim. Activating
all tranches from day 1 would produce false signals and destroy trust in the
product. Showing a "maturing — Tier 2 activates [date]" placeholder is honest
and sets correct expectations.

**Rejected alternative:** Classify all tranches from day 1 with a confidence
weighting. Adds complexity without meaningful signal improvement in the early
months; introduces a parameter that would require tuning before any data exists.

**Reversibility:** High — the activation dates are config parameters.

---

### ADR-006: Streamlit over Next.js for the dashboard

**Decision:** Streamlit (Python) deployed on Streamlit Cloud.

**Reason:** The founder is a Python developer. Streamlit lets the dashboard be
built in the same language as the pipeline — no context switching, no JavaScript
build tooling, no separate deployment pipeline. Plotly charts are native.
Streamlit Cloud deploys from GitHub with zero config. For a personal tool with
1 user, this is the right call.

**Rejected alternative:** Next.js on Vercel — requires JavaScript/TypeScript,
a separate deployment pipeline, and an API layer or Supabase client library in JS.
Correct choice if/when this becomes a multi-user SaaS and the UI needs to be
polished for paying customers. Not correct for a solo founder's personal tool today.

**Upgrade path:** When the product needs a production-grade UI for paying users,
replace Streamlit with Next.js + Supabase JS client on Vercel. The database
schema and pipeline are unchanged.

---

## Deployment Topology

```
Environment:   Production only (no staging — personal tool, solo founder)

Pipeline:
  Runtime:     GitHub Actions (Ubuntu runner, free tier)
  Schedule:    cron: '0 6 * * *'  (6:00 AM UTC daily)
  Trigger:     Also via workflow_dispatch (manual)
  Secrets:     GitHub repo secrets
               SUPABASE_URL, SUPABASE_SERVICE_KEY
               ANTHROPIC_API_KEY
               REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET (if PRAW enabled)
  Retry:       3 attempts with 5-minute backoff on failure
  Notification: GitHub Actions native email on job failure

Database:
  Provider:    Supabase (managed PostgreSQL)
  Plan:        Free tier → upgrade to Pro ($25/mo) when storage >400MB
  Backups:     Supabase automated daily backups (7-day retention on free tier)
  Connection:  Via SUPABASE_URL + service key (pipeline) and anon key (dashboard)

Dashboard:
  Provider:    Streamlit Cloud
  Plan:        Free tier (1 app, public URL)
  Deploy:      Connected to GitHub repo — auto-deploys on push to main
  Auth:        None (personal use) — add Streamlit built-in password protection
               if/when access needs to be restricted

Repo structure:
  app/
  ├── pipeline/
  │   ├── ingest_apewisdom.py     ← Stage 1
  │   ├── ingest_reddit.py        ← Stage 2 (optional)
  │   ├── update_tickers.py       ← Stage 3
  │   ├── compute_scores.py       ← Stage 4
  │   ├── classify_tranches.py    ← Stage 5
  │   ├── log_run.py              ← Stage 6
  │   └── config.py               ← all thresholds as named constants
  ├── dashboard/
  │   └── streamlit_app.py
  ├── db/
  │   └── schema.sql
  ├── .github/
  │   └── workflows/
  │       └── daily_pipeline.yml
  ├── requirements.txt
  └── .env.example
```

---

## Known Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Apewisdom API goes down or changes format | High | Unofficial service with no SLA. Pipeline designed to degrade gracefully — skip stage, use previous day's data. Build format detection to catch API changes early. Monitor via pipeline_runs.apewisdom_stale flag. |
| Reddit API ToS prohibits use case | Medium | Already treated as optional. Entire system functions on Apewisdom-only. PRAW ingester is a bonus, not a dependency. |
| yfinance breaks (Yahoo Finance unofficial) | Medium | Add 48-hour cache on market cap — if fetch fails, use last known value. Flag ticker as cap_unverified. yfinance has broken ~3x in the past 3 years but is quickly patched by the OSS community. |
| Supabase free tier storage limit (500MB) | Medium | Raw mention data grows ~5–10MB/day. Free tier exhausted in ~3–6 months at full scale. Upgrade path to $25/mo Pro plan is clear. Monitor storage weekly via pipeline metadata. |
| Pipeline runs but scores are silently wrong | Medium | Each stage logs record counts to pipeline_runs. A stage that processes 0 tickers when 500 are expected is flagged as anomalous. Add assertion: if len(results) < 10, raise an error before writing. |
| GitHub Actions free tier minutes exhausted | Low | 2,000 min/month free. Pipeline running 2h/day = ~60 min/day = 1,800 min/month. Tight but within limits. Optimise pipeline to run in <1 hour to create headroom. |

---

## Latest file

This document supersedes: *(none — first architecture doc)*
