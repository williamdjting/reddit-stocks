---
name: perform-testing
version: 0.1.0
description: |
  Write tests for existing code or new features. Covers unit tests, integration
  tests, and edge cases. Reads the code under test, identifies untested paths,
  and implements tests that will catch real bugs. Use when asked to "write tests",
  "add test coverage", "test this function", or "improve test coverage".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - write tests
  - add test coverage
  - test this function
  - improve test coverage
  - write unit tests
---

# /perform-testing — Write Tests

Write tests that will actually catch bugs — not tests that just hit the
happy path and inflate coverage numbers.

## Step 1 — Understand the testing context

Check `CLAUDE.md`, `package.json`, or project config for:
- The test command (e.g., `bun test`, `npm test`, `pytest`, `go test ./...`)
- The test framework in use
- Any existing test files for the target code

If the test framework is missing, ask the user whether to set one up first
or write tests assuming one will be added.

## Step 2 — Read the code under test

Read the full implementation of every function or module being tested.
Identify:
- The function signature (inputs, outputs, side effects)
- The branches (every `if`, `switch`, early return)
- The failure paths (throws, error returns, null returns)
- External dependencies (DB, API calls, filesystem)

## Step 3 — Check existing tests

```bash
# Find existing test files
find . -name "*.test.*" -o -name "*.spec.*" | grep -v node_modules | head -20
```

Read them. Understand the patterns in use. Match the existing style.

## Step 4 — Map what needs to be tested

Before writing a single line, list the cases:

```
Function: <name>

Happy path:
- [ ] <normal input produces expected output>

Edge cases:
- [ ] empty input
- [ ] null / undefined input
- [ ] input at maximum boundary
- [ ] input at minimum boundary

Failure cases:
- [ ] invalid input throws or returns error
- [ ] external dependency fails — what happens?

Side effects:
- [ ] DB write happens exactly once
- [ ] event is emitted with correct payload
```

## Step 5 — Write the tests

For each case, write a test that:
1. Sets up the exact starting state (no hidden global state)
2. Calls the code with one specific input
3. Asserts exactly what the output or side effect should be
4. Cleans up after itself

Test naming convention: `<what it does> when <condition>`:
- `returns empty array when input is empty`
- `throws ValidationError when email is missing`
- `calls sendEmail once when user is created`

Mock external dependencies at the boundary — do not mock the code under test.

## Step 6 — Run the tests

```bash
# Run the test suite (use the command from CLAUDE.md or package.json)
```

Fix any failures. If a test failure reveals a real bug in the implementation,
stop and flag it — do not write the test around the bug.

## Step 7 — Report coverage

After tests pass, check coverage if available:

```bash
# e.g., bun test --coverage, jest --coverage, go test -cover ./...
```

Report:
- Which branches are now covered
- Which branches are still uncovered and why (if intentional)
- Any bugs found while writing the tests

## Step 8 — Handoff

Tell the user:
- How many tests were added
- Which edge cases are now covered that weren't before
- Any untested paths that would require significant refactoring to test
- Suggest `/perform-codereview` if the tests are going into a PR