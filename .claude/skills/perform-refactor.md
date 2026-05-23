---
name: perform-refactor
version: 0.1.0
description: |
  Refactor code for clarity, maintainability, or performance without changing
  observable behavior. Identifies the highest-value refactoring opportunities,
  gets author approval on scope, then applies changes with tests passing at
  each step. Use when asked to "refactor this", "clean up this code",
  "improve this", or "make this more maintainable".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - refactor this
  - clean up this code
  - improve this
  - make this more maintainable
  - simplify this
---

# /perform-refactor — Refactor

Improve code structure without changing behavior. The rule: every intermediate
commit must leave tests passing. If you cannot run tests, leave the code
in a working state at every step.

## Step 1 — Understand the target

Ask the user what to refactor if not specified:
- Which file, function, or module?
- What is the pain? (hard to read, duplicated, slow, hard to test?)
- Are there any areas that are off-limits?

Read the target code fully before suggesting anything.

## Step 2 — Run the tests (baseline)

```bash
# Detect and run the existing test suite
# Check CLAUDE.md or package.json for the test command
```

Record which tests pass. Every refactor step must keep this green.
If there are no tests, note it — refactoring without tests is higher risk.

## Step 3 — Identify refactoring opportunities

Evaluate the code against these patterns. Note findings but do NOT apply yet.

**Naming**
- Variables, functions, and types that don't describe what they do
- Abbreviations that require context to decode
- Boolean parameters that need a named constant

**Structure**
- Functions longer than ~40 lines doing more than one thing
- Deeply nested conditionals (more than 3 levels) that can be flattened
- Duplicated logic that should be extracted to a shared function
- Dead code (unreachable, unused exports, stale comments)

**Dependencies**
- Tightly coupled modules that make unit testing hard
- Global state that could be passed as a parameter instead
- Functions that do both data fetching AND data transformation

**Performance** (only if the user asked for it or the issue is clear)
- Repeated work inside a loop that can be moved outside
- Unnecessary re-renders or re-computations
- Large allocations that can be reused

## Step 4 — Propose scope and get approval

Present findings as a prioritized list:

```
Proposed refactoring for <target>:

1. [HIGH VALUE] Extract <X> into a separate function — currently 80 lines doing 3 things
2. [MEDIUM] Rename <y> → <betterName> across 4 callsites
3. [LOW] Remove dead function <z> — not called anywhere

Which of these should I apply?
```

Use AskUserQuestion if the scope is large or the choices are non-obvious.
Do not proceed without the author's OK on scope.

## Step 5 — Apply changes incrementally

Work through approved items one at a time. After each change:

1. Apply the edit
2. Run tests (if available): confirm still passing
3. State what was changed and why

Never combine unrelated refactors in one step. If something breaks, stop
and report before continuing.

## Step 6 — Verify behavior is unchanged

```bash
# Run the full test suite one final time
```

If tests pass: confirm the refactor is complete.
If tests fail: identify which change caused the failure and revert or fix it.

Report:
- What was changed
- What was intentionally left alone (and why)
- Any follow-on refactors worth doing in a future pass
- Test coverage gaps discovered during refactoring

## Step 7 — Handoff

If behavior-affecting changes were necessary (fixes found during refactor),
flag them separately — they belong in their own commit, not the refactor.
Suggest `/perform-codereview` if the changes are going into a PR.