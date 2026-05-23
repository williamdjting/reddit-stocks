---
name: blueprint-testing
version: 0.1.0
description: |
  Plan the test strategy for an application or feature before writing any
  tests. Defines the test pyramid, coverage targets, what to test at each
  layer, tooling choices, and which scenarios from SCENARIOS.md map to
  which test types. Use when asked to "plan the testing strategy",
  "test plan", "what should we test", "testing approach",
  or "define our test coverage".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - plan the testing strategy
  - test plan
  - what should we test
  - testing approach
  - define our test coverage
  - testing strategy
  - test coverage plan
  - write a test plan
---

# /blueprint-testing — Test Strategy Plan

Define what to test, at which layer, with which tools, and to what coverage
target — before writing a single test. A test plan written upfront prevents
over-testing trivial code and under-testing critical paths.

## Step 1 — Read existing context

Check for:
- `SCENARIOS-*.md` — Gherkin scenarios already defined (latest dated file)
- `PRD-*.md` — requirements that drive what must be tested
- `TECHSTACK.md` — stack in use (determines tooling choices)
- `CLAUDE.md` — existing test commands

```bash
ls -t SCENARIOS-*.md 2>/dev/null | head -3
ls -t PRD-*.md 2>/dev/null | head -3
```

## Step 2 — Define the test pyramid

Decide the proportion of tests at each layer:

```
         /\
        /E2E\         (few — slow, expensive, high confidence)
       /──────\
      /Integr.\       (moderate — hits DB/API, catches wiring bugs)
     /──────────\
    /  Unit Tests \   (many — fast, isolated, catches logic bugs)
   /──────────────\
```

For most apps, a healthy pyramid is: **~70% unit / ~20% integration / ~10% E2E**

Adjust based on the app type:
- **CRUD API** — heavier integration layer (DB queries are the logic)
- **Complex frontend** — heavier E2E (UI flows are the product)
- **Pure library/utility** — heavier unit (logic is everything)

## Step 3 — Map SCENARIOS to test layers

Read the latest `SCENARIOS-*.md` file. For every Gherkin scenario,
assign it to a test layer and explain why:

```
Scenario: Successful login with valid credentials
→ Integration test
   Why: Requires DB lookup and session creation — pure unit can't verify this

Scenario: Cart total updates when quantity changes
→ Unit test
   Why: Pure calculation — no external dependencies

Scenario: User completes full checkout flow
→ E2E test
   Why: Spans auth, cart, payment, confirmation — needs a real browser
```

## Step 4 — Define tooling for each layer

For the stack in use, pick the test tooling:

| Layer | Example tools | When to use each |
|-------|--------------|-----------------|
| Unit | Jest, Vitest, Bun test, pytest, Go test | Logic, transforms, calculations |
| Integration | Supertest, httpx, testcontainers | API handlers, DB queries |
| E2E | Playwright, Cypress, Selenium | Critical user flows |
| Snapshot | Storybook, Percy | UI regression |

Pick one tool per layer. Document the choice and the reason.

## Step 5 — Define coverage targets

Set coverage targets that reflect risk, not vanity metrics:

```
Critical paths (auth, payments, data mutations): 90%+ branch coverage
Business logic (calculations, transformations): 85%+ branch coverage
Utility functions: 80%+ line coverage
UI components: Key interactions covered by E2E; unit tests for logic only
Configuration / boilerplate: No coverage target needed
```

Do not set a blanket "80% coverage" target across the entire codebase.
Coverage targets should be higher where bugs cause more damage.

## Step 6 — Identify what NOT to test

Explicitly list what will not be tested and why:

```
Not tested:
- Third-party library internals (Stripe SDK, auth provider) — they test their own code
- Generated code (ORM migrations, type definitions) — no logic to test
- Framework scaffolding (router setup, middleware wiring) — integration tests cover it
- UI layout and styling — manual QA or visual regression tool, not unit tests
```

Testing things that can't break wastes time and creates fragile tests.

## Step 7 — Define the test data strategy

How will tests get their data?

- **Unit tests** — in-line fixtures (small, readable, right next to the test)
- **Integration tests** — factory functions that create minimal valid records
- **E2E tests** — seeded test database, reset before each run

Decide:
- Where test fixtures live (`test/fixtures/`, `__fixtures__/`, inline)
- How the DB is reset between integration tests (transaction rollback vs truncate)
- Whether E2E tests run against a real staging DB or a seeded test DB

## Step 8 — Define the CI test split

How tests run in CI:

```
On every commit:
  - Lint
  - Unit tests (must be < 30s)

On every PR:
  - Unit tests
  - Integration tests
  - Build check

Before merge to main:
  - Full test suite including E2E
  - Coverage report (fail if below target)

Nightly / weekly:
  - Performance regression tests
  - Visual regression tests
```

## Step 9 — Write the test plan

Check for an existing test plan:

```bash
ls -t TESTPLAN-*.md 2>/dev/null | head -3
```

**Never overwrite an existing TESTPLAN file.** Create a new dated file:

```
TESTPLAN-<YYYY-MM-DD>.md
```

If a file for today already exists, append the time:
`TESTPLAN-<YYYY-MM-DD>-<HHMM>.md`

File contents:

```markdown
# Test Plan: <Feature or Project Name>

Generated: <YYYY-MM-DD HH:MM>
Source: <SCENARIOS filename>, <PRD filename>
Status: Draft | Review | Approved

## Test pyramid target
Unit: X% | Integration: Y% | E2E: Z%

## Tooling
Unit: <tool>
Integration: <tool>
E2E: <tool>

## Coverage targets
<coverage table from Step 5>

## Scenario-to-layer mapping
<table from Step 3>

## What is explicitly not tested
<list from Step 6>

## Test data strategy
<decisions from Step 7>

## CI split
<pipeline from Step 8>

## Latest file
This document supersedes: <previous TESTPLAN-*.md, if one exists>
```

## Step 10 — Handoff

Tell the user:
- Total scenarios mapped across layers (X unit, Y integration, Z E2E)
- The highest-risk path with the most critical test coverage requirement
- Any gaps — scenarios that have no test layer assignment yet
- The output filename
- Suggest `/perform-testing` to implement the tests
- Suggest `/perform-implement` to build the feature alongside the tests