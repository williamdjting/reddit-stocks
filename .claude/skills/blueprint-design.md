---
name: blueprint-design
version: 0.1.0
description: |
  Create a product design specification. Covers user flows, screen-by-screen
  descriptions, component breakdown, interaction patterns, and edge case
  handling. Use when asked to "write a design spec", "design this feature",
  "spec out the UX", or "design document".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - write a design spec
  - design this feature
  - spec out the ux
  - design document
  - design spec
---

# /blueprint-design — Design Specification

Translate a product idea into a clear design specification that engineers
can implement and stakeholders can review without ambiguity.

## Step 1 — Read existing context

Find and read the most recent context files:

```bash
ls -t PRD-*.md OPPORTUNITY-*.md 2>/dev/null | head -5
```

Open the most recent files found. Also check for `REQUIREMENTS.md`.

If none exist, ask the user:
- What is the feature or product being designed?
- Who is the primary user?
- What is the one thing the user must be able to do?

## Step 2 — Define the user flows

For each primary user goal, write a numbered flow:

```
Flow: <Name>
Actor: <who is doing this>
Precondition: <what must be true before this starts>
Steps:
  1. User <action>
  2. System <response>
  3. ...
Success: <what the user sees / has when done>
Failure paths: <what can go wrong at each step>
```

Cover at minimum:
- The primary happy path (most common case)
- The first-time / empty state
- The error state (something goes wrong)
- An edge case (unexpected input or timing)

## Step 3 — Describe each screen or surface

For every distinct screen, page, or modal in the flow:

```
### <Screen Name>

**Purpose:** What the user accomplishes here.

**Entry points:** How the user gets here.

**Layout:**
- Header: <what's shown>
- Body: <primary content and controls>
- Footer / actions: <CTAs, navigation>

**States:**
- Default (data present)
- Empty (no data yet)
- Loading
- Error

**Interactions:**
- <control> → <what happens>
```

## Step 4 — Define the component breakdown

List the UI components needed:

| Component | Description | Props / Inputs | States |
|-----------|-------------|----------------|--------|
| | | | |

Note which components are new vs reuse of existing ones.

## Step 5 — Specify interaction patterns

Document non-obvious behaviors:
- Optimistic updates vs wait-for-server
- Debounce / throttle on inputs
- Keyboard navigation requirements
- Mobile-specific behavior (tap targets, swipe)
- Accessibility requirements (ARIA roles, focus management)

## Step 6 — Identify open design questions

List decisions that need product or stakeholder input before implementation:
- Tradeoffs between simplicity and power
- Anything requiring A/B testing or validation
- Anything depending on technical constraints not yet known

## Step 7 — Write the design spec

Check for an existing design spec:

```bash
ls -t DESIGN-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`DESIGN-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`DESIGN-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# Design Spec: <Feature Name>

**Generated:** <YYYY-MM-DD HH:MM>
**Status:** Draft | Review | Approved

## Goal
<One sentence. What this design enables for the user.>

## User Flows
<Flows from Step 2>

## Screens
<Screen descriptions from Step 3>

## Component Breakdown
<Table from Step 4>

## Interaction Patterns
<Notes from Step 5>

## Open Questions
<List from Step 6>

## Out of Scope
<Explicitly list what is NOT being designed here.>

## Latest file
This document supersedes: <previous DESIGN-*.md filename, if one exists>
```

## Step 8 — Handoff

Tell the user:
- How many screens are in scope
- Which open questions are blockers for engineering to start
- Suggest `/blueprint-techstack` or `/blueprint-prd` if not already done
- Suggest `/review-eng` once engineers review the spec