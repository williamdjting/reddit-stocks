---
name: review-release
version: 0.1.0
description: |
  Release readiness review. Checks that a feature or product is safe to ship:
  testing complete, rollback plan defined, monitoring in place, stakeholders
  notified, and docs updated. Use when asked to "release review", "is this
  ready to ship", "pre-launch checklist", or "review the release".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - release review
  - is this ready to ship
  - pre-launch checklist
  - review the release
  - launch review
  - ship readiness
---

# /review-release — Release Readiness Review

Confirm the product or feature is safe to put in front of users. Find the gaps
in testing, rollback, monitoring, and communication before they become incidents.

## Step 1 — Read everything

Find the most recent version of each context file:

```bash
ls -t PRD-*.md DESIGN-*.md ENG_REVIEW-*.md TECHSTACK-*.md RELEASE_REVIEW-*.md 2>/dev/null | head -10
```

Open the most recent of each type. Also check `CHANGELOG.md`, `README.md`,
`CLAUDE.md`, and any deployment notes.

Read them all. Understand what is supposed to ship and what the intended user
experience is — not just the implementation details.

## Step 2 — Map the release scope

Produce a short summary of what is actually changing:

```
Release: <name or version>
Date:    <target>

What ships:
- <feature or change 1>
- <feature or change 2>

What does NOT ship (explicitly deferred):
- <item>

Who is affected:
- <user segment or system>
```

If the scope is unclear, ask the author before proceeding. A release without
a defined scope cannot be reviewed for readiness.

## Step 3 — Check the state of testing

For each item in scope:

- What tests exist and do they pass?
- Are there known failures or flaky tests that were skipped?
- Was the feature tested end-to-end in a staging or production-like environment?
- Were edge cases tested, not just the happy path?

Flag any gap between "tests written" and "tests passing in an environment that
resembles production."

## Step 4 — Work through the checklist

**Completeness**
- [ ] Is every feature in scope implemented and functional?
- [ ] Are there any half-finished items that could confuse or break the user experience?
- [ ] Are migration steps for existing data complete and tested?
- [ ] Are all dependent services or APIs updated and compatible?

**Testing**
- [ ] Do unit and integration tests pass?
- [ ] Was manual end-to-end testing completed in staging?
- [ ] Were edge cases (empty state, errors, concurrent users) verified?
- [ ] Is there a regression test covering any bug that was fixed?

**Rollback**
- [ ] Is there a documented rollback procedure?
- [ ] Has the rollback procedure been tested or at minimum walked through?
- [ ] Can the rollback be executed without downtime or data loss?
- [ ] Is the rollback criteria defined (what observable condition triggers it)?

**Monitoring and alerting**
- [ ] Are error rates and latency being tracked for the new surface?
- [ ] Will on-call be alerted if something breaks within the first hour?
- [ ] Is there a way to distinguish errors from this release vs pre-existing errors?
- [ ] Are dashboards or logs available to verify the feature is working in production?

**Security**
- [ ] Are new inputs validated and sanitized?
- [ ] Are authorization checks in place for any new actions or routes?
- [ ] Is sensitive data handled correctly (not logged, not exposed in responses)?
- [ ] Were any dependencies updated that could introduce vulnerabilities?

**Documentation and communication**
- [ ] Is the changelog updated with user-facing language?
- [ ] Are internal stakeholders (support, sales, other eng teams) notified?
- [ ] Is user-facing documentation (help docs, onboarding, tooltips) updated?
- [ ] Is the release announcement ready if this is a public launch?

## Step 5 — Define the go/no-go criteria

State explicitly what must be true before the release proceeds:

```
## Go/No-Go Criteria: <Release Name>

### Must be true before deploy
- <criterion>: <how to verify>

### Must be true within 1 hour of deploy
- <criterion>: <how to verify>

### Rollback is triggered if
- <observable condition>
```

## Step 6 — State the verdict

- **Go** — release is safe to ship, all criteria met
- **Go with conditions** — list specific items that must be resolved or accepted as known risk before shipping
- **No-go** — identify the blocking gap that must be closed first

## Step 7 — Write the review

Check for an existing release review:

```bash
ls -t RELEASE_REVIEW-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`RELEASE_REVIEW-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`RELEASE_REVIEW-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# Release Review: <Name / Version>

**Generated:** <YYYY-MM-DD HH:MM>
**Target release date:** <date>
**Verdict:** Go | Go with conditions | No-go

## Release Scope
<Scope summary from Step 2>

## Testing Status
<Summary of what was tested, what passed, any gaps>

## Findings
<One section per finding from the checklist. Only include actual findings.>

## Go/No-Go Criteria
<Criteria from Step 5>

## Conditions (if verdict is Go with conditions)
<Numbered, specific, actionable. Each item must be owned by someone.>

## Rollback Plan
<Who triggers it, how, and under what conditions>

## Open Risks
<Known issues accepted for this release, with mitigation or monitoring in place.>

## Latest file
This document supersedes: <previous RELEASE_REVIEW-*.md filename, if one exists>
```

## Step 8 — Handoff

Tell the user the verdict and the single most important item to resolve.
If Go: confirm the rollback plan is understood by the person deploying.
If No-go: identify the one thing that must be fixed before re-review.