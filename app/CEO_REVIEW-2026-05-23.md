# CEO Review: Multi-Tranche Reddit Pre-Breakout Sentiment Monitor

**Generated:** 2026-05-23 02:45
**Mode:** Hold Scope
**Verdict:** Proceed with modifications

---

## Summary

The core idea is sound and differentiated: track the slow build of Reddit conviction across
three time horizons before price reacts. No competitor owns this framing. The personal trading
case alone justifies the build cost. However, three specific problems need to be resolved
before implementation starts: (1) the business case's one condition for GO — validate the
historical signal — was bypassed in the PRD without a documented decision; (2) the distribution
strategy for the SaaS layer is entirely missing; (3) the v1 architecture is "no auth, single
user" but the business case assumes paying customers by month 3 — these two facts are
incompatible. Fix these three things; everything else is correctly scoped.

---

## Findings

### 1. Problem Definition — Precise

The problem is well-defined. "Reddit trackers show what's trending now — a lagging indicator —
and no tool captures the 1–3 year conviction build before a breakout." This is specific enough
to drive product decisions. PLTR in 2023, RKLB in 2024 as concrete examples gives the story
a spine.

No change needed here.

---

### 2. Who is the Customer — Specific Enough

Retail swing/position trader, 25–45, holds weeks to months, reads Reddit already, has felt
the pain of missing a 5–10× move. $30–40/month price sensitivity is appropriate for this
persona. This is one real person, not a demographic blob.

The one gap: the Opportunity Analysis scores **team/founder fit at 1/5** — "no technical
or trading edge identified yet." This is the honest answer, but it means the single biggest
risk to execution is not in the product design — it's whether the person building this can
actually build and maintain a daily data pipeline alone. The plan needs to acknowledge this
explicitly rather than treating it as background noise.

---

### 3. The 10-Star Product

The 10-star version of this is not "better alerts." It is a system that can say:
**"RKLB has been building conviction for 18 months. Here is what its trajectory looks like
compared to PLTR at the same stage. Based on 12 known breakouts, this pattern resolves to
a breakout within the next 4–8 months with 65% confidence."**

That requires 12+ months of accumulated data and validated pattern-matching. Today you can't
build that. But every design decision from day one should ask: "does this get us closer to
or further from that 10-star version?" Specifically:

- Storing `ticker_tranche_log` as an accumulating labeled dataset ✓ (correct direction)
- Forward-only data strategy ✓ (correct — no alternative exists)
- Making thresholds configurable from day one ✓ (correct — you'll need to tune them)

The 10-star product isn't version 1. But the architecture is already pointed at it.

---

### 4. What to Cut

The PRD's "Should Have" and "Could Have" sections are appropriately deprioritized. The current
Must Have list of 13 items is on the edge of too large for a solo builder. One specific cut:

**Cut: Daily digest email/webhook (Must Have #12) from v1.**

The PRD puts "daily digest notification" as Must Have. But for a personal tool used by one
person, the dashboard IS the digest. Opening the dashboard every morning is the same workflow
as reading an email digest — the only difference is who initiates it. Delivering a daily email
to yourself requires: email infrastructure (Resend/SendGrid), email template, unsubscribe
handling, and email formatting logic. That's 2–4 days of build time for a feature with zero
marginal benefit for a single-user v1.

The dashboard's "Daily Digest" page already fulfills the user story. The email version is
a SaaS-tier feature, not a personal-tool feature.

---

### 5. What is Being Avoided — CRITICAL FINDING

**The business case's one condition for GO has been bypassed.**

The BUSINESS_CASE-2026-05-23.md states explicitly:

> *"The condition: run the backtest before writing code. Pull historical Reddit data for
> 2022–2025, measure whether PLTR, RKLB, and 3–5 other known breakout stocks showed
> measurable velocity acceleration 4–8 weeks before their price moves."*

> *"The single number that most changes this outcome: the backtest hit rate."*

The PRD then moved to a "forward-only, no historical backtest required" strategy — citing
the unavailability of historical Reddit data (Pushshift defunct, Reddit API pricing).

This is a real constraint. But it was not documented as a decision. It was documented as a
strategy. These are different things.

The correct framing is: **the core signal thesis is unvalidated.** The forward-only approach
accepts this risk and treats forward-collection + watching outcomes as the validation method.
That is a defensible call — but it means you are building for 12+ months before you know
if Tier 1 and Tier 2 signals actually predict breakouts.

**This is not a reason to stop.** The Tier 3 signal (pre-pop velocity) is validatable within
weeks — you can watch tickers the system surfaces in real time. The Tier 2 and Tier 1 signals
require patient capital: you will not know if they work for 12–24 months.

The required change is: **document this as an explicit risk acceptance**, not a strategy
choice. The founder needs to know they are building on an unvalidated thesis for the Tier 1
and Tier 2 tranches specifically.

---

### 6. Competition — Gap is Real

The competitive analysis is correct. No product exists at the intersection of:
- Pre-breakout framing (not trending-now)
- Multi-horizon velocity scoring (not just 24h mention count)
- Market cap filter for early-stage names (not large-cap sentiment)

The gap is real and unoccupied. The risk is not a competitor already doing this — the risk
is that the signal isn't real, and no competitor is doing this because the signal isn't real.
See finding #5.

---

### 7. Distribution — MISSING

The PRD is entirely silent on distribution. The Business Case mentions "launch with a public
'we called it' leaderboard" as a viral acquisition channel. This is the right idea — but it
has not been designed into the product.

For the SaaS layer to reach 250 paying customers by month 12, the distribution mechanism
needs to be built alongside the product, not bolted on after. Specifically:

- **"We called it" leaderboard** — a public page showing: "On [date], the system surfaced
  [TICKER] with velocity X. [N] weeks later, the stock did Y." This is the proof-of-concept
  post that drives Reddit-native word-of-mouth. It requires the system to log what it
  surfaced and what happened to those tickers afterward — which requires tracking outcomes
  against tickers.

- **Free tier design** — "free tier: top 10 tickers, 24h delay" is mentioned in the Business
  Case but is not in the PRD. If the SaaS path is the plan, the free tier needs to be in the
  v1 dashboard — not as an afterthought at month 6. You can't grow from a free tier you haven't
  built.

This doesn't require building auth now. It requires designing the dashboard with the SaaS
transition in mind.

---

### 8. Business Model — Architecture Gap

The Business Case assumes paying customers at $30/mo by month 3. The PRD says:

> *"v1 is single-user. No auth, no user management."*

These facts cannot both be true. If you plan to charge users by month 3, you need auth by
month 3. Auth is not a trivial addition to a Streamlit app — especially when Streamlit Cloud
hosting has limited support for per-user session management.

**The right call** is one of:
- Accept that the SaaS layer is month 6+ and keep v1 strictly personal (current PRD scope)
- Or scope in auth from the start using Streamlit built-in password protection as a stopgap,
  and plan the migration to proper auth (Clerk or Supabase Auth) at month 3

The current plan implies the second option is possible but doesn't design for it. Pick one
and commit.

---

### 9. Team Fit — Acknowledged Risk

The Opportunity Analysis is honest: team/founder fit scored 1/5. Solo Python developer
building a daily data pipeline + scoring model + Streamlit dashboard. The pipeline is the
risky part — not the math, but keeping it running reliably without breaking when yfinance
changes its API format or Apewisdom paginations shift.

The architecture is designed to minimize this risk (managed services, no self-hosted
infrastructure, GitHub Actions for scheduling). But the founder should set a hard rule:
if the pipeline breaks and isn't fixed within 48 hours, that's a system design problem,
not a Monday morning task.

---

### 10. Timeline — Implicit, Not Explicit

No timeline appears in the PRD or Architecture. The Business Case implies:
- Month 1: Pipeline running, Tier 3 data flowing
- Month 3: SaaS launch
- Month 6: Tier 2 data matures
- Month 12: Tier 1 data matures

The month 3 SaaS launch is the most aggressive assumption given that (a) the pipeline
needs to prove itself first and (b) no auth is designed for v1. Everything else is paced
appropriately — the phase-gate design correctly accounts for data maturity requirements.

---

## Required Changes

1. **Document the thesis validation gap explicitly.** Add a "Known Unknowns" section to
   the PRD or Architecture noting: "The Tier 1 and Tier 2 signals are unvalidated hypotheses.
   Forward collection is the validation method. Signal quality will not be known until
   month 12–24. Tier 3 (Pre-pop) can be validated in weeks by watching surfaced tickers."
   This is not a reason to stop — it is context for calibrating conviction in the system's
   outputs during the first year.

2. **Cut the email digest from v1 Must Have.** The dashboard Daily Digest view satisfies
   the user story for a personal tool. Email infrastructure is a SaaS-layer feature.
   Reclassify to "Should Have" with the label "required before first paid user."

3. **Commit to one SaaS timeline and design auth accordingly.** If SaaS is month 6+:
   keep v1 strictly single-user (no auth), add Streamlit built-in password protection at
   launch, and design auth properly at month 5. If SaaS is month 3: add auth now (Supabase
   Auth or Clerk). Do not leave this implicit — the architecture diverges significantly
   based on the answer.

---

## The Opportunity

The bigger version of this is a pattern-matching library: *"this ticker's Reddit trajectory
resembles RKLB at month 8, PLTR at month 14, and NVDA at month 6. Historically, trajectories
in this pattern resolve to a breakout within 3–6 months with 60% confidence."* That requires
2+ years of owned data and a validated labeled training set. The current architecture is
already building toward it — the ticker_tranche_log is the future ML training set. Every
day the pipeline runs and every tranche transition it logs is a data point that does not
exist anywhere else. The proprietary dataset is the moat. Build it now, and in 24 months
you will have something no competitor can replicate.

---

## Latest file

This document supersedes: none (first CEO review)
