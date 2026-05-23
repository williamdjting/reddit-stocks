---
name: perform-codereview
version: 0.1.0
description: |
  Review code changes for bugs, correctness, security issues, and completeness.
  Reads the diff against the base branch, categorizes findings by severity,
  auto-fixes safe issues, and flags decisions that need the author's input.
  Use when asked to "review my code", "code review", "review this PR",
  or "check my changes".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - review my code
  - code review
  - review this pr
  - check my changes
  - review this diff
---

# /perform-codereview — Code Review

Find the bugs that pass CI but blow up in production. Auto-fix the safe ones.
Flag decisions that need the author.

## Step 1 — Get the diff

```bash
git diff $(git merge-base HEAD main)..HEAD --stat
```

If not on a feature branch, ask the user which files or commits to review.

## Step 2 — Read the changed files

For every file in the diff, read the full file — not just the changed lines.
Context matters. A one-line change can break an invariant established 200 lines away.

```bash
git diff $(git merge-base HEAD main)..HEAD
```

## Step 3 — Check against this list

Work through every category. Do not skip even if a category seems unlikely.

**Correctness**
- [ ] Logic errors: off-by-one, wrong operator, incorrect condition
- [ ] Null / undefined not handled where possible
- [ ] Race conditions or shared state mutated from multiple paths
- [ ] Return values ignored where failure matters
- [ ] Async errors swallowed silently

**Security**
- [ ] User input used in SQL, shell commands, file paths, or HTML without sanitization
- [ ] Secrets hardcoded or logged
- [ ] Auth checks missing on new endpoints or actions
- [ ] Overly permissive CORS, CSP, or file permissions
- [ ] Dependency added without checking for known CVEs

**Completeness**
- [ ] Error paths handled (not just the happy path)
- [ ] Edge cases: empty list, zero, null input, very large input
- [ ] New code has corresponding tests
- [ ] New public API has documentation or clear naming
- [ ] Old code that this change makes dead is removed

**Performance**
- [ ] N+1 query patterns introduced
- [ ] Unnecessary work in a hot loop
- [ ] Large allocations or copies that could be avoided
- [ ] Missing index on a new query pattern

**Maintainability**
- [ ] Function or variable names accurately describe what they do
- [ ] Complex logic is explained with a comment (the WHY, not the WHAT)
- [ ] No copy-paste duplication that should be a shared function
- [ ] No commented-out code left behind

## Step 4 — Categorize findings

For each finding, assign a severity:

- **[BLOCK]** — Will cause data loss, security breach, or crash in production. Must fix before merge.
- **[WARN]** — Likely to cause bugs under real conditions. Should fix.
- **[NOTE]** — Style, naming, or minor improvement. Fix or defer — author's call.

## Step 5 — Auto-fix safe issues

For [NOTE]-level issues and clear [WARN] issues where the fix is unambiguous
(rename, remove dead code, add a null check), apply the fix directly using Edit.

For [BLOCK] issues or anything requiring a design decision, do NOT auto-fix.
Present the finding and ask the author how to proceed.

## Step 6 — Report findings

Present a summary:

```
## Code Review Summary

**Branch:** <branch name>
**Files changed:** X
**Findings:** Y total (A block, B warn, C note)

### [BLOCK] <Title>
File: <path>:<line>
Issue: <what is wrong>
Impact: <what breaks in production>
Fix: <what to do>

### [WARN] <Title>
...

### [NOTE] <Title>
...

### Auto-fixed
- <description of what was fixed automatically>

### Approved
The following areas were reviewed and look correct:
- <area>
```

## Step 7 — Handoff

If all [BLOCK] findings are resolved, tell the user the diff is ready for merge.
Suggest `/review-qa` if the changes affect user-facing behavior.
Suggest `/perform-testing` if test coverage is thin on the changed code.