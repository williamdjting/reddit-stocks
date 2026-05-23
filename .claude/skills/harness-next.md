---
name: harness-next
version: 0.2.0
description: |
  Orchestrates the jwnlabs development harness against an application directory.
  Scans /app for completed harness artifacts, checks what has been done, and
  performs the next step or tells you exactly what to do. Use when asked to
  "what's next", "next step", "harness status", "continue the harness",
  "where am I in the process", or "check my progress".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - what's next
  - next step
  - harness status
  - continue the harness
  - where am I in the process
  - check my progress
  - run the harness
---

# /harness-next — Harness Progress Check + Next Step

Scan the application directory against the jwnlabs harness pipeline, determine
what has been completed, and drive the next step.

## The harness pipeline

The harness has 16 stages in order. Each stage produces one or more artifact files.
All artifact files live in the app directory.

HTML companion files (`.html`) are generated alongside their parent `.md` files.
`SYSTEM_DIAGRAM.html` is generated automatically by whichever of stages 5, 8, or 9
runs last — it requires all three of those artifacts to exist first.

| # | Stage | Skill | Artifact(s) | Requires |
|---|-------|-------|-------------|----------|
| 1 | Opportunity analysis | `/blueprint-analyzeopportunity` | `OPPORTUNITY.md` | — |
| 2 | Business case | `/blueprint-businesscase` | `BUSINESS_CASE.md` | OPPORTUNITY.md |
| 3 | Product requirements | `/blueprint-prd` | `PRD.md` | BUSINESS_CASE.md |
| 4 | Design spec | `/blueprint-design` | `DESIGN.md` | PRD.md |
| 5 | Architecture | `/blueprint-architecture` | `ARCHITECTURE.md` · `SYSTEM_DIAGRAM.html`* | PRD.md |
| 6 | Data model | `/blueprint-datamodel` | `DATAMODEL.md` · `DATAMODEL.html` | PRD.md |
| 7 | API contract | `/blueprint-api` | `API.md` · `API.html` | DATAMODEL.md |
| 8 | Tech stack | `/blueprint-techstack` | `TECHSTACK.md` · `SYSTEM_DIAGRAM.html`* | PRD.md |
| 9 | Scenarios | `/blueprint-scenarios` | `SCENARIOS.md` · `SYSTEM_DIAGRAM.html`* | PRD.md + DESIGN.md |
| 10 | Planning — CEO review | `/review-ceo` | `CEO_REVIEW.md` | PRD.md + DESIGN.md + TECHSTACK.md |
| 11 | Planning — Eng review | `/review-eng` | `ENG_REVIEW.md` | PRD.md + ARCHITECTURE.md + TECHSTACK.md |
| 12 | Code exists | — | `src/` or `app/` or any source files | ENG_REVIEW.md |
| 13 | Implementation + per-feature quality gate | `/perform-implement` | `CODE_REVIEW.md` · `TESTS.md` · `REFACTOR.md` | Code exists; loops per feature: codereview → debug → refactor → testing |
| 14 | Post-impl Eng review | `/review-eng` (via perform-implement) | `ENG_REVIEW.md` (updated) | CODE_REVIEW.md + TESTS.md |
| 15 | Post-impl QA review | `/review-qa` (via perform-implement) | `QA_REVIEW.md` | CODE_REVIEW.md + TESTS.md |
| 16 | Release review | `/review-release` (via perform-implement) | `RELEASE_REVIEW.md` | QA_REVIEW.md |

*`SYSTEM_DIAGRAM.html` is generated automatically once stages 5, 8, and 9 are all complete.
It does not need to be driven manually — whichever skill runs last among those three triggers it.

**Note on stages 13–16:** `/perform-implement` drives all of these internally:
- Stage 13: It builds features one at a time. After each feature it runs `/perform-codereview`,
  `/perform-debug` (if needed), `/perform-refactor`, and `/perform-testing` before asking
  permission to continue to the next feature.
- Stages 14–16: After all features pass their per-feature quality gate, it runs the final
  review pipeline: `/review-eng` → `/review-ceo` → `/review-qa` → `/review-release`.

`harness-next` tracks these stages by checking for their artifact files. The artifacts are
produced by `/perform-implement` but the check logic is the same.

## Step 1 — Locate the app directory

Check the following paths in order:
1. `./app` — app is a subfolder of the current working directory
2. `../app` — app is a sibling directory
3. The path stored in `.harness-app-path` if it exists in the current directory

If none of those exist, use AskUserQuestion to ask:
> "Where is your application directory? Provide the path relative to here or an absolute path."

Store the confirmed path in `.harness-app-path` so future runs don't re-ask.

Once located, set APP_DIR to the confirmed path and continue.

## Step 2 — Scan for completed artifacts

Check APP_DIR for each artifact in the pipeline table. For each one found:
- Note that it exists
- Read its first 10 lines to confirm it is a real document (not an empty file or stub)
- Check if it has a `**Status:** Draft` vs `**Status:** Complete` header field — if present, use that
- Otherwise, treat a file with >50 lines as "complete" and <50 lines as "stub"

For HTML companion files (`DATAMODEL.html`, `API.html`, `SYSTEM_DIAGRAM.html`):
- Note presence or absence alongside the parent `.md` file
- If the `.md` exists but the `.html` does not, flag it as incomplete and recommend
  re-running the skill to regenerate it

Build a status table:

```
Stage                          | Artifact(s)                          | Status
-------------------------------|--------------------------------------|--------
Opportunity analysis           | OPPORTUNITY.md                       | ✓ Complete
Business case                  | BUSINESS_CASE.md                     | ✓ Complete
Product requirements           | PRD.md                               | ✓ Complete
Design spec                    | DESIGN.md                            | ✗ Missing
Architecture                   | ARCHITECTURE.md · SYSTEM_DIAGRAM.html| ✗ Missing
Data model                     | DATAMODEL.md · DATAMODEL.html        | ✗ Missing
API contract                   | API.md · API.html                    | ✗ Missing
Tech stack                     | TECHSTACK.md · SYSTEM_DIAGRAM.html   | ✗ Missing
Scenarios                      | SCENARIOS.md · SYSTEM_DIAGRAM.html   | ✗ Missing
Planning — CEO review          | CEO_REVIEW.md                        | ✗ Missing
Planning — Eng review          | ENG_REVIEW.md                        | ✗ Missing
Code exists                    | src/ or source files                 | ✗ Missing
Implementation + quality gates | CODE_REVIEW.md · TESTS.md · REFACTOR | ✗ Missing
Post-impl Eng review           | ENG_REVIEW.md (updated)              | ✗ Missing
Post-impl QA review            | QA_REVIEW.md                         | ✗ Missing
Release review                 | RELEASE_REVIEW.md                    | ✗ Missing
```

Print this table to the user before proceeding.

## Step 3 — Identify the current stage

Walk the pipeline in order. The current stage is the **first stage whose artifact
is missing or is a stub**. All prior stages must be complete for a stage to be
considered truly done — if a prerequisite is missing, flag it.

**Special handling for stage 12 (code exists):** check if APP_DIR contains any of:
- A `src/` directory with files
- An `app/` subdirectory with files
- Any `.ts`, `.tsx`, `.js`, `.py`, `.go`, `.rb`, `.rs`, `.java` files at the root
- A `package.json`, `pyproject.toml`, `Cargo.toml`, or similar build manifest

If any of the above are found, treat stage 12 as complete.

**Special handling for stage 13 (implementation + quality gate):** This stage is
complete when `CODE_REVIEW.md`, `TESTS.md`, and `REFACTOR.md` all exist and are
non-stub. These are produced incrementally by `/perform-implement` as each feature
passes its quality gate.

**Special handling for stages 14–16:** These are complete when their artifacts exist
(`ENG_REVIEW.md` updated post-code, `QA_REVIEW.md`, `RELEASE_REVIEW.md`). Check
the `**Generated:**` date on `ENG_REVIEW.md` — if it predates any code files in
`src/`, the planning-phase review exists but the post-implementation review has not
yet run. Flag this and recommend re-running `/perform-implement` to complete the
final review pipeline.

## Step 4 — Check for blockers

Before proceeding to the next step, check for blockers:

1. **Failed planning reviews** — if `CEO_REVIEW.md` or the planning-phase `ENG_REVIEW.md`
   contains `**Verdict:** Not ready`, do not skip past it. Report the finding and ask:
   > "The [review type] verdict is 'Not ready'. Do you want to address the blockers
   > and re-run the review, or proceed anyway?"

2. **Failed final reviews** — if `QA_REVIEW.md` or `RELEASE_REVIEW.md` contains
   `**Verdict:** No-go` or `Not ready`, surface the blockers and recommend addressing
   them before considering the harness complete.

3. **Missing prerequisites** — if the current stage requires an artifact that is
   missing, flag the gap and recommend completing prerequisites in order.

4. **Stub artifacts** — if an artifact exists but is a stub (<50 lines), treat it
   as incomplete and recommend completing it before moving to the next stage.

5. **Missing HTML companions** — if `API.md` exists but `API.html` does not, or
   `DATAMODEL.md` exists but `DATAMODEL.html` does not, flag it and suggest re-running
   the skill to generate the missing visualization.

6. **Missing system diagram** — if stages 5, 8, and 9 are all complete but
   `SYSTEM_DIAGRAM.html` does not exist, flag it and suggest re-running any of
   `/blueprint-architecture`, `/blueprint-techstack`, or `/blueprint-scenarios` to
   trigger generation.

## Step 5 — Perform or prompt the next step

### If the harness is complete (all 16 stages done):

Tell the user:
> "All harness stages are complete. RELEASE_REVIEW.md exists and covers the current
> codebase. If the release verdict is Go, you are ready to ship."

### If the next step is stage 12 (implement code):

Tell the user:
> "All planning documents are complete and both planning reviews passed.
> The next step is implementation using `/perform-implement`.
>
> `/perform-implement` builds features one at a time. After each feature it runs a
> quality gate (code review → debug → refactor → testing) and waits for your
> confirmation before starting the next feature. After all features pass, it runs
> the final review pipeline (eng review → CEO review → QA review → release review).
>
> Start building in [APP_DIR]/src/. Run `/perform-implement` now."

### If the next step is a blueprint or planning review skill (stages 1–11):

Ask the user:
> "The next step is [stage name] using `/[skill name]`.
> Options:
> A) Run it now — I'll invoke the skill and work through it with you
> B) Tell me what to do — I'll describe what to prepare and you'll run it
> C) Skip this stage — I'll note it as intentionally skipped and move to the next"

- If A: invoke the skill from the harness and tell it to save its output to APP_DIR
- If B: explain the inputs the skill will need, where to run it, and what artifact it will produce
- If C: write a one-line `<ARTIFACT_NAME>.skip` file in APP_DIR noting the skip, and continue to the next stage

### If the next step is stage 13 (implementation in progress):

Check whether any per-feature quality gate artifacts already exist:

```bash
ls CODE_REVIEW.md TESTS.md REFACTOR.md 2>/dev/null
```

If partial: tell the user which features have passed the quality gate and which have not.
Recommend running `/perform-implement` to continue from where it left off.

If none: tell the user to run `/perform-implement` to start the implementation phase.

### If the next step is stages 14–16 (final reviews incomplete):

Tell the user:
> "Implementation is complete but the final review pipeline has not finished.
> Run `/perform-implement` — it will detect that all features are built and
> proceed directly to the final review pipeline:
> review-eng → review-ceo → review-qa → review-release."

## Step 6 — After completing a step

Once the invoked skill writes its artifact to APP_DIR:
- Re-run the status scan (Step 2)
- Print the updated table
- State the next stage clearly
- Ask if the user wants to continue immediately or stop here

## Notes on running skills against APP_DIR

When invoking a blueprint or review skill, tell it:
> "Save all output files to [APP_DIR]. Read context from any existing documents there."

The skills read from and write to the current directory by default — either `cd` to
APP_DIR first or pass it explicitly in the prompt when invoking.