---
name: blueprint-businesscase
version: 0.1.0
description: |
  Write a business case document for a feature, product, or initiative.
  Covers problem statement, proposed solution, costs, expected return, risks,
  and a go/no-go recommendation. Use when asked to "write a business case",
  "make the case for this", "justify this investment", or "business case".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - write a business case
  - make the case for this
  - justify this investment
  - business case
  - should we invest in this
---

# /blueprint-businesscase — Business Case

Turn a proposal into a defensible business case. Collect the inputs, structure
the argument, and write a document that decision-makers can use to say yes or no.

## Step 1 — Understand the proposal

Find and read the most recent context files:

```bash
ls -t OPPORTUNITY-*.md PRD-*.md 2>/dev/null | head -5
```

Open the most recent files found.
If nothing exists, ask the user:
- What are you proposing to build or do?
- Who is the decision-maker this document is for?
- What is the timeline and budget envelope?

## Step 2 — Gather the numbers

Use AskUserQuestion to collect concrete inputs. Do not guess or fill in
placeholders — a business case with made-up numbers is worse than none.

Ask:
1. **Cost to build** — engineering time, tooling, external services (one-time)
2. **Cost to run** — ongoing infrastructure, support, maintenance (monthly)
3. **Expected benefit** — revenue increase, cost reduction, churn reduction (specific: $X/month or Y% reduction)
4. **Time to value** — how many months until the benefit is realized?
5. **Confidence level** — are these estimates backed by data or gut feel?

If the user cannot answer, note the assumption gap and flag it as a risk.

## Step 3 — Calculate ROI

Compute:
- **Total 12-month cost** = build cost + (12 × monthly run cost)
- **Total 12-month benefit** = monthly benefit × (12 − time to value)
- **Net 12-month return** = benefit − cost
- **Payback period** = build cost / monthly net benefit (months)
- **Confidence-adjusted return** = net return × confidence % (e.g., 70% confident → multiply by 0.7)

Show the math. Do not hide it in prose.

## Step 4 — Identify risks

List the top 3–5 risks with severity (High / Medium / Low) and a one-line mitigation:
- Technical risk: can we actually build it?
- Adoption risk: will users actually use it?
- Market risk: will the expected benefit materialize?
- Resource risk: do we have the people?
- Timing risk: does this depend on something outside our control?

## Step 5 — Write the business case doc

Check for an existing business case:

```bash
ls -t BUSINESS_CASE-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`BUSINESS_CASE-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`BUSINESS_CASE-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# Business Case: <Initiative Name>

**Generated:** <YYYY-MM-DD HH:MM>
**Prepared for:** <decision-maker>
**Recommendation:** GO / NO-GO / CONDITIONAL GO

## Executive Summary
<3–5 sentences. Problem, proposed solution, expected return, recommendation.>

## Problem Statement
<What is broken, what it costs us today, why it matters now.>

## Proposed Solution
<What we are building or doing. Scope in, scope out.>

## Investment Required
| Item | Cost |
|------|------|
| Build (one-time) | $ |
| Run (monthly) | $ |
| **Total Year 1** | $ |

## Expected Return
| Metric | Current | Projected | Δ |
|--------|---------|-----------|---|
| | | | |

**Payback period:** X months
**12-month net return:** $X (confidence-adjusted)

## Risk Register
| Risk | Severity | Mitigation |
|------|----------|------------|
| | | |

## Alternatives Considered
<What else we looked at and why this option wins.>

## Recommendation
<GO / NO-GO / CONDITIONAL GO. One paragraph of rationale. What must be true
for the decision to change.>

## Latest file
This document supersedes: <previous BUSINESS_CASE-*.md filename, if one exists>
```

## Step 6 — Handoff

Tell the user the recommendation and the single number that most changes the outcome.
If GO, suggest running `/blueprint-prd` or `/blueprint-techstack` next.