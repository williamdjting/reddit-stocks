-- Reddit Pre-Breakout Sentiment Monitor
-- PostgreSQL schema for Supabase
-- Generated: 2026-05-23

-- ─────────────────────────────────────────
-- Enums
-- ─────────────────────────────────────────

CREATE TYPE tranche_enum AS ENUM (
  'seed',               -- Tier 1: 12+ months, 5–50/wk, market cap < $5B
  'early',              -- Tier 2: 6+ months, 50–300/wk, cap < $10B
  'pre_pop',            -- Tier 3: >300/wk or >50% WoW growth
  'noise',              -- High volume spike, no sustained build
  'insufficient_data',  -- <90 days in dataset
  'unclassified'        -- 90+ days, no rule matched
);

CREATE TYPE run_status_enum AS ENUM (
  'success',
  'partial',
  'failed'
);

-- ─────────────────────────────────────────
-- tickers — master registry
-- ─────────────────────────────────────────

CREATE TABLE tickers (
  symbol            text            PRIMARY KEY,
  name              text            NOT NULL,
  aliases           text[]          NOT NULL DEFAULT '{}',
  market_cap        bigint,
  sector            text,
  current_tranche   tranche_enum    NOT NULL DEFAULT 'insufficient_data',
  cap_verified      boolean         NOT NULL DEFAULT false,
  cap_last_updated  timestamptz,
  is_active         boolean         NOT NULL DEFAULT true,
  first_seen_at     timestamptz     NOT NULL DEFAULT now(),
  created_at        timestamptz     NOT NULL DEFAULT now(),
  updated_at        timestamptz     NOT NULL DEFAULT now()
);

CREATE INDEX idx_tickers_tranche   ON tickers (current_tranche);
CREATE INDEX idx_tickers_active    ON tickers (is_active) WHERE is_active = true;

-- ─────────────────────────────────────────
-- apewisdom_snapshots — raw daily counts
-- ─────────────────────────────────────────

CREATE TABLE apewisdom_snapshots (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker           text        NOT NULL,
  snapshot_date    date        NOT NULL,
  mention_count_24h integer    NOT NULL,
  mention_count_7d  integer,
  rank             integer,
  upvotes          integer,
  created_at       timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT uq_apewisdom_ticker_date UNIQUE (ticker, snapshot_date)
);

CREATE INDEX idx_apewisdom_date   ON apewisdom_snapshots (snapshot_date DESC);
CREATE INDEX idx_apewisdom_ticker ON apewisdom_snapshots (ticker, snapshot_date DESC);

-- ─────────────────────────────────────────
-- raw_mentions — optional Reddit context
-- (entire table is optional — dropped if Reddit ToS prohibits)
-- ─────────────────────────────────────────

CREATE TABLE raw_mentions (
  id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker                  text        NOT NULL REFERENCES tickers (symbol) ON DELETE RESTRICT,
  post_id                 text        NOT NULL,
  subreddit               text        NOT NULL,
  post_title              text        NOT NULL,
  content_snippet         text,
  author_account_age_days integer,
  mention_date            date        NOT NULL,
  source                  text        NOT NULL DEFAULT 'reddit_api',
  created_at              timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT uq_raw_mention_ticker_post UNIQUE (ticker, post_id)
);

CREATE INDEX idx_raw_mentions_ticker_date ON raw_mentions (ticker, mention_date DESC);
CREATE INDEX idx_raw_mentions_date        ON raw_mentions (mention_date DESC);

-- ─────────────────────────────────────────
-- ticker_daily_stats — computed scores
-- ─────────────────────────────────────────

CREATE TABLE ticker_daily_stats (
  id                  uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker              text          NOT NULL REFERENCES tickers (symbol) ON DELETE RESTRICT,
  stat_date           date          NOT NULL,
  days_in_dataset     integer       NOT NULL,
  -- Date of the apewisdom_snapshots actually used for scoring.
  -- Equals stat_date when data is fresh; equals the previous available date when stale.
  apewisdom_snapshot_date date      NOT NULL,

  -- Rolling mention counts (NULL = insufficient data, not zero)
  mention_count_1w    integer,
  mention_count_1mo   integer,
  mention_count_3mo   integer,
  mention_count_6mo   integer,
  mention_count_1y    integer,
  mention_count_18mo  integer,
  mention_count_2y    integer,

  -- Velocity: normalised weekly rate ratio between adjacent windows
  -- >1.0 = accelerating, <1.0 = decelerating, NULL = window unavailable
  velocity_1w_vs_1mo    numeric(8,4),
  velocity_1mo_vs_3mo   numeric(8,4),
  velocity_3mo_vs_6mo   numeric(8,4),
  velocity_6mo_vs_1y    numeric(8,4),

  -- Acceleration: change in velocity (velocity_1w_vs_1mo - velocity_1mo_vs_3mo)
  acceleration          numeric(8,4),

  -- Subreddit diversity (from raw_mentions if available, else NULL)
  subreddit_spread      integer,

  -- Classification output
  tranche             tranche_enum  NOT NULL,

  created_at          timestamptz   NOT NULL DEFAULT now(),
  updated_at          timestamptz   NOT NULL DEFAULT now(),

  CONSTRAINT uq_daily_stats_ticker_date UNIQUE (ticker, stat_date)
);

CREATE INDEX idx_daily_stats_date_tranche
  ON ticker_daily_stats (stat_date DESC, tranche);

CREATE INDEX idx_daily_stats_tranche_velocity
  ON ticker_daily_stats (tranche, velocity_1w_vs_1mo DESC NULLS LAST);

CREATE INDEX idx_daily_stats_ticker_date
  ON ticker_daily_stats (ticker, stat_date DESC);

-- ─────────────────────────────────────────
-- ticker_tranche_log — transition history (ML training set)
-- ─────────────────────────────────────────

CREATE TABLE ticker_tranche_log (
  id                    uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker                text          NOT NULL REFERENCES tickers (symbol) ON DELETE RESTRICT,
  tranche               tranche_enum  NOT NULL,
  previous_tranche      tranche_enum,
  entered_at            date          NOT NULL,
  exited_at             date,                    -- NULL = currently in this tranche
  velocity_at_entry     numeric(8,4),
  mention_count_at_entry integer,
  market_cap_at_entry   bigint,
  created_at            timestamptz   NOT NULL DEFAULT now(),

  -- Prevents duplicate log entries when the pipeline is re-run for the same date.
  -- ON CONFLICT (ticker, entered_at) DO UPDATE allows idempotent upserts.
  CONSTRAINT uq_tranche_log_ticker_entered UNIQUE (ticker, entered_at)
);

CREATE INDEX idx_tranche_log_ticker      ON ticker_tranche_log (ticker, entered_at DESC);
CREATE INDEX idx_tranche_log_tranche     ON ticker_tranche_log (tranche, entered_at DESC);
CREATE INDEX idx_tranche_log_open        ON ticker_tranche_log (exited_at) WHERE exited_at IS NULL;

-- ─────────────────────────────────────────
-- pipeline_runs — reliability log
-- ─────────────────────────────────────────

CREATE TABLE pipeline_runs (
  id                  uuid              PRIMARY KEY DEFAULT gen_random_uuid(),
  run_date            date              NOT NULL UNIQUE,
  started_at          timestamptz       NOT NULL,
  completed_at        timestamptz,
  status              run_status_enum   NOT NULL,
  tickers_processed   integer,
  apewisdom_records   integer,
  reddit_records      integer,
  scores_computed     integer,
  tranches_updated    integer,
  apewisdom_stale     boolean           NOT NULL DEFAULT false,
  errors              text[]            NOT NULL DEFAULT '{}',
  duration_ms         integer,
  created_at          timestamptz       NOT NULL DEFAULT now()
);
