---
name: perform-debug
version: 0.1.0
description: |
  Systematically investigate and fix a bug or unexpected behavior.
  Reproduces the issue, traces the root cause, applies the minimal fix,
  and adds a regression test so it cannot silently reappear. Use when
  asked to "debug this", "fix this bug", "something is broken",
  "why is this failing", or "investigate this error".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - debug this
  - fix this bug
  - something is broken
  - why is this failing
  - investigate this error
  - find the bug
  - this isn't working
  - track down this issue
---

# /perform-debug — Debug and Fix

Reproduce, trace, fix, and prevent. In that order.

## Step 1 — Capture the full bug report

Before touching code, establish:

- **What is the observed behavior?** (exact error message, wrong output, crash)
- **What is the expected behavior?**
- **How do you reproduce it?** (steps, inputs, environment)
- **When did it start?** (always broken, regression from a recent change)
- **Where does it happen?** (dev, staging, prod, specific browser/OS)

If any of these are missing, ask. You cannot fix what you cannot reproduce.

## Step 2 — Reproduce the bug

Write the smallest possible reproduction before investigating:

```bash
# Run the failing test, script, or command that demonstrates the bug
```

If you cannot reproduce it, stop and report that. An unreproducible bug
cannot be safely fixed — you will be guessing.

## Step 3 — Narrow the scope

Identify the boundary of the problem. Work inward from the symptom:

1. Check the error stack trace — what is the deepest frame in your code?
2. Read that file. Understand what it is supposed to do.
3. Add temporary logging or use a debugger to observe actual vs expected values.

```bash
# Check recent changes that might have introduced the regression
git log --oneline -20
git diff HEAD~5..HEAD -- <suspected file>
```

Do not read every file in the project. Follow the stack trace.

## Step 4 — Form a hypothesis

Before making any change, write down:
- What you think is wrong and why
- What the fix should be
- What side effects the fix might have

A fix without a hypothesis is a guess. Guesses break other things.

## Step 5 — Verify the hypothesis

Prove the hypothesis before fixing:
- Add an assertion or log at the suspected point
- Run the reproduction case
- Confirm that the actual value matches your hypothesis about what's wrong

If the actual value does not match your hypothesis, go back to Step 3.

## Step 6 — Apply the minimal fix

Fix the root cause, not the symptom. Ask:
- Am I fixing the actual bug or hiding it?
- Is this the simplest change that makes the behavior correct?
- Am I introducing new assumptions that could break something else?

Make the change. Run the reproduction case — confirm it passes.
Run the full test suite — confirm nothing else regressed.

```bash
# Run the full test suite
```

## Step 7 — Write a regression test

If no test caught this bug, write one now:

```
Test name: <describes the exact scenario that was broken>
Input: <the specific input or state that triggered the bug>
Assert: <the correct behavior the code should now exhibit>
```

This test must fail on the unfixed code and pass on the fixed code.
A bug that has no test will be reintroduced.

## Step 8 — Handoff

Tell the user:
- Root cause (one sentence — what was actually wrong)
- The fix applied (what changed and why)
- The regression test added
- Any related code that might have the same bug elsewhere
- Suggest `/perform-codereview` if this goes into a PR