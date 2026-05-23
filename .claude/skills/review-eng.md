---
name: review-eng
version: 0.1.0
description: |
  Engineering manager review of a plan or architecture. Locks in data flow,
  identifies edge cases, defines the test plan, surfaces hidden assumptions,
  and produces ASCII diagrams. Use when asked to "engineering review",
  "review the architecture", "eng review", or "is this technically sound".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - engineering review
  - review the architecture
  - eng review
  - is this technically sound
  - technical review
  - architecture review
---

# /review-eng — Engineering Review

Lock in the architecture before implementation starts. Find the edge cases,
failure modes, and missing tests that will hurt later if not caught now.

## Step 1 — Read everything

Find the most recent version of each context file:

```bash
ls -t PRD-*.md DESIGN-*.md TECHSTACK-*.md ARCHITECTURE-*.md OPPORTUNITY-*.md 2>/dev/null | head -10
```

Open the most recent of each type. Also check existing code and `CLAUDE.md`.

Read them all. The goal is to understand what is being built, not just
what the author intended.

## Step 2 — Draw the data flow

Produce an ASCII diagram of how data moves through the system:
- Where it enters (user input, API call, scheduled job, event)
- How it is validated and transformed
- Where it is stored
- Where it exits (response, side effect, downstream system)

```
[Input source]
     │
     ▼
[Validation layer]
     │ valid          │ invalid
     ▼                ▼
[Business logic]   [Error response]
     │
     ▼
[Persistence / Output]
```

If the data flow is unclear from the documents, ask the author to clarify
before proceeding. An unclear data flow means the design is not ready.

## Step 3 — Check the state machine

For any feature with meaningful state (e.g., order: pending → paid → shipped):

- List every state
- List every valid transition
- List every invalid transition (and what happens when someone tries one)
- Identify which state is the source of truth and where it lives

A missing state or invalid transition is a production bug waiting to happen.

## Step 4 — Work through the checklist

**Correctness**
- [ ] What happens with empty or null input at every entry point?
- [ ] What happens at maximum scale (10x expected load)?
- [ ] Are there race conditions if two users trigger the same action simultaneously?
- [ ] Is the error handling exhaustive or just the happy path?

**Security**
- [ ] Are all user-supplied inputs validated before use?
- [ ] Are authorization checks on every action, not just the route?
- [ ] Is sensitive data (PII, credentials, tokens) stored and transmitted correctly?
- [ ] What can an authenticated-but-unauthorized user access?

**Reliability**
- [ ] What happens when the database is slow or unavailable?
- [ ] What happens when a downstream API times out?
- [ ] Is there retry logic where needed? Is it idempotent?
- [ ] Are background jobs recoverable if interrupted?

**Observability**
- [ ] What gets logged when something goes wrong?
- [ ] Is there a way to know in production if this feature is broken?
- [ ] Are errors distinguishable (which error, where, for whom)?

**Testability**
- [ ] Can the core logic be tested without a real database or network?
- [ ] Are there integration tests for the critical paths?
- [ ] Is the test plan defined before implementation starts?

**Completeness**
- [ ] Are there migration steps for existing data?
- [ ] Is rollback possible if the deploy goes wrong?
- [ ] Are dependent teams or services notified of the change?

## Step 5 — Define the test plan

Write the minimum test plan that must exist before this ships:

```
## Test Plan: <Feature Name>

### Unit tests (must pass before PR)
- <test case>: <what it verifies>

### Integration tests (must pass before merge)
- <test case>: <what it verifies>

### Manual verification (must be done before deploy)
- <step>: <what to check>

### Rollback criteria
Ship is rolled back if: <specific observable condition>
```

## Step 6 — State the verdict

- **Ready for implementation** — architecture is sound, test plan is defined
- **Ready with modifications** — list specific changes required before coding starts
- **Not ready** — identify the fundamental gap to resolve first

## Step 7 — Write the review

Check for an existing engineering review:

```bash
ls -t ENG_REVIEW-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`ENG_REVIEW-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`ENG_REVIEW-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# Engineering Review: <Plan / Feature Name>

**Generated:** <YYYY-MM-DD HH:MM>
**Verdict:** Ready | Ready with modifications | Not ready

## Data Flow Diagram
<ASCII diagram from Step 2>

## State Machine (if applicable)
<State/transition table from Step 3>

## Findings
<One section per finding from the checklist. Only include actual findings.>

## Test Plan
<Test plan from Step 5>

## Required Changes (if verdict is Ready with modifications)
<Numbered, specific, actionable.>

## Open Questions
<Architecture decisions not yet resolved that will block implementation.>

## Latest file
This document supersedes: <previous ENG_REVIEW-*.md filename, if one exists>
```

## Step 8 — Handoff

Tell the user the verdict and the most critical open question.
If Ready: suggest `/blueprint-scenarios` if test cases need to be written out.
If Not ready: identify the one document that needs to be updated first.