# Scenarios: Multi-Tranche Reddit Pre-Breakout Sentiment Monitor

**Generated:** 2026-05-23 02:30
**Source PRD:** PRD-2026-05-23.md
**Status:** Draft

---

## Summary

Total scenarios: 35
P0: 12 | Automate (unit): 10 | Automate (integration): 16 | E2E: 5 | Manual: 4

---

## Scenarios

---

### Feature 1: Daily Digest View
*So that the trader can evaluate early-stage opportunities before the broader market notices.*

```gherkin
Feature: Daily Digest View
  So that the trader can evaluate early-stage opportunities before the broader market notices

  Background:
    Given the pipeline has completed successfully for today's date
    And the Supabase database contains ticker_daily_stats records for today

  # Automation: e2e
  # Priority: P0
  Scenario: Digest shows tickers that crossed a tranche threshold in the last 24 hours
    Given "RKLB" entered the "pre_pop" tranche at 06:15 UTC today
    And "ACHR" had a velocity_1w_vs_1mo score increase from 1.2 to 2.8 today
    When I open the Daily Digest page in the dashboard
    Then I see "RKLB" listed under the "Pre-pop" group
    And I see "ACHR" listed under the "Pre-pop" group
    And each ticker row shows: symbol, current tranche, velocity score, and top subreddit

  # Automation: e2e
  # Priority: P0
  Scenario: Clicking a ticker in the digest navigates to its full mention trajectory
    Given the Daily Digest page shows "ACHR" in the Pre-pop group
    When I click on "ACHR"
    Then I am taken to the Ticker Detail View for "ACHR"
    And the mention volume chart covers all available time windows from first detection to today

  # Automation: integration
  Scenario: Digest shows "no new signals today" when no tranche thresholds were crossed
    Given no ticker changed tranche and no ticker had velocity_1w_vs_1mo increase > 50% today
    When I open the Daily Digest page
    Then I see the message "No new signals today — check back tomorrow"
    And the page load completes in under 3 seconds

  # Automation: integration
  Scenario: Digest groups results correctly by tranche
    Given "RKLB" is in "pre_pop" tranche with a new entry today
    And "LUNR" is in "early" tranche with a velocity increase today
    When I view the Daily Digest page
    Then "RKLB" appears under the "Pre-pop" section
    And "LUNR" appears under the "Early" section
    And the "Seed" section is either populated or absent — never shows "Early" or "Pre-pop" entries
```

---

### Feature 2: Tranche Overview
*So that the trader knows which tickers are long-term builds, medium-term, or near-term setups.*

```gherkin
Feature: Tranche Overview
  So that the trader knows which tickers are long-term builds, medium-term, or near-term setups

  Background:
    Given the dashboard is open on the Tranche Overview page

  # Automation: e2e
  # Priority: P0
  Scenario: Three-column view shows all active tickers sorted by velocity score descending
    Given the database contains 12 tickers in "pre_pop", 5 in "early", and 0 in "seed"
    When I open the Tranche Overview page
    Then I see three columns: "Seed", "Early", "Pre-pop"
    And the "Pre-pop" column lists all 12 tickers sorted by velocity_1w_vs_1mo descending
    And the "Early" column lists all 5 tickers sorted by velocity_1w_vs_1mo descending

  # Automation: e2e
  # Priority: P0
  Scenario: Immature tranche shows "maturing" placeholder before activation date
    Given the dataset was first collected on 2026-05-23
    And today is 2026-07-01 (39 days since collection started)
    When I open the Tranche Overview page
    Then the "Seed" column shows "Maturing — activates approx. May 2027"
    And the "Early" column shows "Maturing — activates approx. Nov 2026"
    And the "Pre-pop" column shows active tickers normally

  # Automation: integration
  Scenario: Market cap filter limits visible tickers to the selected range
    Given the "Pre-pop" column contains "RKLB" (market cap $8B) and "ACHR" (market cap $600M)
    When I set the market cap filter to "Under $1B"
    Then only "ACHR" appears in the "Pre-pop" column
    And "RKLB" is hidden

  # Automation: e2e
  Scenario: Tranche column shows days-in-tranche alongside each ticker
    Given "RKLB" entered "pre_pop" on 2026-05-01 and today is 2026-05-23
    When I view the "Pre-pop" column
    Then "RKLB" shows "22 days in tranche" next to its velocity score
```

---

### Feature 3: Ticker Detail View
*So that the trader can judge the quality and consistency of a signal before committing capital.*

```gherkin
Feature: Ticker Detail View
  So that the trader can judge the quality and consistency of a signal before committing capital

  Background:
    Given "RKLB" has been tracked for 210 days with apewisdom_snapshots for all 210 days

  # Automation: e2e
  # Priority: P0
  Scenario: Detail view shows all six required data elements for a mature ticker
    When I open the Ticker Detail View for "RKLB"
    Then I see a mention volume chart with data for 1w, 1mo, 3mo, 6mo windows
    And I see a subreddit breakdown showing mention counts per subreddit
    And I see up to 5 post excerpts each showing title, subreddit name, and date
    And I see the current tranche label and the number of days in that tranche
    And I see a velocity score and an acceleration score
    And I see the first detection date

  # Automation: integration
  # Priority: P0
  Scenario: Time windows with insufficient data are labelled — not shown as zero
    Given "ACHR" has been tracked for 95 days
    When I open the Ticker Detail View for "ACHR"
    Then the 6-month mention window shows "Not enough data yet (95 / 180 days)"
    And the 1-year mention window shows "Not enough data yet (95 / 365 days)"
    And the 1-week and 1-month windows show their actual mention counts

  # Automation: unit
  Scenario: Detail view loads in under 2 seconds
    Given "LUNR" has 365 days of apewisdom_snapshots (365 rows)
    When I request the detail view for "LUNR"
    Then the page renders completely within 2 seconds

  # Automation: integration
  Scenario: Detail view shows "context unavailable" when raw_mentions is empty for that ticker
    Given Reddit ingester is disabled and raw_mentions has no rows for "RKLB"
    When I open the Ticker Detail View for "RKLB"
    Then the post excerpts section shows "No Reddit post context available"
    And all scoring data (velocity, tranche, chart) is still shown normally
```

---

### Feature 4: Daily Pipeline Digest Notification
*So that the trader never misses a ticker accelerating toward a breakout.*

```gherkin
Feature: Daily Pipeline Digest Notification
  So that the trader never misses a ticker accelerating toward a breakout

  Background:
    Given the GitHub Actions daily pipeline runs at 06:00 UTC

  # Automation: integration
  # Priority: P0
  Scenario: Digest is available in the dashboard by 07:00 UTC on the following morning
    Given the pipeline started at 06:00 UTC and completed successfully at 06:47 UTC
    When I open the Daily Digest page at 07:00 UTC
    Then the digest reflects tranche data as of today's completed run
    And the "Last updated" timestamp on the digest shows today's date

  # Automation: integration
  Scenario: Digest entry for each ticker shows required fields
    Given "ACHR" crossed from "unclassified" to "pre_pop" today
    When I view the Daily Digest entry for "ACHR"
    Then the entry shows: symbol "ACHR", current tranche "Pre-pop", velocity score, and top subreddit driving mentions

  # Automation: integration
  Scenario: No digest entry is generated for tickers with no tranche change and no velocity spike
    Given "SPY" has been in "noise" tranche for 30 days with stable velocity_1w_vs_1mo of 0.9
    When the pipeline completes today
    Then "SPY" does not appear in the Daily Digest entries

  # Automation: manual
  Scenario: GitHub Actions sends an email notification when the pipeline job fails
    Given the pipeline job exits with a non-zero status code
    When GitHub Actions detects the failure
    Then an email is sent to the configured GitHub notification address
    And the email subject contains the workflow name and "failed"
```

---

### Feature 5: Ticker Search
*So that the trader can validate whether Reddit sentiment supports or contradicts their thesis.*

```gherkin
Feature: Ticker Search
  So that the trader can validate whether Reddit sentiment supports or contradicts their thesis

  # Automation: e2e
  # Priority: P0
  Scenario: Searching a known ticker returns its full history
    Given "RKLB" has been tracked for 210 days with complete velocity and tranche data
    When I type "RKLB" in the search bar and press enter
    Then I see the Ticker Detail View for "RKLB"
    And the view includes: mention history chart, current tranche "pre_pop", velocity score, first detection date

  # Automation: integration
  # Priority: P0
  Scenario: Searching a ticker the system has never seen returns a clear no-data message
    Given "MSTR" has no rows in the tickers table or apewisdom_snapshots
    When I type "MSTR" in the search bar and press enter
    Then I see the message: "No data yet for MSTR — will appear once first mentions are detected"
    And no error or empty chart is shown

  # Automation: integration
  Scenario: Search is case-insensitive
    Given "RKLB" exists in the tickers table
    When I type "rklb" in the search bar (lowercase)
    Then I see the same result as searching "RKLB"

  # Automation: integration
  Scenario: Searching a ticker in "noise" or "unclassified" tranche still returns its history
    Given "WISH" is in the "noise" tranche and is not shown on the Tranche Overview
    When I type "WISH" in the search bar
    Then I see the Ticker Detail View for "WISH" with its full mention history
    And the tranche label shows "Noise"
```

---

### Feature 6: Data Immaturity Warning
*So that the trader does not mistake a new ticker for a genuinely early-signal one.*

```gherkin
Feature: Data Immaturity Warning
  So that the trader does not mistake a new ticker for a genuinely early-signal one

  # Automation: integration
  # Priority: P0
  Scenario: Ticker with fewer than 90 days of data is labelled "Insufficient history"
    Given "NVTS" first appeared in the dataset 45 days ago
    When "NVTS" appears in any dashboard view
    Then it is labelled "Insufficient history (45 / 90 days)"
    And it is not assigned to Tier 1 "seed" or Tier 2 "early" tranche

  # Automation: unit
  # Priority: P0
  Scenario: Ticker with exactly 90 days of data is eligible for tranche classification
    Given "ACHR" has days_in_dataset = 90 in ticker_daily_stats for today
    When the tranche classifier runs
    Then "ACHR" is evaluated against tranche rules (it may receive "unclassified" but not "insufficient_data")

  # Automation: unit
  Scenario: Ticker with 89 days of data is still classified as "insufficient_data"
    Given "JOBY" has days_in_dataset = 89
    When the tranche classifier runs
    Then "JOBY" receives tranche = "insufficient_data"
    And "JOBY" does not appear in the Tranche Overview columns

  # Automation: integration
  Scenario: Recently-IPO'd ticker is excluded from Tier 1 and Tier 2 even if velocity is high
    Given "NEWCO" has days_in_dataset = 30 and velocity_1w_vs_1mo = 5.0
    When the tranche classifier runs
    Then "NEWCO" receives tranche = "insufficient_data" regardless of velocity
    And "NEWCO" is not listed in any tranche column on the overview
```

---

### Feature 7: Apewisdom Daily Ingest
*So that daily mention counts are available for all scoring and classification.*

```gherkin
Feature: Apewisdom Daily Ingest
  So that daily mention counts are available for all scoring and classification

  # Automation: integration
  # Priority: P0
  Scenario: Successful ingest stores one apewisdom_snapshot row per ticker per date
    Given the Apewisdom API returns data for 1,200 tickers across 12 pages
    When the apewisdom ingest stage runs for 2026-05-23
    Then 1,200 rows exist in apewisdom_snapshots with snapshot_date = 2026-05-23
    And each row has a non-null mention_count_24h value

  # Automation: integration
  # Priority: P0
  Scenario: Re-running ingest for the same date does not create duplicate rows
    Given apewisdom_snapshots already has 1,200 rows for 2026-05-23
    When the apewisdom ingest stage runs again for 2026-05-23
    Then apewisdom_snapshots still has exactly 1,200 rows for 2026-05-23
    And no row has a conflicting or duplicate entry for the same ticker + date

  # Automation: integration
  # Priority: P0
  Scenario: Ingest failure flags the run as stale without corrupting existing data
    Given the Apewisdom API returns HTTP 503 on all requests
    When the apewisdom ingest stage runs
    Then the pipeline_runs record for today shows apewisdom_stale = true
    And apewisdom_snapshots for yesterday's date is unchanged
    And the pipeline continues to the scoring stage using yesterday's snapshot data

  # Automation: unit
  Scenario: New ticker found in Apewisdom that is not in the tickers table is auto-registered
    Given "LUNR" does not exist in the tickers table
    And the Apewisdom API returns "LUNR" with mention_count_24h = 45
    When the ticker sync stage runs
    Then a new row for "LUNR" is inserted into tickers with first_seen_at = today
    And the apewisdom_snapshot for "LUNR" is stored normally
```

---

### Feature 8: Tranche Classification
*So that tickers are correctly assigned to detection tiers based on the phase-gated rules.*

```gherkin
Feature: Tranche Classification
  So that tickers are correctly assigned to detection tiers based on the phase-gated rules

  Background:
    Given the scoring engine has completed and ticker_daily_stats is populated for today

  # Automation: unit
  # Priority: P0
  Scenario: Tier 3 Pre-pop is correctly assigned when weekly volume exceeds 300
    Given "ACHR" has mention_count_1w = 350, subreddit_spread = 4, and market_cap = 900000000 ($900M)
    And days_in_dataset = 120
    When the tranche classifier runs
    Then "ACHR" receives tranche = "pre_pop"

  # Automation: unit
  # Priority: P0
  Scenario: Tier 1 Seed is blocked before month 12 regardless of velocity
    Given today is 200 days since first data collection started
    And "RKLB" has mention_count_1w = 25, velocity_1w_vs_1mo = 2.5, market_cap = 3000000000 ($3B)
    When the tranche classifier runs
    Then "RKLB" is NOT assigned "seed" tranche
    And "RKLB" receives either "pre_pop", "early", "unclassified", or "noise" based on its other metrics

  # Automation: unit
  Scenario: Noise is assigned when volume spike appears without sustained build
    Given "GME" has mention_count_1w = 800 but velocity_1mo_vs_3mo = 0.3 (decelerating)
    And the prior 4 weeks all had mention_count < 50
    When the tranche classifier runs
    Then "GME" receives tranche = "noise"

  # Automation: integration
  Scenario: Tranche transition is recorded in ticker_tranche_log only when tranche changes
    Given "ACHR" was in "unclassified" yesterday and moves to "pre_pop" today
    When the tranche classifier runs
    Then a new row is appended to ticker_tranche_log with previous_tranche = "unclassified" and tranche = "pre_pop"
    And tickers.current_tranche for "ACHR" is updated to "pre_pop"

  # Automation: unit
  Scenario: Ticker with market cap above tier cap gate is excluded from that tier
    Given "META" has mention_count_1w = 500, subreddit_spread = 8, but market_cap = 1400000000000 ($1.4T)
    When the tranche classifier runs
    Then "META" does NOT receive "pre_pop" tranche (market cap exceeds $20B gate)
    And "META" receives "noise" or "unclassified"
```

---

### Feature 9: Pipeline Idempotency
*So that a failed or repeated pipeline run never corrupts existing data.*

```gherkin
Feature: Pipeline Idempotency
  So that a failed or repeated pipeline run never corrupts existing data

  # Automation: integration
  # Priority: P0
  Scenario: Re-running the full pipeline for a given date produces identical results
    Given the pipeline ran successfully on 2026-05-22 and all tables are populated
    When the pipeline is run again for 2026-05-22 via workflow_dispatch
    Then ticker_daily_stats has the same row count for 2026-05-22 as before
    And all velocity and tranche values are identical to the first run
    And pipeline_runs shows exactly one row for run_date = 2026-05-22 (upserted, not duplicated)

  # Automation: integration
  # Priority: P0
  Scenario: A mid-pipeline crash leaves previously committed stages intact
    Given the pipeline completed Stage 1 (apewisdom_ingest) and Stage 2 (ticker_sync)
    And Stage 3 (score_compute) crashes with an uncaught exception
    When the pipeline exits with failure status
    Then apewisdom_snapshots rows for today remain intact
    And tickers rows remain intact
    And ticker_daily_stats has no partial or corrupt rows for today
    And pipeline_runs shows status = "partial" with the error in the errors array

  # Automation: integration
  Scenario: Manual re-trigger after a failed run completes successfully without data gaps
    Given yesterday's pipeline failed after Stage 1 (scoring was not run)
    When I manually trigger the pipeline via workflow_dispatch for yesterday's date
    Then scoring and classification complete for yesterday's date
    And the data gap in ticker_daily_stats is filled
    And the final pipeline_runs record for yesterday shows status = "success"
```

---

### Feature 10: Quality Filter
*So that pump tickers, OTC listings, and low-quality signals are suppressed from tranche results.*

```gherkin
Feature: Quality Filter
  So that pump tickers, OTC listings, and low-quality signals are suppressed from tranche results

  # Automation: unit
  # Priority: P0
  Scenario: Ticker with market cap below $50M is excluded from all tranches
    Given "TINY" has market_cap = 30000000 ($30M) and mention_count_1w = 500
    When the tranche classifier and quality filter run
    Then "TINY" is not assigned to any active tranche
    And "TINY" is excluded from all Tranche Overview columns

  # Automation: unit
  Scenario: Ticker where >80% of mentions come from accounts under 30 days old is suppressed
    Given "SCAM" has 100 mentions today and 85 of them are from accounts with author_account_age_days < 30
    When the quality filter runs
    Then "SCAM" receives tranche = "noise"
    And "SCAM" does not appear in the Tranche Overview

  # Automation: unit
  Scenario: Ticker where all mentions originate from a blocked pump subreddit is suppressed
    Given the pump_subreddit_blocklist contains "r/RobinHoodPennyStocks"
    And "PUMP" has 200 mentions today, all from "r/RobinHoodPennyStocks"
    When the quality filter runs
    Then "PUMP" receives tranche = "noise"
    And "PUMP" does not appear in the Tranche Overview

  # Automation: manual
  Scenario: Quality filter thresholds are configurable without code changes
    Given the current account_age threshold is 30 days (defined in config.py)
    When I change the threshold to 60 days in config.py and re-run the pipeline
    Then tickers with 31–59 day old accounts are now also suppressed
    And no schema migration is required
```

---

## Latest file

This document supersedes: none (first version)
