---
name: blueprint-scenarios
version: 0.2.0
description: |
  Convert PRD user stories into Gherkin acceptance scenarios. Reads the user
  stories from PRD.md, writes a concrete Gherkin scenario for each story
  covering happy path, edge cases, and failure modes, and saves them to a
  dated SCENARIOS file. Use when asked to "write scenarios", "gherkin scenarios",
  "acceptance scenarios", "write test scenarios from PRD", or "convert user stories to scenarios".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - write scenarios
  - gherkin scenarios
  - acceptance scenarios
  - write test scenarios from prd
  - convert user stories to scenarios
  - scenarios from prd
  - write acceptance tests
---

# /blueprint-scenarios — Gherkin Acceptance Scenarios from PRD

Turn PRD user stories into precise Gherkin scenarios that can drive
implementation, automated tests, and manual QA.

Read `blueprint-scenarios/Gherkin.md` for the full Gherkin syntax reference
and usage examples.

## Step 1 — Read the PRD

```bash
ls -t PRD-*.md 2>/dev/null | head -5
```

Open the most recent `PRD-*.md` file. Extract every user story from the
"User Stories" section. List them out before writing any scenarios:

```
Story 1: As a <user>, I want to <action>, so that <value>
  Acceptance criteria: <list>
Story 2: ...
```

If no PRD exists, ask the user for the user stories before continuing.
Do not generate scenarios without a source of truth.

## Step 2 — Plan the scenario coverage for each story

For every user story, you will write at least 3 scenarios:

1. **Happy path** — the user completes the story successfully
2. **Edge case** — a valid but unusual input or state
3. **Failure** — an invalid action or system error; the system responds correctly

For stories with explicit acceptance criteria, every criterion becomes
at least one scenario.

## Step 3 — Write Gherkin scenarios

For each user story, write a `Feature` block with its scenarios.

Use the Gherkin format from `Gherkin.md`:

```gherkin
Feature: <Feature name from the user story>
  <One-line description from the story's "so that" clause>

  Background:
    Given <shared precondition for all scenarios in this feature, if any>

  Scenario: <Name — written as the outcome, not the action>
    Given <concrete starting state with real values>
    When  <the specific action>
    Then  <the observable outcome>
    And   <additional outcome if needed>
    But   <outcome that must NOT occur, if needed>
```

Rules for writing good scenarios:
- Use **concrete values** — `"alice@example.com"`, `$49.99`, not "a valid email"
- One `When` per scenario — if two actions are needed, split into two scenarios
- `Then` must assert something **observable** — a UI element, a response code,
  a database state, an email sent
- Name scenarios after the outcome: "User is redirected to dashboard after login"
  not "User logs in"
- Use `Scenario Outline` + `Examples` table for parameterized cases (testing
  multiple valid inputs against the same behavior)

## Step 4 — Mark each scenario's automation type

After writing each scenario, annotate it with:

```
# Automation: unit | integration | e2e | manual
```

- **unit** — pure logic test, no browser, no DB
- **integration** — hits the DB or an API, no browser
- **e2e** — requires a full browser and live stack
- **manual** — subjective, exploratory, or too costly to automate

## Step 5 — Identify the P0 scenarios

Mark scenarios `# Priority: P0` if the feature cannot ship without them passing.
These are the scenarios where a failure means data loss, security violation,
or complete feature break.

## Step 6 — Write the output file

Check for an existing SCENARIOS file:

```bash
ls -t SCENARIOS-*.md 2>/dev/null | head -3
```

**Never overwrite an existing SCENARIOS file.** Create a new file with
today's date:

```
SCENARIOS-<YYYY-MM-DD>.md
```

If a file for today already exists, append the time:
`SCENARIOS-<YYYY-MM-DD>-<HHMM>.md`

File header:

```markdown
# Scenarios: <Feature or Project Name>

Generated: <YYYY-MM-DD HH:MM>
Source PRD: <PRD filename referenced>
Status: Draft | Review | Approved

## Summary

Total scenarios: X
P0: X | Automate (unit): X | Automate (integration): X | E2E: X | Manual: X

## Scenarios
```

Then write the full Gherkin blocks, grouped by Feature (one Feature per
user story).

At the bottom, add:

```markdown
## Latest file

This document supersedes: <previous SCENARIOS-*.md filename, if one exists>
```

## Step 7 — Check for system diagram readiness

After writing the SCENARIOS file, check whether the other two system design
artifacts are also present:

```bash
ls TECHSTACK-*.md ARCHITECTURE-*.md 2>/dev/null
```

If both `TECHSTACK-*.md` AND `ARCHITECTURE-*.md` exist (any version), generate
`SYSTEM_DIAGRAM.html` now. See the **System Diagram HTML** section below.

If either is missing, skip this step — the diagram will be generated when
the missing skill completes.

---

## System Diagram HTML

Generate `SYSTEM_DIAGRAM.html` — a self-contained HTML file (no external
dependencies — inline all CSS) that gives any stakeholder a complete picture
of the system design and how user scenarios flow through it.

Read the most recent versions of:
- `SCENARIOS-*.md` — user scenarios and acceptance criteria
- `TECHSTACK-*.md` — technology choices and API style
- `ARCHITECTURE-*.md` — components, data flow, and integration points

Structure the HTML in two main sections:

---

### Section 1: System Architecture

**Component map:**
Draw each system component as a styled box arranged in logical tiers:
- Tier 1 (top): Client(s) — web app, mobile app, CLI
- Tier 2: API / backend layer — servers, API gateway
- Tier 3: Data layer — databases, cache, queues
- Tier 4 (bottom): External services — auth, email, payments, storage

Each component box shows:
- Component name (header)
- Technology (e.g., React, Next.js, PostgreSQL, Redis)
- Purpose (one line)

Connect components with labeled arrows showing the protocol or mechanism
(HTTPS, SQL, Redis protocol, WebSocket, SMTP, etc.).

**Technology stack summary panel:**
A reference table beside the diagram:
```
Layer          | Technology        | Rationale (one line)
Frontend       | React + Vite      | ...
Backend        | Node.js + Express | ...
Database       | PostgreSQL 15     | ...
Auth           | Clerk             | ...
```

**Integration points panel:**
For every external service: name, purpose, failure mode, and fallback.

---

### Section 2: Scenario Flows

For each Gherkin Feature from SCENARIOS.md, render a scenario flow card:

**Feature card:**
- Feature name as the card header
- Source user story (the "so that" clause) as a subtitle
- A step-by-step flow diagram for the **happy path** scenario:
  - Each step shown as a numbered node
  - Given steps in blue, When steps in orange, Then steps in green
  - Arrows connecting the steps left-to-right or top-to-bottom
- A compact list of edge case and failure scenarios below the diagram
  (no full diagram — just the scenario name and expected outcome)
- P0 badge on any scenario marked Priority: P0

---

### Style guidance for SYSTEM_DIAGRAM.html:

- Page title: "System Diagram — [Product Name]"
- Generated date and source files in a metadata bar
- Section 1 and Section 2 as tabbed panels or scrollable sections with
  anchor links in a top navigation bar
- Component boxes: distinct background color per tier
- Scenario step nodes: colored by step type (Given/When/Then)
- SVG or CSS-based connectors for the architecture and flow diagrams
- Clean white background, dark text, readable at any zoom level
- Sticky top nav so users can jump between sections

After generating the file, confirm: "Generated `SYSTEM_DIAGRAM.html` —
open in a browser to view the full system design and scenario flows."

---

## Step 8 — Handoff

Tell the user:
- How many scenarios were written total
- How many are P0
- Which stories had the most edge cases
- The output filename
- Whether `SYSTEM_DIAGRAM.html` was generated or what is still needed
- Suggest `/blueprint-testing` to plan the full test strategy
- Suggest `/perform-testing` to implement the automated scenarios