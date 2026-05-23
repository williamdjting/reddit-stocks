---
name: perform-implement
version: 0.2.0
description: |
  Implement a feature end-to-end from a spec, PRD, or plain description.
  Reads existing context documents, breaks the work into discrete feature tasks,
  builds each feature incrementally with tests passing at every step, then stops
  after each feature for a mandatory quality gate (codereview → debug → refactor →
  testing) before continuing. After all features are complete, runs the full review
  pipeline (review-eng → review-ceo → review-qa → review-release). Use when asked
  to "build this feature", "implement this", "code this up", or "make this work".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - build this feature
  - implement this
  - code this up
  - make this work
  - implement the feature
  - build it
  - write the code
---

# /perform-implement — Implement a Feature

Turn a spec into working, tested code — one feature at a time, with a quality
gate after each one. No feature moves forward until the previous one is reviewed,
debugged, refactored, and tested.

## Step 1 — Read all available context

Check the current directory for:
- `PRD.md` — requirements and acceptance criteria
- `DESIGN.md` — user flows and component breakdown
- `TECHSTACK.md` — stack decisions and architecture
- `DATAMODEL.md` — schema and entity relationships
- `API.md` — API contracts
- `ENG_REVIEW.md` — technical constraints and test plan
- `CLAUDE.md` — project-specific commands and conventions

Pull in everything available before writing a line.

## Step 2 — Clarify before starting

If any of these are unknown, ask before starting:

- What is the entry point? (new file, new route, new component?)
- Are there existing files this feature hooks into?
- What does "done" look like — is there a test command or acceptance test?
- Any constraints not in the spec? (auth required, rate limits, feature flags?)

Do not guess on ambiguous scope. One clarifying question now saves two
hours of rework later.

## Step 3 — Break the work into features

Decompose the work into discrete, independently shippable features.
Each feature maps to a user-facing capability, not a layer.
Write them out before touching any code:

```
Feature 1: <user-facing capability — e.g., "user registration and login">
Feature 2: <user-facing capability — e.g., "create and list items">
Feature 3: <user-facing capability — e.g., "notifications and emails">
```

For each feature, identify the internal tasks (data layer, logic, API, UI,
tests). Keep these internal — they drive your implementation order, but the
quality gate runs at the feature level, not the task level.

## Step 4 — Check for existing code to reuse

Before writing anything, search for:

```bash
# Find related files
grep -r "<feature keyword>" . --include="*.ts" --include="*.tsx" \
  --include="*.js" --include="*.py" -l | grep -v node_modules | head -20
```

Reuse existing utilities, patterns, and types. Match the conventions in
the surrounding code — naming, error handling, file structure.

## Step 5 — Implement one feature at a time

For each feature, follow this loop exactly. Do not skip the quality gate.
Do not start the next feature until the user confirms the current one passed.

---

### 5a — Build the feature

For each internal task within the feature:

1. Write the implementation
2. Write or update tests for that layer
3. Run the test suite — fix before moving on

```bash
# Run tests (use the command from CLAUDE.md or package.json)
```

Never move to the next internal task with a failing test. A passing suite
at every step means any regression is immediately traceable.

### 5b — Wire the feature end-to-end

Once all internal tasks for this feature are complete:
- Connect the layers (routes, exports, providers, wiring)
- Run the full test suite
- Smoke test the happy path if a dev server is available

```bash
# Start dev server if applicable
```

### 5c — Verify against acceptance criteria

Return to the PRD. For each acceptance criterion that belongs to this feature:
- Mark it met or not met
- If not met, implement the gap before proceeding to the quality gate

Do not proceed to the quality gate until all acceptance criteria for this
feature are met.

### 5d — QUALITY GATE (mandatory — do not skip)

Stop here. Do not start the next feature until this gate passes.

Run these four steps in order:

**1. Code review**
Invoke `/perform-codereview` against the code written for this feature.
Record any issues found in `CODE_REVIEW.md` (or append if it already exists).

**2. Debug (if issues found)**
If `/perform-codereview` found bugs or logic errors, invoke `/perform-debug`
to resolve them before continuing. Re-run the test suite after fixes.

**3. Refactor**
Invoke `/perform-refactor` against the feature's code to apply improvements
from the code review. This includes naming, structure, duplication, and
test coverage gaps. Re-run the test suite after refactoring.

**4. Testing**
Invoke `/perform-testing` to verify test coverage for this feature is
complete. Confirm that every acceptance criterion has at least one automated
test.

### 5e — Ask before continuing

After the quality gate passes, present a summary to the user:

```
Feature [N] complete: <feature name>
Quality gate: ✓ Code review | ✓ Debug | ✓ Refactor | ✓ Testing

Files changed: <list>
Acceptance criteria met: <X of Y>
Tests added: <N>

Ready for Feature [N+1]: <next feature name>
Continue? (Y to proceed, N to stop here)
```

Wait for confirmation. If the user says N, stop and hand off.
If the user says Y, loop back to Step 5a for the next feature.

---

## Step 6 — Full review pipeline (after all features complete)

Once every feature has passed its quality gate and the user confirms all
features are done, run the end-to-end review pipeline in order:

**1. Engineering review** — invoke `/review-eng`
Technical architecture, scalability, security, and code quality assessment.
This produces `ENG_REVIEW.md`. If the verdict is "Not ready", address
blockers before continuing.

**2. CEO review** — invoke `/review-ceo`
Product strategy, user value, and business alignment. This produces
`CEO_REVIEW.md`. If the verdict is "Not ready", surface the concerns to
the user before continuing.

**3. QA review** — invoke `/review-qa`
Quality, edge cases, accessibility, and release readiness. This produces
`QA_REVIEW.md`. If the verdict is "Not ready", address blockers before
continuing.

**4. Release review** — invoke `/review-release`
Final gate: changelog, versioning, deployment checklist, and rollback plan.
This produces `RELEASE_REVIEW.md`.

## Step 7 — Final handoff

After the full review pipeline, tell the user:
- All features built and which acceptance criteria are met
- Any criteria not implemented and why
- Any known edge cases left for follow-on work
- The status of each review (verdict from ENG, CEO, QA, Release)
- Next action: if all reviews pass, the app is ready to ship