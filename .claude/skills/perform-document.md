---
name: perform-document
version: 0.1.0
description: |
  Write developer and user-facing documentation for a project or feature.
  Covers README, API reference, setup guides, onboarding docs, and
  inline code comments. Reads the actual code to produce accurate docs —
  never fabricates. Use when asked to "write docs", "document this",
  "write a README", "API documentation", or "onboarding guide".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - write docs
  - document this
  - write a readme
  - api documentation
  - onboarding guide
  - write documentation
  - document the api
  - update the readme
---

# /perform-document — Write Documentation

Documentation that is accurate, minimal, and useful to the person who
needs it — not a wall of auto-generated text no one reads.

## Step 1 — Identify the audience and type

Before writing, confirm:

- **Who is the reader?** (new developer joining the team, API consumer,
  end user, future maintainer)
- **What type of doc is needed?**
  - `README.md` — project overview and quick start
  - `API.md` — endpoint reference
  - `SETUP.md` / `CONTRIBUTING.md` — local dev and contributor guide
  - `ARCHITECTURE.md` — system design and decisions
  - Inline code comments — complex logic explanation
  - User-facing help / onboarding flow

Different audiences need radically different docs. Confirm before starting.

## Step 2 — Read the actual code

Never write docs from memory or assumptions.

```bash
# Find entry points, routes, exported functions
grep -r "export " . --include="*.ts" --include="*.js" -l | \
  grep -v node_modules | grep -v dist | head -20

# Find API routes
grep -r "router\.\|app\.get\|app\.post\|@Get\|@Post" . \
  --include="*.ts" --include="*.js" | grep -v node_modules | head -30
```

Read every file that defines the public surface being documented.
Only document what is there — not what you expect to be there.

## Step 3 — Write the README

If writing a README, cover exactly these sections (skip sections that do
not apply — do not add placeholder headings):

```markdown
# <Project Name>

<One sentence: what it does and who it is for.>

## Quick start

\```bash
# Minimum commands to go from zero to running
\```

## What it does
<2–4 sentences. The problem it solves and how.>

## Installation
<Prerequisites, then install steps.>

## Configuration
<Environment variables table: name | required | description | default>

## Usage
<Common usage patterns with real code examples.>

## API reference
<Link to API.md or inline for small projects.>

## Development
<How to run tests. How to run locally. How to contribute.>

## License
```

Short beats comprehensive. A new developer should be productive in under
10 minutes from a good README.

## Step 4 — Write the API reference

For each public endpoint or exported function, document:

```markdown
### POST /users

Create a new user account.

**Request body**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | yes | User email address |
| password | string | yes | Min 8 characters |

**Response 201**
\```json
{ "id": "usr_123", "email": "user@example.com", "createdAt": "2024-01-01T00:00:00Z" }
\```

**Errors**
| Status | Code | Description |
|--------|------|-------------|
| 400 | INVALID_EMAIL | Email format invalid |
| 409 | EMAIL_EXISTS | Email already registered |
```

Every field that is sent or received must be listed. Every error that
can be returned must be listed. Do not document what the code might do —
document what the code actually does.

## Step 5 — Write inline comments

Only add inline comments where the WHY is not obvious from the code:

- A non-obvious algorithm or formula
- A workaround for a specific bug or library limitation
- A constraint that is not visible in the code (rate limit, business rule)
- A subtle invariant that future editors must not break

Do NOT add comments that restate what the code does. If the code is
clear enough to read, the comment adds noise.

```typescript
// BAD: iterate over users and send email
// GOOD: BCC limit on SendGrid is 1000 — batch to avoid 413
```

## Step 6 — Verify accuracy

After writing, spot-check every claim:

```bash
# Verify the install command works
# Verify the quick start steps run without errors
# Verify every code example is syntactically correct
```

Docs that lie are worse than no docs. A developer who follows broken
instructions and hits an error will distrust everything else in the docs.

## Step 7 — Handoff

Tell the user:
- Which doc files were created or updated
- Any sections left as TODOs and why (missing context, need user input)
- Any code that was notably hard to document — it may need refactoring
- Suggest `/perform-codereview` if this is going into a PR