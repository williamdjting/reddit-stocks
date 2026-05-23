---
name: blueprint-analyzeopportunity
version: 0.1.0
description: |
  Analyze a product or business opportunity. Asks probing questions about the
  problem, target user, market, and competition, then produces a structured
  opportunity analysis doc. Use when asked to "analyze this opportunity",
  "is this worth building", "evaluate this idea", or "opportunity analysis".
allowed-tools:
  - Bash
  - Read
  - Write
  - WebSearch
  - AskUserQuestion
triggers:
  - analyze this opportunity
  - is this worth building
  - evaluate this idea
  - opportunity analysis
  - should we build this
---

# /blueprint-analyzeopportunity — Opportunity Analysis

Evaluate whether a product or business idea is worth pursuing. Ask the right
questions, surface hidden assumptions, and produce a structured analysis you
can hand to any stakeholder.

## Step 1 — Gather the raw idea

Ask the user to describe the opportunity in 2–3 sentences if they haven't already.
Do not move on until you understand:
- What problem is being solved?
- Who has the problem?
- Why does the problem exist today?

## Step 2 — Ask the six forcing questions

Use AskUserQuestion to surface answers to these (bundle where context is clear):

1. **Pain intensity** — "On a scale of 1–10, how much does this problem cost the user in time, money, or frustration? Give a concrete example."
2. **Existing solutions** — "How do people solve this today? What is broken about those solutions?"
3. **User segment** — "Who is the single most important user type? Describe one real person."
4. **Market size** — "How many people or businesses have this problem? Do you have any data?"
5. **Why now** — "What has changed in the last 12 months that makes this the right time to build?"
6. **Unfair advantage** — "Why are you or your team the right people to build this?"

Record all answers. Do not skip questions — each surfaces a different failure mode.

## Step 2b — $10K/month Gate Check

Every opportunity must pass this minimum viability test before proceeding to scoring.
The baseline target is **$10,000/month recurring revenue**.

Work through the following explicitly:

**Pricing math:**
- At $50/month per customer, reaching $10K/month requires **200 paying customers**.
- A $50/month subscription is only defensible if it delivers **≥$500/month in value** to the customer.
- Valuing a customer's hour at $50, that means the product must save them **at least 10 hours per week**.

Answer these three questions using what you know so far:

1. **Value delivered** — Does the product credibly save 10+ hours/week (or equivalent dollar value)? State the specific workflow or cost it eliminates.
2. **Reachability** — Is a pool of 200+ paying customers reachable? Name the channel (community, SEO, outbound, marketplace, etc.) and whether it's realistic in under 12 months.
3. **Price fit** — Would the target user pay $50/month? Is there evidence (comparable tools, willingness-to-pay signals, or analogous markets)?

If you cannot make a credible case for all three, flag the opportunity as **failing the $10K/month gate** and note it clearly in the output. Do not suppress this finding — an opportunity that can't reach $10K/month with a defensible price is not worth building without a different pricing model or a significantly larger addressable pool.

If the opportunity uses a different price point (enterprise, usage-based, etc.), rescale the math: the gate is $10K/month, not strictly $50/customer. Show the revised unit economics explicitly.

## Step 3 — Research (if web access is available)

Search for:
- Top 3 existing competitors or alternatives
- Recent funding or acquisition news in this space
- Any market size estimates or analyst reports

Summarize findings in 3–5 bullet points. Note signal strength (strong evidence vs speculation).

## Step 4 — Score the opportunity

Rate each dimension 1–5 based on the gathered information:

| Dimension | Score (1–5) | Notes |
|-----------|-------------|-------|
| Pain severity | | |
| Market size | | |
| Timing / why now | | |
| Competitive differentiation | | |
| Team / founder fit | | |
| $10K/month viability | | Value delivered ≥10 hrs/week saved, 200 reachable customers, $50/mo price fit |

Total possible: 30. Rough guidance:
- 24–30: Strong signal. Recommend proceeding to PRD.
- 16–23: Mixed signal. Identify the weakest dimension and address it first.
- Below 16: Significant gaps. Recommend more discovery before building.

**Hard gate:** If the $10K/month viability dimension scores 1–2, do not recommend
proceeding regardless of total score. Unit economics must be credible before anything else.

## Step 5 — Write the opportunity analysis doc

Check for an existing analysis file:

```bash
ls -t OPPORTUNITY-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`OPPORTUNITY-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`OPPORTUNITY-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# Opportunity Analysis: <Name>

**Generated:** <YYYY-MM-DD HH:MM>
**Status:** Draft

## The Problem
<1–2 paragraphs. What is broken and why it matters.>

## Target User
<Who has this problem. One concrete persona.>

## Why Now
<What changed. Market timing signal.>

## Competitive Landscape
<Top 3 alternatives and their weaknesses.>

## $10K/Month Viability
**Price point:** $<X>/month
**Customers needed:** <$10,000 / price> paying customers
**Value delivered:** <How the product saves ≥10 hrs/week or equivalent dollar value per customer>
**Reachability:** <Channel and realistic timeline to 200+ customers>
**Gate result:** PASS / FAIL / CONDITIONAL — <one sentence of rationale>

## Opportunity Score
<Score table from Step 4, including $10K/month viability row.>

## Recommendation
<One of: Proceed to PRD | Do more discovery | Do not pursue. One paragraph of rationale.
If the $10K/month gate failed, this must be "Do more discovery" or "Do not pursue" — explain what would need to change.>

## Open Questions
<List of unresolved assumptions that must be validated.>

## Latest file
This document supersedes: <previous OPPORTUNITY-*.md filename, if one exists>
```

## Step 6 — Handoff

Tell the user:
- The overall score and recommendation
- The single weakest dimension to address
- If recommendation is "Proceed", suggest running `/blueprint-prd` next