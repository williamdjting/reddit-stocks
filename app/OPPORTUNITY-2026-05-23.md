# Opportunity Analysis: Pre-Breakout Reddit Sentiment Monitor

**Generated:** 2026-05-23 00:20
**Status:** Draft

## The Problem

Most Reddit stock tracking tools show what's already trending — they're lagging indicators.
By the time a ticker appears on Swaggy Stocks or Apewisdom, the informed retail crowd has
already loaded up and the move is partially priced in.

The real opportunity is the period *before* breakout: when a small or mid-cap stock starts
accumulating genuine Reddit conversation — not spam, not hype, but growing organic discussion
across subreddits — weeks or months before the price reacts. Palantir (PLTR) in mid-2023
and Rocket Lab (RKLB) in early-to-mid 2024 are the clearest recent examples: both had
measurably accelerating Reddit conversation well before their major price runs. Anyone
tracking mention velocity in those windows would have had a significant edge.

The problem is that no tool surfaces this signal. Existing trackers count total mentions
today vs yesterday. None track the acceleration curve of an *unknown* ticker over a
4–12 week window, or filter specifically for early-stage names (sub-$5B market cap,
no mainstream analyst coverage, no ETF inclusion yet).

## Target User

**Primary:** Retail swing trader or position trader, 25–45 years old. Not a day trader
chasing intraday moves — someone who holds for weeks to months and is looking for the
next 5–10× idea before it becomes obvious. Already reads Reddit (r/wallstreetbets,
r/stocks, r/investing, sector-specific subs like r/space, r/biotech, r/electricvehicles)
as part of their research process. Has experienced missing a PLTR or RKLB type move
and wants a systematic way to catch the next one. Willing to pay $30–50/month for a
credible early-warning signal.

## Why Now

Three forces converge in 2025–2026:

1. **Reddit as a proven market signal.** The 2021–2024 meme stock era proved Reddit moves
   small-cap prices. Institutional players now monitor it. Retail traders know it matters
   but lack systematic tools.
2. **Post-IPO Reddit data landscape.** Reddit's 2024 IPO and API restructuring created
   a clearer (if more expensive) path to legitimate data access. The fragility of the
   scraping era is giving way to a more stable API model.
3. **LLMs make ticker extraction and sentiment classification cheap.** Accurately
   identifying a stock ticker in a comment ("$RKLB", "Rocket Lab", "the rocket company
   Bezos is backing") and classifying sentiment used to require significant NLP
   infrastructure. Today it's a commodity. The moat is the data and the scoring model,
   not the NLP.

## Competitive Landscape

No direct competitor does pre-breakout early-stage sentiment detection. Adjacent players:

- **Swaggy Stocks** — tracks WSB mentions, shows what's trending *now*. No velocity
  tracking, no small-cap filter, no "before the move" framing.
- **Apewisdom.io** — free mention counts, very basic. Shows the most-mentioned tickers
  in the last 24h. No trajectory, no filtering by market cap or stage.
- **Quiver Quantitative** — Reddit data as one of many alternative data sources.
  Designed for quants, $50–200/month, not positioned for retail pre-breakout hunting.
- **Unusual Whales** — options flow + social, focused on institutional signals. Different
  user and different signal.

**The gap is real and unoccupied:** no product is built specifically around the thesis
"catch the 5–10× before Reddit makes it obvious." The framing, the scoring model
(velocity + acceleration + market cap filter), and the UI are all differentiated.

## $10K/Month Viability

**Price point:** $40/month (justified by asymmetric trade value)
**Customers needed:** 250 paying customers
**Value delivered:** A single pre-breakout catch — getting into RKLB at $4 before
it ran to $25, or PLTR at $12 before it ran to $80 — returns thousands of dollars on
a modest position. $40/month is noise compared to one correct early call. The value
proposition is not "saves you time" but "gives you an edge that pays for itself with
one trade per quarter."
**Reachability:** Target users are highly concentrated and vocal in Reddit's own
communities, finance Twitter/X, and stock Discord servers. A free "early signal of
the week" newsletter or public leaderboard ("we called RKLB 6 weeks early") is a
viral acquisition channel. 250 customers is reachable in under 12 months with the
right proof-of-concept post.
**Gate result:** PASS — strong asymmetric value proposition, reachable audience,
credible price point. The differentiated framing ("pre-breakout," not "trending")
removes the comparison to free tools.

## Opportunity Score

| Dimension | Score (1–5) | Notes |
|-----------|-------------|-------|
| Pain severity | 5 | Missing a 5–10× move is extremely painful and memorable |
| Market size | 3 | Smaller segment than generic retail traders — serious swing traders |
| Timing / why now | 4 | Reddit proven signal, LLMs lower build cost, API stabilizing |
| Competitive differentiation | 4 | No one owns the pre-breakout early-stage angle |
| Team / founder fit | 1 | No technical or trading edge identified yet — biggest risk |
| $10K/month viability | 4 | Asymmetric value → $40/mo price defensible, 250 users reachable |

**Total: 21 / 30**

## Recommendation

**Do more discovery — then proceed.**

The pre-breakout angle is genuinely differentiated and the unit economics are stronger
than a generic sentiment tracker. The score moved from 18 to 21 with this clarification,
and the path to "Proceed" is visible. Two things must be resolved first:

1. **Backtest the thesis.** Before writing a PRD, validate historically: did PLTR and
   RKLB (and others) actually show measurable Reddit conversation acceleration 4–8 weeks
   before their breakouts? If yes, that's your marketing story and your product validation
   in one shot. Build a simple script, pull historical Reddit data, and show the signal
   visually. This de-risks everything downstream.

2. **Founder fit.** "Neither yet" is the single biggest risk. The builder path is clear:
   this is a data pipeline + scoring model + dashboard. If you can build that (or partner
   with someone who can), the differentiated angle does the rest. Get specific about who
   builds it before moving to PRD.

Once the backtest shows signal and the build plan is clear, run `/blueprint-businesscase`
and then `/blueprint-prd`. This is worth building.

## Open Questions

- **Backtest results:** Did the PLTR/RKLB thesis actually hold in historical Reddit data?
  Which other tickers would have been caught? What were the false positives?
- **Scoring model:** What combination of signals defines "pre-breakout"? (Velocity over
  4 weeks, market cap < $5B, no mainstream analyst coverage, sentiment quality score?)
- **Subreddit coverage:** Which subs carry the most signal for early-stage names?
  WSB is noisy; r/stocks, r/investing, and niche sector subs may be higher signal.
- **Data source:** Reddit API at current pricing ($0.24/1K API calls) — is this
  economically viable at scale? Or scraping? Or a data vendor (PushShift archive)?
- **Alert mechanism:** Dashboard, email digest, Discord bot, mobile push?
- **False positive problem:** How do you prevent the tool from surfacing pump-and-dump
  penny stocks that get artificially mentioned? Quality filtering is critical.
- **B2B angle:** Hedge funds and quant firms would pay $500–2,000/month for this data
  as an API feed. Worth considering as a revenue layer alongside retail.

## Latest file

This document supersedes: *(none — first analysis)*
