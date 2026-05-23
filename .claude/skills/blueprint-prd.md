---
name: blueprint-prd
version: 0.1.0
description: |
  Write a Product Requirements Document (PRD). Covers goals, success metrics,
  user stories, functional requirements, non-functional requirements, and
  explicit out-of-scope boundaries. Use when asked to "write a PRD",
  "product requirements", "requirements doc", or "spec this feature".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - write a prd
  - product requirements
  - requirements doc
  - spec this feature
  - write requirements
---

# /blueprint-prd — Product Requirements Document

Turn a product idea into a structured PRD that aligns engineering, design,
and stakeholders before a line of code is written.

## Step 1 — Read existing context

Find and read the most recent context files:

```bash
ls -t OPPORTUNITY-*.md BUSINESS_CASE-*.md DESIGN-*.md 2>/dev/null | head -5
```

Open the most recent files found. Pull goals, user descriptions, and constraints.

If no context exists, ask:
- What feature or product are we speccing?
- Who is the primary user?
- What is the business goal this serves?

## Step 2 — Define success

Before writing requirements, get agreement on what "done" looks like.

Ask or derive:
- **Primary success metric** — one number that goes up or down (e.g., activation rate, task completion time, revenue)
- **Secondary metrics** — 2–3 supporting signals
- **Anti-metrics** — what must NOT get worse (e.g., load time, error rate, churn)
- **Target** — specific value and timeline (e.g., "+10% activation in 30 days")

Write these down before any requirements — they constrain scope.

## Step 3 — Write user stories

For each user type, write stories in this format:

```
As a <user type>,
I want to <do something>,
So that <I get this value>.

Acceptance criteria:
- Given <starting state>, when <action>, then <expected result>
```

Cover:
- Primary user (the main beneficiary)
- Secondary users (admins, reviewers, other roles affected)
- Edge case users (first-time user, user returning after long absence)

## Step 4 — Define functional requirements

Group by feature area. Use MoSCoW priority:
- **Must have** — without this, the feature does not ship
- **Should have** — strong expectation, cut only under pressure
- **Could have** — nice to have, cut first
- **Won't have** — explicitly out of scope for this version

Format each requirement as a testable statement:
> "The system must allow users to upload a CSV file up to 10MB and process it within 30 seconds."

Not: "The system should handle file uploads."

## Step 5 — Define non-functional requirements

| Category | Requirement |
|----------|-------------|
| Performance | |
| Scalability | |
| Security | |
| Accessibility | |
| Browser / device support | |
| Uptime / SLA | |
| Data retention | |

Only include rows that are actually constrained. Do not add boilerplate.

## Step 6 — Define what is explicitly out of scope

List at least 3 things this PRD does NOT cover. This prevents scope creep
and sets expectations with engineering.

## Step 7 — Write the PRD

Check for an existing PRD:

```bash
ls -t PRD-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`PRD-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`PRD-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# PRD: <Feature Name>

**Generated:** <YYYY-MM-DD HH:MM>
**Status:** Draft | Review | Approved
**Owner:** <user>

## Goal
<One sentence. Why we are building this.>

## Success Metrics
| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| | | | |

Anti-metrics (must not regress):
- <metric>

## User Stories
<Stories from Step 3>

## Functional Requirements

### Must Have
- <requirement>

### Should Have
- <requirement>

### Could Have
- <requirement>

### Won't Have (this version)
- <item>

## Non-Functional Requirements
<Table from Step 5>

## Out of Scope
<List from Step 6>

## Open Questions
<Unresolved assumptions or decisions needed before engineering starts>

## Dependencies
<Other teams, systems, or external services this relies on>

## Latest file
This document supersedes: <previous PRD-*.md filename, if one exists>
```

## Step 8 — Handoff

Tell the user:
- Count of Must Have requirements
- The most important open question to resolve before engineering starts
- Suggest `/blueprint-design` if UX work is needed
- Suggest `/blueprint-techstack` if architecture decisions are needed
- Suggest `/review-eng` for engineering readiness review