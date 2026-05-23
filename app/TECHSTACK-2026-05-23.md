# Tech Stack: Multi-Tranche Reddit Pre-Breakout Sentiment Monitor

**Generated:** 2026-05-23 02:00
**Status:** Approved

---

## Constraints

**Hard:**
- Solo founder — zero ops overhead; no self-hosted infrastructure
- Infrastructure cost < $200/month total
- Pipeline must run fully unattended every day at 6 AM UTC
- No Reddit PII stored; Reddit ToS compliance required
- Python only — no polyglot complexity

**Soft:**
- Prefer managed services over self-hosted
- Prefer free tiers where available; paid tiers only when the free tier is a real ceiling
- Dashboard must connect directly to DB — no intermediate API layer needed at v1
- All thresholds and config in code, not hardcoded in schema

---

## Stack Overview

| Layer | Technology | Version / Tier |
|-------|------------|----------------|
| Pipeline language | Python | 3.11+ |
| Data ingest — primary | Apewisdom API (HTTP) | Public, no auth |
| Data ingest — secondary | PRAW (Reddit API) | Optional; remove if ToS prohibits |
| Market cap data | yfinance | Latest PyPI |
| Alias extraction | Anthropic Claude API | claude-haiku-4-5 (cheapest, sufficient) |
| Database | Supabase (PostgreSQL 15) | Free → Pro tier |
| DB client (pipeline) | supabase-py | Latest PyPI |
| DB client (dashboard) | supabase-py | Latest PyPI |
| Scheduler / CI-CD | GitHub Actions | Free tier (2,000 min/month) |
| Dashboard | Streamlit | Latest PyPI |
| Dashboard hosting | Streamlit Cloud | Free tier |
| Data processing | pandas | Latest PyPI |
| Charts | plotly | Latest PyPI |
| HTTP client | requests | Latest PyPI |
| Env vars | python-dotenv | Latest PyPI |
| Testing | pytest | Latest PyPI |
| Secrets management | GitHub Actions Secrets + Streamlit Secrets | Built-in |

---

## Architecture Diagram

```
 ┌──────────────────────────────────────────────────────────┐
 │                  GitHub Actions (cron 6 AM UTC)          │
 │                                                          │
 │  ┌────────────────────────────────────────────────────┐  │
 │  │                   pipeline/ (Python)               │  │
 │  │                                                    │  │
 │  │  [1] apewisdom_ingest.py                           │  │
 │  │        │ HTTPS GET                                 │  │
 │  │        ▼                                           │  │
 │  │  apewisdom.io/api/v1.0/filter/all-stocks/page/{n} │  │
 │  │        │ JSON response                             │  │
 │  │        ▼                                           │  │
 │  │  [2] ticker_sync.py  ──── new ticker? ────►        │  │
 │  │                               HTTPS POST           │  │
 │  │                          api.anthropic.com         │  │
 │  │                         (alias extraction)         │  │
 │  │        │                                           │  │
 │  │        ▼                                           │  │
 │  │  [3] market_cap_fetch.py                           │  │
 │  │        │ yfinance (Yahoo Finance unofficial)        │  │
 │  │        │                                           │  │
 │  │        ▼                                           │  │
 │  │  [4] reddit_ingest.py  [OPTIONAL]                  │  │
 │  │        │ PRAW / Reddit API                         │  │
 │  │        │                                           │  │
 │  │        ▼                                           │  │
 │  │  [5] score_compute.py                              │  │
 │  │        │ rolling windows, velocity, acceleration   │  │
 │  │        │                                           │  │
 │  │        ▼                                           │  │
 │  │  [6] tranche_classify.py                           │  │
 │  │        │ phase-gated rules, config-driven          │  │
 │  │        │                                           │  │
 │  │        ▼                                           │  │
 │  │  [7] pipeline_log.py                               │  │
 │  │        │ write pipeline_runs record                │  │
 │  │        │                                           │  │
 │  │        │ PostgreSQL (supabase-py)                  │  │
 │  │        ▼                                           │  │
 │  └─────── Supabase ─────────────────────────────────-─┘  │
 └──────────────────────────────────────────────────────────┘
                           │
                           │ PostgreSQL (supabase-py)
                           ▼
               ┌───────────────────────┐
               │    Supabase           │
               │  (PostgreSQL 15)      │
               │                       │
               │  tickers              │
               │  apewisdom_snapshots  │
               │  raw_mentions         │
               │  ticker_daily_stats   │
               │  ticker_tranche_log   │
               │  pipeline_runs        │
               └───────────┬───────────┘
                           │
                           │ PostgreSQL (supabase-py)
                           ▼
               ┌───────────────────────┐
               │   Streamlit Cloud     │
               │   (dashboard/)        │
               │                       │
               │   Tranche Overview    │
               │   Ticker Detail View  │
               │   Daily Digest        │
               │   Ticker Search       │
               └───────────────────────┘
                           ▲
                           │ HTTPS
                      [Browser — sole user]
```

---

## Layer Decisions

### Pipeline Language

**Chosen:** Python 3.11+
**Rejected alternatives:** None — Python is the only viable choice given the ecosystem (PRAW, yfinance, supabase-py, anthropic, streamlit all have first-class Python SDKs; none have a mature alternative in any other language for this use case).
**Rationale:** Ecosystem fit is perfect. Every dependency has a maintained PyPI package. GitHub Actions supports Python natively. Streamlit is Python-only.
**Risks:** Python concurrency model is a non-issue for daily batch; GIL does not matter here.

---

### Primary Data Source — Apewisdom API

**Chosen:** Apewisdom public API (`apewisdom.io/api/v1.0/filter/all-stocks/page/{n}`)
**Rejected alternatives:**
- Raw Reddit scraping as primary — too fragile, higher ToS risk, harder to paginate all tickers
- StockTwits / Twitter — out of scope v1
**Rationale:** Free, no auth, returns pre-aggregated 24h and 7d mention counts with rank and upvotes across multiple subreddits. This is exactly the signal needed for Tier 3 scoring from Day 1. Covers 500–2,000 tickers per daily poll with ~5–10 paginated requests.
**Risks:** No SLA, unofficial service. Mitigation: graceful degradation (if API unreachable, log `apewisdom_stale=true` and continue with previous day's data; alert on 3+ consecutive stale days).

---

### Secondary Data Source — Reddit API (PRAW)

**Chosen:** PRAW (Python Reddit API Wrapper) — **OPTIONAL, conditionally included**
**Rejected alternatives:** Direct PRAW-less HTTP scraping — more fragile, same ToS exposure
**Rationale:** Used only for post title / excerpt context shown in the ticker detail view (up to 5 posts per ticker). Not required for scoring. The entire pipeline runs without it.
**Risks:** Reddit's Responsible Builder Policy may prohibit automated scraping for commercial analysis tools. Decision: if ToS review concludes PRAW is not viable, remove this component entirely. The scoring system is unaffected.
**If included:** ~100 API calls/day total; well within Reddit free tier limits.

---

### Market Cap Data — yfinance

**Chosen:** yfinance
**Rejected alternatives:**
- Financial Modeling Prep (FMP) — 250 calls/day free tier is sufficient, but adds another API key to manage; yfinance is zero-config
- Alpha Vantage — 25 calls/day free tier is insufficient for 500–2,000 tickers; paid tier defeats the cost goal
- Polygon.io — free tier too limited; paid tier ~$30/mo just for market cap is disproportionate
**Rationale:** yfinance is a well-maintained Python library (pinned to specific version to avoid breakage), zero auth, works for daily market cap polls at this scale. Wraps Yahoo Finance unofficial API.
**Risks:** Unofficial Yahoo Finance API. Yahoo has broken yfinance integrations before. Mitigation: pin yfinance version, wrap all calls in try/except, cache last known market cap in `tickers.market_cap` — if yfinance fails for a ticker, use the stored value and flag `cap_verified=false`.

---

### Ticker Alias Extraction — Anthropic Claude API

**Chosen:** Anthropic Claude API (`claude-haiku-4-5`) — used sparingly
**Rejected alternatives:**
- Regex + hardcoded alias map — brittle for company name variations ("Rocket Lab" vs "RocketLab" vs "RKLB")
- spaCy NER — requires training data; not worth it for this use case
- GPT-4o — more expensive, no meaningful quality advantage for this task
**Rationale:** Called only when a new ticker appears in Apewisdom that is not yet in the `tickers` table. Generates a list of common aliases (company name, abbreviations, informal references). At ~$0.001 per call and <20 new tickers/day, monthly cost is well under $1.
**Risks:** API latency adds ~1–2 seconds per new ticker to pipeline runtime. Acceptable — new-ticker volume is small.

---

### Database — Supabase (PostgreSQL 15)

**Chosen:** Supabase free tier → Pro tier as data grows
**Rejected alternatives:**
- SQLite (local file) — not accessible to GitHub Actions and Streamlit Cloud simultaneously; no multi-process safety
- Raw PostgreSQL on Railway / Render — more ops overhead; Supabase free tier is generous (500 MB) and provides a built-in dashboard for manual inspection
- PlanetScale (MySQL) — wrong DB family; all schema is PostgreSQL-specific (enums, uuid, timestamptz)
**Rationale:** Managed PostgreSQL with a free tier that covers ~6+ months of daily data at 2,000 tickers. Dashboard and pipeline both connect with the same supabase-py SDK. Supabase Studio provides manual table inspection without writing SQL.
**Risks:** Supabase free tier pauses after 1 week of inactivity. Mitigation: daily GitHub Actions cron keeps the DB active. Free tier storage limit (~500 MB) hit at roughly 6–12 months. Pro tier ($25/month) is well within budget.

---

### Scheduler — GitHub Actions

**Chosen:** GitHub Actions (`schedule: cron: '0 6 * * *'`)
**Rejected alternatives:**
- Cron on VPS — requires a persistent server; unnecessary ops overhead for a daily batch job
- Render cron jobs — free tier too limited; adds another platform to manage
- Airflow / Prefect — wildly over-engineered for a single-DAG daily pipeline with 7 sequential stages
**Rationale:** Free tier provides 2,000 minutes/month; pipeline is expected to run in <60 minutes (well under budget). Zero servers to maintain. Native GitHub Secrets for credential management. Email notification on workflow failure is built in.
**Risks:** GitHub Actions free tier may have queue delays during peak hours. Acceptable — the digest target is 7 AM; a 6 AM trigger with 60-minute runtime gives 60 minutes of headroom.

---

### Dashboard — Streamlit + Streamlit Cloud

**Chosen:** Streamlit (Python), hosted on Streamlit Cloud
**Rejected alternatives:**
- Metabase — no-code BI, but limited custom chart types; cannot build the custom tranche view and velocity sparklines needed
- Grafana — strong time-series visualization but no Python-native data processing; requires Grafana-specific query language
- Next.js / React — massively over-engineered for a single-user personal tool; requires a separate backend API, TypeScript, deployment pipeline
- Vercel — cannot host a persistent Python Streamlit server; Streamlit apps need a long-lived process
**Rationale:** Streamlit is Python-native, connects to Supabase with the same SDK used in the pipeline, runs on Streamlit Cloud for free (1 app, public or private), and can be built end-to-end without switching languages. Dashboard state (which tickers to show, date range) is handled by Streamlit session state — no separate state management needed.
**Risks:** Streamlit free tier puts apps to sleep after 7 days of inactivity. Mitigation: visit the dashboard at least once per week, or upgrade to Streamlit Community Cloud (free). Cold wake takes ~10 seconds; acceptable for a personal tool.

---

### Observability

**Chosen:** GitHub Actions built-in logs + `pipeline_runs` table in Supabase
**Rejected alternatives:**
- Datadog / Sentry — overkill and cost at this scale
- Custom logging service — unnecessary ops overhead
**Rationale:** The `pipeline_runs` table records every run's status, error list, and stage-level counts. GitHub Actions emails on workflow failure. The Streamlit dashboard includes a "Pipeline Health" view reading from `pipeline_runs`. This is sufficient for a solo operator.
**Risks:** No real-time alerting. Mitigation: GitHub Actions failure email is immediate; Streamlit health view makes degraded runs visible on daily dashboard check.

---

## Key Architectural Decisions

| Decision | Options Considered | Choice | Reversibility |
|----------|--------------------|--------|---------------|
| Dashboard framework | Streamlit, Next.js, Metabase, Grafana | Streamlit | Easy — dashboard is read-only; swap anytime |
| Scheduler | GitHub Actions, VPS cron, Airflow, Render cron | GitHub Actions | Easy — pipeline is self-contained Python; move to any runner |
| Database | Supabase, SQLite, raw PostgreSQL, PlanetScale | Supabase (PostgreSQL) | Hard — schema is PostgreSQL-specific; migration to another DB requires data export + schema rewrite |
| Apewisdom as sole required source | Apewisdom + Reddit required, Reddit only, scraping only | Apewisdom required / Reddit optional | Easy — Reddit ingest is isolated; removing it requires deleting one pipeline stage and making `raw_mentions` optional in dashboard |
| Raw/computed table separation | Single denormalized table, separate raw+computed | Separate (raw append-only, computed rebuildable) | Painful to collapse — the ML retraining use case requires raw immutability |

---

## What We Will NOT Use and Why

| Technology | Reason |
|------------|--------|
| Vercel | Stateless serverless — cannot host a persistent Python/Streamlit process |
| Airflow / Prefect | Overkill for a single sequential daily pipeline; adds servers and UI to maintain |
| Docker / Kubernetes | Unnecessary complexity; GitHub Actions provides a clean Python environment natively |
| Redis / Celery | No concurrent task queue needed — pipeline stages run sequentially |
| Auth (Clerk, Auth0, Supabase Auth) | v1 is single-user; no auth required |
| GraphQL | No client-driven query needs; Supabase direct SQL is simpler and faster |
| Playwright / Selenium | Reddit data comes from API (PRAW) or Apewisdom — no browser automation needed |
| StockTwits / Twitter API | Out of scope v1; adds cost and credential management for marginal signal gain |
| Financial Modeling Prep | yfinance is zero-config and covers the same market cap use case at no cost |

---

## Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Apewisdom API goes down or changes schema | High | Cache last known snapshot per ticker; log `apewisdom_stale=true`; alert after 3 consecutive stale days. Fallback: PRAW-based counting if Reddit is available. |
| yfinance breaks due to Yahoo Finance API change | Medium | Pin yfinance version in `requirements.txt`; fallback to cached `tickers.market_cap` value; `cap_verified=false` flag prevents tranche misclassification. |
| Supabase free tier storage exhausted | Low | At ~500 MB free and ~1 KB/ticker/day for computed stats, runway is ~6–12 months at 2,000 tickers. Monitor in `pipeline_runs`. Upgrade to Supabase Pro ($25/mo) when needed — within budget. |

---

## Repository Structure

```
reddit-stocks/
└── app/
    ├── pipeline/               # Daily batch pipeline stages
    │   ├── config.py           # All thresholds and configurable constants
    │   ├── apewisdom_ingest.py
    │   ├── ticker_sync.py
    │   ├── market_cap_fetch.py
    │   ├── reddit_ingest.py    # OPTIONAL
    │   ├── score_compute.py
    │   ├── tranche_classify.py
    │   └── pipeline_log.py
    ├── dashboard/              # Streamlit dashboard
    │   ├── app.py              # Main entry point
    │   ├── pages/
    │   │   ├── tranche_overview.py
    │   │   ├── ticker_detail.py
    │   │   ├── daily_digest.py
    │   │   └── pipeline_health.py
    │   └── components/         # Reusable Streamlit widgets
    ├── db/
    │   └── schema.sql          # PostgreSQL DDL
    ├── tests/                  # pytest test suite
    ├── requirements.txt        # Pinned dependencies
    ├── .env.example            # Documented env var template
    └── .github/
        └── workflows/
            └── daily_pipeline.yml   # Cron job definition
```

---

## Environment Variables

| Variable | Used By | Source |
|----------|---------|--------|
| `SUPABASE_URL` | pipeline, dashboard | GitHub Secrets + Streamlit Secrets |
| `SUPABASE_SERVICE_KEY` | pipeline (write access) | GitHub Secrets |
| `SUPABASE_ANON_KEY` | dashboard (read access) | Streamlit Secrets |
| `ANTHROPIC_API_KEY` | ticker_sync.py | GitHub Secrets |
| `REDDIT_CLIENT_ID` | reddit_ingest.py (optional) | GitHub Secrets |
| `REDDIT_CLIENT_SECRET` | reddit_ingest.py (optional) | GitHub Secrets |
| `REDDIT_USER_AGENT` | reddit_ingest.py (optional) | GitHub Secrets |

---

## Latest file

This document supersedes: none (first version)
