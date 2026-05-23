# Business Case: Multi-Tranche Reddit Pre-Breakout Sentiment Monitor

**Generated:** 2026-05-23 00:35
**Prepared for:** Founder (self-evaluation)
**Recommendation:** CONDITIONAL GO

## Executive Summary

Retail investors consistently miss the best entry points on 5–100× stock moves because
they discover the thesis after Reddit has already made it obvious. The signal was present
years earlier — in niche subreddits, in low-volume threads, in growing organic conversation
that no one was tracking systematically. This project builds a multi-tranche Reddit
sentiment monitor that classifies stocks across three detection horizons: Seed (2–3 years
before breakout), Early (1–2 years), and Pre-pop (weeks to months). Each tranche surfaces
different signal patterns and serves different holding strategies. The tool is built
initially as a personal trading instrument, with a freemium SaaS layer added once the
backtest validates the signal across all three tranches. Total Year 1 cost is under $7K.
The tool pays for itself on a single correct early-stage call.

## Problem Statement

Active Reddit communities (r/wallstreetbets, r/stocks, r/investing, and dozens of sector
subs) accumulate genuine conviction about a company long before the price reacts. Palantir
(PLTR) was discussed in detail on r/investing and r/stocks years before its 2023 run.
Rocket Lab (RKLB) was a frequent topic on r/space and r/investing long before retail
discovered it in 2024. The signal existed at multiple time horizons — seed-level chatter
2+ years out, growing community awareness 1–2 years out, and a clear velocity spike in
the months before breakout.

No tool captures this multi-year arc. Existing trackers (Swaggy Stocks, Apewisdom) show
mention volume over the last 24–72 hours. They are designed to catch what is already
trending — a lagging indicator by design. There is no product that tracks the slow build
of organic conviction from first mention to community obsession to price breakout.

The cost today: an investor who found RKLB in 2022 instead of 2024 captured 20–30× instead
of 5×. The difference between tranches is not just timing — it is order-of-magnitude
difference in return potential.

The cost today: missing one pre-breakout setup per quarter on a $5K–$10K position
represents a $25K–$100K opportunity cost annually at 5–10× return multiples.

## Proposed Solution

A Reddit data pipeline that classifies every tracked ticker across three detection
tranches, each with distinct signal characteristics and use cases:

| Tranche | Horizon | Signal character | Use case |
|---------|---------|-----------------|----------|
| **Tier 1 — Seed** | 2–3 years before breakout | 5–30 mentions/week, niche subs, no price reaction | Maximum upside, long hold |
| **Tier 2 — Early** | 1–2 years before breakout | Growing mentions, spreading to larger subs, thesis forming | Strong risk/reward, position building |
| **Tier 3 — Pre-pop** | Weeks to months | Velocity spike, crossing into mainstream subs, sentiment intensifying | Momentum entry, shorter hold |

The pipeline:
1. Monitors 15–25 subreddits continuously (broad market + sector-specific)
2. Extracts and normalises ticker mentions across post titles, bodies, and comments
3. Computes a **multi-horizon velocity score** — rolling mention rate over 1 week,
   1 month, 3 months, 6 months, 1 year, 2 years — and classifies each ticker into
   the appropriate tranche based on its trajectory shape
4. Filters for early-stage characteristics: market cap < $5B, limited mainstream
   analyst coverage, no major ETF inclusion yet
5. Surfaces a daily digest with tickers newly entering or advancing between tranches
6. Shows full historical mention trajectory so users can see the multi-year build-up
7. Backtests the model against known breakouts (PLTR, RKLB, and others) across all
   three tranches to validate signal reliability per horizon

**In scope for v1:** Data pipeline, ticker extraction, multi-horizon velocity scoring,
tranche classification, dashboard with historical view, email/Discord digest.
**Out of scope for v1:** Mobile app, social features, portfolio integration, B2B API,
real-time streaming (daily batch is sufficient for 1–3 year horizons).

## Investment Required

| Item | Cost |
|------|------|
| Build — engineering time (self-built) | $4,000 (opportunity cost est.) |
| Build — paid APIs / tooling / setup | $1,000 |
| Run — Reddit API | ~$50/mo |
| Run — Hosting (cloud, DB) | ~$50/mo |
| Run — LLM calls (ticker extraction, sentiment) | ~$50/mo |
| **Total one-time build** | **$5,000** |
| **Total monthly run** | **$150/mo** |
| **Total Year 1 (build + 12 months run)** | **$6,800** |

## Expected Return

### Scenario A — Personal Trading Alpha (Primary)

| Metric | Baseline | With Tool | Δ |
|--------|----------|-----------|---|
| Pre-breakout setups identified/yr | 0–1 (manual) | 4–8 (systematic) | +4–7 setups |
| Win rate on early entries | ~40% | ~45–55% (better timing) | +5–15% |
| Avg position size | $5,000 | $5,000 | — |
| Avg return on correct call (5–10×) | — | $20,000–$45,000 | — |
| Expected annual trading alpha | ~$0 | $40,000–$150,000 | **+$40K–$150K** |

*Conservative case: catch 2 pre-breakout setups per year, 50% win rate, 5× average
return on $5K position = $25K gain. Tool cost: $6,800. Net Year 1: +$18,200.*

**Payback period (trading alpha): 1 correct trade.**

### Scenario B — SaaS Revenue (Secondary, Month 6+)

Freemium model: free tier (top 10 tickers, 24h delay) / paid tier ($30/mo, real-time
velocity alerts, full history, custom alerts).

| Month | Paid Users | MRR |
|-------|-----------|-----|
| 3 | 0 | $0 (building + backtest phase) |
| 6 | 50 | $1,500 |
| 9 | 150 | $4,500 |
| 12 | 300 | $9,000 |

**Break-even on SaaS (covering run costs):** ~10 paid users at $30/mo = $300/mo.
Achievable within 3 months of launch.

**12-month net SaaS return** (revenue minus run costs, post-launch month 3):
$0 + $0 + $1,500 + $4,500 + $9,000 = ~$15,000 gross MRR earned in months 6–12.
Minus $150/mo run cost × 12 = $1,800. **Net: ~$13,200.**

**Confidence-adjusted** (50% confidence on SaaS numbers — depends on backtest signal
quality and word-of-mouth): $13,200 × 0.50 = **$6,600 SaaS net Year 1.**

### Combined Year 1 Return (Conservative)

| Source | Return |
|--------|--------|
| Trading alpha (conservative, 2 setups, 50% win rate) | $18,200 net |
| SaaS revenue (confidence-adjusted) | $6,600 net |
| **Total Year 1 net (conservative)** | **$24,800** |
| **Total Year 1 cost** | **$6,800** |
| **ROI** | **365%** |

**Payback period: 1–2 months** (first correct pre-breakout trade covers the build cost).

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| Backtest shows no signal — Reddit velocity didn't actually precede PLTR/RKLB breakouts | High | Backtest before building the full product. If signal isn't there in historical data, the core thesis fails. Do this first, before spending $5K. |
| Reddit API access becomes too expensive or restricted | Medium | Design pipeline to work with rate-limited free tier first; evaluate paid tier only after validating signal. Keep scraping as backup. |
| Pump-and-dump noise drowns out real signal | Medium | Build quality filters: account age, post karma, subreddit trust score. Filter penny stocks and OTC explicitly. |
| No distribution — free users don't convert to paid | Medium | Launch with a public "we called it" leaderboard. Post backtest results on Reddit itself. Let the product market itself in the communities it monitors. |
| Founder builds alone, gets stuck on data pipeline | Low | The data pipeline is the hardest part. Scope v1 to 3–5 subreddits only. Don't boil the ocean — prove the signal with a narrow dataset first. |

## Alternatives Considered

- **Buy existing data from Quiver Quantitative or SocialBlade.** Faster to start but
  $50–200/mo without the velocity/acceleration scoring that is the core differentiation.
  You'd be paying for commodity data, not the edge.
- **Build on top of existing free tools (Apewisdom API).** Data is limited, update
  frequency is too slow for early-stage detection, and you'd have no control over
  the scoring model.
- **Skip personal use, go straight to B2B.** Enterprise sales cycle is 3–6 months.
  Wrong first step when the signal hasn't been validated. Personal use first is the
  right sequencing.

## Recommendation

**CONDITIONAL GO.**

The personal trading case alone justifies the $5K build cost — one correct pre-breakout
trade returns multiples of the investment. The SaaS layer is upside, not the primary
bet. The condition: **run the backtest before writing code.** Pull historical Reddit
data for 2022–2025, measure whether PLTR, RKLB, and 3–5 other known breakout stocks
showed measurable velocity acceleration 4–8 weeks before their price moves. If the
signal is real, proceed immediately to PRD. If not, the thesis needs revision before
building.

The single number that most changes this outcome: **the backtest hit rate.** If 4 out
of 5 known breakouts showed a Reddit velocity signal 4+ weeks early, this product has
a story that markets itself. If only 1 out of 5 did, the signal isn't reliable enough
to build on.

## Latest file

This document supersedes: *(none — first business case)*
