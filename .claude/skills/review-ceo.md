---
name: review-ceo
version: 0.1.0
description: |
  Strategic CEO-level review of a plan, feature, or product decision. Challenges
  scope and assumptions, finds the 10x opportunity hiding inside the request, and
  identifies what to cut. Four modes: Expansion, Selective Expansion, Hold Scope,
  Reduction. Use when asked to "CEO review", "challenge this plan", "strategic
  review", or "is this the right thing to build".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - ceo review
  - challenge this plan
  - strategic review
  - is this the right thing to build
  - scope review
  - challenge my assumptions
---

# /review-ceo — CEO Review

Think like a first-principles founder. The goal is not to approve the plan —
it is to find what is wrong with it before any code is written.

## Step 1 — Read everything

Find the most recent version of each context file:

```bash
ls -t OPPORTUNITY-*.md BUSINESS_CASE-*.md PRD-*.md DESIGN-*.md TECHSTACK-*.md 2>/dev/null | head -10
```

Open the most recent of each type. Also check for `CLAUDE.md` and any notes.

Read them all. Understand what has been decided and what is still open.

If nothing exists, ask the user to describe what they are building and why.

## Step 2 — Choose the mode

Ask the user (or infer from context) which mode applies:

- **Expansion** — "What if we built 10x more?" Push the vision further. Find the bigger problem this is really solving.
- **Selective Expansion** — "This part is right, this part is too small." Agree on what's correct, challenge what's undersized.
- **Hold Scope** — "This is the right scope. Don't let me add to it." Defend against feature creep. Say no firmly.
- **Reduction** — "What is the minimum that proves the idea?" Find the wedge. Cut everything that isn't the core.

Default to **Reduction** for early-stage work. Default to **Hold Scope** for work
already in progress with committed scope.

## Step 3 — Apply the ten-section challenge

Work through each section. For every finding, state the assumption being challenged
and the question the builder needs to answer.

**1. Problem definition**
Is the problem stated precisely? Or is it vague enough to mean anything?
"We want to improve the user experience" is not a problem. "Users abandon the
onboarding flow at step 3 because they don't understand what they're signing up for"
is a problem.

**2. Who is the customer**
Is the target user specific? One real person, not a demographic.
Challenge: "If you shipped this tomorrow, who would you call first to demo it to?"

**3. The 10-star product**
What would make this genuinely remarkable — not just better than the competition?
What would make someone tell three friends about it unprompted?

**4. What to cut**
What in the current plan does not directly serve the core value proposition?
Every feature that is "nice to have" is a feature that delays the core.

**5. What is being avoided**
What is the hardest, most important problem in this space that the plan does not address?
Is it being avoided because it's genuinely out of scope — or because it's hard?

**6. The competition**
What do the top 3 competitors do well? What do users complain about in their reviews?
Is the plan differentiated on the things that actually matter to users?

**7. The distribution**
How does this product reach its first 100 users? Is that built into the product itself
or is it an afterthought?

**8. The business model**
How does this make money? Is monetization designed in or bolted on later?
If it is free, what is the path to paid — and is the free tier a wedge or a trap?

**9. The team fit**
Is this the right team to build this? What unfair advantage does the team have?
What is the single biggest capability gap?

**10. The timeline**
Is the timeline realistic? What is the most optimistic assumption baked in?
What is the first thing that will slip?

## Step 4 — State the verdict

After the ten sections, give a clear verdict:

- **Proceed as planned** — the scope is right, the reasoning is sound
- **Proceed with modifications** — list the specific changes required
- **Stop and rethink** — identify the fundamental problem with the current direction

Do not hedge. A vague verdict is worse than no verdict.

## Step 5 — Write the review

Check for an existing CEO review:

```bash
ls -t CEO_REVIEW-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`CEO_REVIEW-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`CEO_REVIEW-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# CEO Review: <Plan / Feature Name>

**Generated:** <YYYY-MM-DD HH:MM>
**Mode:** Expansion | Selective Expansion | Hold Scope | Reduction
**Verdict:** Proceed | Proceed with modifications | Stop and rethink

## Summary
<3–5 sentences. What this is, what was challenged, what the verdict is.>

## Findings
<One section per finding from Step 3. Only include sections with actual findings.>

## Required Changes (if verdict is Proceed with modifications)
<Numbered list. Each item is a specific, actionable change.>

## The Opportunity (if verdict is Proceed or Expand)
<What the bigger version of this looks like. One paragraph.>

## What to Cut (if applicable)
<Specific items from the current plan to remove.>

## Latest file
This document supersedes: <previous CEO_REVIEW-*.md filename, if one exists>
```

## Step 6 — Handoff

Tell the user the verdict and the single most important change to make (if any).
If Proceed: suggest `/review-eng` to lock architecture.
If Stop and rethink: suggest `/blueprint-analyzeopportunity` to restart from the problem.