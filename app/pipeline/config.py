"""
Pipeline configuration — all classification thresholds, formulas, and constants.

Every number that affects tranche classification lives here.
Change a value here; the entire pipeline picks it up on the next run.
No schema migrations needed for threshold changes.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Data maturity gates
# ─────────────────────────────────────────────────────────────────────────────

# Minimum days in dataset before any tranche classification is attempted.
# Tickers below this threshold receive tranche = 'insufficient_data'.
# Source: CURRENT_DATE - tickers.first_seen_at::date  (NOT count of snapshot rows)
INSUFFICIENT_DATA_MIN_DAYS: int = 90

# Minimum days before Tier 2 (Early) classification is eligible.
TIER2_MIN_DAYS_IN_DATASET: int = 180  # ~6 months

# Minimum days before Tier 1 (Seed) classification is eligible.
TIER1_MIN_DAYS_IN_DATASET: int = 365  # ~12 months

# ─────────────────────────────────────────────────────────────────────────────
# Tier 3 — Pre-pop  (active from Day 1, no phase gate)
# ─────────────────────────────────────────────────────────────────────────────

# Weekly mention count threshold (from ticker_daily_stats.mention_count_1w)
TIER3_MIN_WEEKLY_MENTIONS: int = 300

# Minimum week-over-week growth rate (as a ratio: 1.50 = 50% growth)
# Applied when weekly mentions are below TIER3_MIN_WEEKLY_MENTIONS but velocity is high.
TIER3_WOW_GROWTH_THRESHOLD: float = 1.50

# Minimum number of distinct subreddits mentioning the ticker in the past 30 days
TIER3_MIN_SUBREDDIT_SPREAD: int = 3

# Maximum market cap (USD). Tickers above this are excluded from Tier 3.
TIER3_MAX_MARKET_CAP: int = 20_000_000_000  # $20B

# ─────────────────────────────────────────────────────────────────────────────
# Tier 2 — Early  (active after TIER2_MIN_DAYS_IN_DATASET)
# ─────────────────────────────────────────────────────────────────────────────

TIER2_MIN_WEEKLY_MENTIONS: int = 50
TIER2_MAX_WEEKLY_MENTIONS: int = 300
TIER2_MAX_MARKET_CAP: int = 10_000_000_000  # $10B

# Both of these velocity windows must be positive (>1.0) for Early classification.
TIER2_MIN_VELOCITY_3MO_VS_6MO: float = 1.0
TIER2_MIN_VELOCITY_1MO_VS_3MO: float = 1.0

# ─────────────────────────────────────────────────────────────────────────────
# Tier 1 — Seed  (active after TIER1_MIN_DAYS_IN_DATASET)
# ─────────────────────────────────────────────────────────────────────────────

TIER1_MIN_WEEKLY_MENTIONS: int = 5
TIER1_MAX_WEEKLY_MENTIONS: int = 50
TIER1_MAX_MARKET_CAP: int = 5_000_000_000  # $5B

# Both of these velocity windows must be positive (>1.0) for Seed classification.
TIER1_MIN_VELOCITY_6MO_VS_1Y: float = 1.0
TIER1_MIN_VELOCITY_3MO_VS_6MO: float = 1.0

# ─────────────────────────────────────────────────────────────────────────────
# Quality filter
# ─────────────────────────────────────────────────────────────────────────────

# Tickers with market cap below this are excluded from all tranches (OTC / micro-cap noise).
QUALITY_MIN_MARKET_CAP: int = 50_000_000  # $50M

# Maximum ratio of mentions from accounts younger than QUALITY_MIN_ACCOUNT_AGE_DAYS.
# Exceeding this ratio triggers 'noise' classification (coordinated pump signal).
QUALITY_MAX_NEW_ACCOUNT_RATIO: float = 0.80

# Account age threshold (days). Accounts younger than this are flagged as "new".
QUALITY_MIN_ACCOUNT_AGE_DAYS: int = 30

# Subreddits in this list are known pump-and-dump communities.
# Tickers where ALL mentions in the past 7 days came from these subreddits → 'noise'.
# Editable here without code changes.
PUMP_SUBREDDIT_BLOCKLIST: list[str] = [
    "r/pennystocks",
    "r/RobinHoodPennyStocks",
    "r/StonkFeed",
    "r/OTCstocks",
]

# ─────────────────────────────────────────────────────────────────────────────
# Noise detection
# ─────────────────────────────────────────────────────────────────────────────
#
# Algorithm: a ticker is classified 'noise' if it shows a large single-week spike
# that is NOT supported by sustained prior volume.
#
# Specifically:
#   noise = (mention_count_1w > NOISE_SPIKE_ABS_THRESHOLD)
#         AND (monthly_weekly_avg < mention_count_1w * NOISE_SUSTAINED_RATIO)
#
# where monthly_weekly_avg = mention_count_1mo / 4.33
#
# Interpretation: the spike week is more than (1/NOISE_SUSTAINED_RATIO) times
# larger than the average week in the prior month. Default: spike > 5× average.

# Minimum weekly mentions to trigger the noise spike check.
# Below this, even a disproportionate spike is too small to classify as noise.
NOISE_SPIKE_ABS_THRESHOLD: int = 100

# If the prior monthly weekly average is below this fraction of the current week,
# the current week is a spike without sustained build → noise.
# 0.20 means: prior avg must be at least 20% of spike week, else it's noise.
NOISE_SUSTAINED_RATIO: float = 0.20

# ─────────────────────────────────────────────────────────────────────────────
# Velocity formula
# ─────────────────────────────────────────────────────────────────────────────
#
# velocity(short_window, long_window) = weekly_rate(short) / weekly_rate(long)
#
# where weekly_rate(window) = mention_count_for_window / weeks_in_window
#
# Result interpretation:
#   > 1.0 = accelerating (short-term rate above long-term average)
#   = 1.0 = flat (same rate across both windows)
#   < 1.0 = decelerating
#   None   = cannot compute (one or both windows have no data)
#
# Edge cases:
#   - If long_window_count == 0 AND short_window_count > 0: velocity = +inf
#     → treat as high acceleration; classifier should check for noise first
#   - If long_window_count == 0 AND short_window_count == 0: velocity = None
#   - If short_window_count is None (window not available): velocity = None

WEEKS_IN_WINDOW: dict[str, float] = {
    "1w":  1.0,
    "1mo": 4.33,
    "3mo": 13.0,
    "6mo": 26.0,
    "1y":  52.0,
    "18mo": 78.0,
    "2y":  104.0,
}


def compute_velocity(
    short_count: int | None,
    long_count: int | None,
    short_key: str,
    long_key: str,
) -> float | None:
    """
    Compute normalised weekly rate ratio between two mention windows.

    Returns None if either window has no data (insufficient history).
    Returns None if long_count is 0 and short_count is also 0 (dead ticker).
    Returns a large sentinel (999.0) if long_count is 0 and short_count > 0
    (brand-new spike with no prior history — handled as pre_pop candidate or noise).
    """
    if short_count is None or long_count is None:
        return None
    short_weeks = WEEKS_IN_WINDOW[short_key]
    long_weeks = WEEKS_IN_WINDOW[long_key]
    short_rate = short_count / short_weeks
    if long_count == 0:
        if short_count == 0:
            return None
        return 999.0  # sentinel for "spike from zero"
    long_rate = long_count / long_weeks
    return round(short_rate / long_rate, 4)


def compute_acceleration(
    velocity_short: float | None,
    velocity_long: float | None,
) -> float | None:
    """
    Acceleration = change in velocity between adjacent velocity windows.

    velocity_short = velocity_1w_vs_1mo
    velocity_long  = velocity_1mo_vs_3mo

    Positive = accelerating (velocity is increasing).
    Negative = decelerating.
    None = either velocity window is unavailable.
    """
    if velocity_short is None or velocity_long is None:
        return None
    return round(velocity_short - velocity_long, 4)


# ─────────────────────────────────────────────────────────────────────────────
# days_in_dataset
# ─────────────────────────────────────────────────────────────────────────────
#
# Canonical definition:
#   days_in_dataset = (CURRENT_DATE - tickers.first_seen_at::date)
#
# This is computed in score_compute.py as:
#   (stat_date - ticker.first_seen_at.date()).days
#
# Do NOT compute as COUNT(DISTINCT snapshot_date) — data gaps in Apewisdom
# would undercount the actual time the ticker has been in the system.

# ─────────────────────────────────────────────────────────────────────────────
# Per-ticker error handling contract
# ─────────────────────────────────────────────────────────────────────────────
#
# On yfinance failure for a ticker:
#   1. Use cached tickers.market_cap (last known value)
#   2. Set tickers.cap_verified = False for that ticker
#   3. Append f"{symbol}: yfinance_failed" to the stage error list
#   4. CONTINUE pipeline for this ticker using the cached market cap
#   5. The ticker is not skipped — it still gets scored and classified
#
# On Apewisdom API failure (all pages):
#   1. Set pipeline_runs.apewisdom_stale = True
#   2. Use the most recent apewisdom_snapshots rows for all tickers (previous day's data)
#   3. Set ticker_daily_stats.apewisdom_snapshot_date = yesterday's date (not today)
#   4. CONTINUE pipeline — do not abort
#   5. Alert after APEWISDOM_STALE_ALERT_THRESHOLD consecutive stale days
#
# On stage crash (unhandled exception):
#   1. Catch at stage boundary in the orchestrator
#   2. Log full traceback to pipeline_runs.errors
#   3. Set pipeline_runs.status = 'partial' if any prior stage succeeded
#   4. Set pipeline_runs.status = 'failed' if Stage 1 itself failed
#   5. Exit with non-zero status code → GitHub Actions sends email

APEWISDOM_STALE_ALERT_THRESHOLD: int = 3  # consecutive stale days before alerting

# ─────────────────────────────────────────────────────────────────────────────
# Pipeline timing targets
# ─────────────────────────────────────────────────────────────────────────────
#
# Total target: <60 minutes to stay within GitHub Actions free tier budget.
# (2,000 min/month limit; 60 min/day = 1,800 min/month leaves 200 min headroom)
#
# Stage-level targets:
#   Stage 1 (Apewisdom):  ~5 min  (200 pages × 1s delay = 3.3 min + overhead)
#   Stage 2 (Reddit):     ~10 min (optional; PRAW calls with rate limiting)
#   Stage 3 (Tickers):    ~20 min (yfinance batching — see below)
#   Stage 4 (Scoring):    ~15 min (single pandas DataFrame load, in-memory compute)
#   Stage 5 (Classify):   ~5 min  (pure Python, no I/O beyond final upserts)
#   Stage 6 (Log):        ~1 min
#
# Stage 3 batching strategy:
#   Fetch yfinance in batches of 10 tickers per call (yfinance supports batch download).
#   200 batches × 0.5s delay = 1.7 minutes total (NOT 2000 × 0.5s = 16.7 minutes).
#   Use yfinance.download(tickers=batch_list, period='1d') for market cap batch fetch.

YFINANCE_BATCH_SIZE: int = 10       # tickers per yfinance batch call
YFINANCE_BATCH_DELAY_SEC: float = 0.5  # seconds between batches
APEWISDOM_PAGE_DELAY_SEC: float = 1.0  # seconds between Apewisdom page requests

# ─────────────────────────────────────────────────────────────────────────────
# Monitored subreddits
# ─────────────────────────────────────────────────────────────────────────────
# Editable here without code changes. Used by reddit_ingest.py (if PRAW is enabled).

MONITORED_SUBREDDITS: list[str] = [
    "wallstreetbets",
    "stocks",
    "investing",
    "StockMarket",
    "options",
    "pennystocks",       # monitored but pump-subreddit-filtered in classifier
    "RobinHoodPennyStocks",  # monitored but pump-subreddit-filtered
    "smallstreetbets",
    "ValueInvesting",
    "SecurityAnalysis",
    "space",
    "biotech",
    "electricvehicles",
    "Semiconductors",
    "energy",
    "MachineLearning",
    "singularity",
    "Superstonk",
    "Commodities",
    "CanadianInvestor",
]
