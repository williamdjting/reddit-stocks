---
name: blueprint-datamodel
version: 0.1.0
description: |
  Design the database schema and entity relationships for an application.
  Covers entity identification, field types, relationships, indexes, and
  normalization decisions. Produces a DATAMODEL.md and optionally a
  schema file for the chosen ORM. Use when asked to "design the data model",
  "database schema", "entity relationships", "ERD", or "schema design".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - design the data model
  - database schema
  - entity relationships
  - erd
  - schema design
  - data model
  - design the schema
  - model the data
---

# /blueprint-datamodel — Data Model Design

Design the data model before writing a line of application code.
A bad schema is the most expensive technical debt you can accumulate —
it touches every query, every migration, every API response.

## Step 1 — Read existing context

Find the most recent version of each context file:

```bash
ls -t PRD-*.md TECHSTACK-*.md API-*.md 2>/dev/null | head -5
```

Open the most recent files found. Also check for existing schema files,
migration files, or ORM models.

## Step 2 — Extract entities from requirements

Read the PRD user stories. Every noun that users create, read, update,
or delete is a candidate entity.

For each entity, write:
```
Entity: <name>
Purpose: <one sentence — what this record represents>
Lifecycle: created when <event>, deleted when <event> (or never deleted)
Owner: belongs to <user/org/etc> or is global
```

Do not model entities that do not have at least one user story.
Do not add fields "in case we need them later."

## Step 3 — Design each entity's fields

For each entity, specify every field:

```
Table: users
  id          uuid, primary key, default gen_random_uuid()
  email       text, unique, not null
  name        text, nullable
  role        enum(user, admin), not null, default 'user'
  created_at  timestamptz, not null, default now()
  updated_at  timestamptz, not null, default now()
  deleted_at  timestamptz, nullable  (soft delete if needed)
```

Rules:
- Every table gets a surrogate primary key (`id uuid`)
- Every table gets `created_at` and `updated_at`
- Use `timestamptz` (not `timestamp`) for all times — timezone-aware
- Prefer `text` over `varchar(n)` — avoid arbitrary length limits
- Use enums for fields with a fixed set of values
- Mark fields nullable only when null is a meaningful distinct state

## Step 4 — Map relationships

For each relationship, specify:

```
users      1──< posts        (one user has many posts)
posts      1──< comments     (one post has many comments)
users      >──< tags         (many-to-many via post_tags join table)

Foreign keys:
  posts.user_id → users.id (on delete cascade)
  comments.post_id → posts.id (on delete cascade)
  post_tags.post_id → posts.id (on delete cascade)
  post_tags.tag_id → tags.id (on delete cascade)
```

Decide on each foreign key: `CASCADE`, `RESTRICT`, or `SET NULL`.
Never leave this implicit — it determines what happens when a user
is deleted.

## Step 5 — Define indexes

Every query path needs an index. List the queries first, then derive
the indexes:

```
Query: find all posts by user → index on posts(user_id)
Query: find posts by status, ordered by created_at → index on posts(status, created_at DESC)
Query: find user by email (login) → unique index on users(email)
Query: full text search on posts → GIN index on posts using to_tsvector
```

Add only indexes that serve a real query. Every index slows down writes.

## Step 6 — Check normalization

Verify the schema is in at least 3NF:
- No repeating groups (no arrays in a column where each element is a separate concern)
- No partial dependencies (every column depends on the full primary key)
- No transitive dependencies (column A → column B → column C should split to two tables)

Common violations to check:
- Storing comma-separated IDs in a text field — extract to a join table
- Duplicating a field that changes (e.g., user.company_name in every order) — use a FK
- Storing computed values — remove if they can be derived at query time

## Step 7 — Draw the ERD (ASCII)

```
┌─────────────┐         ┌─────────────┐
│    users    │         │    posts    │
├─────────────┤         ├─────────────┤
│ id (PK)     │──────<  │ id (PK)     │
│ email       │         │ user_id (FK)│
│ name        │         │ title       │
│ role        │         │ body        │
│ created_at  │         │ status      │
└─────────────┘         │ created_at  │
                        └─────────────┘
```

## Step 8 — Write the data model doc

Check for an existing data model:

```bash
ls -t DATAMODEL-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`DATAMODEL-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`DATAMODEL-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# Data Model

**Generated:** <YYYY-MM-DD HH:MM>
**Database:** PostgreSQL 15
**ORM:** <Prisma | Drizzle | TypeORM | SQLAlchemy | ActiveRecord | etc.>

## Entities

### users
<field table>

### posts
<field table>

## Relationships
<relationship list with FK behaviors>

## Indexes
<index list with rationale>

## ERD
<ASCII diagram>

## Design decisions
<Any non-obvious choices and why they were made>

## Latest file
This document supersedes: <previous DATAMODEL-*.md filename, if one exists>
```

## Step 9 — Generate the schema file (optional)

If the ORM and project are known, generate the initial schema file:
- Prisma: `schema.prisma`
- Drizzle: `schema.ts`
- TypeORM: entity files
- SQLAlchemy: `models.py`

## Step 10 — Generate Data Model HTML

After writing the `DATAMODEL-<YYYY-MM-DD>.md` file, generate a companion HTML
visualization: `DATAMODEL-<YYYY-MM-DD>.html` (same date as the markdown file).

Write a self-contained HTML file (no external dependencies — inline all CSS).
The file should be fully readable by opening it in any browser.

Structure the HTML as a visual ERD (Entity Relationship Diagram):

**Header section:**
- Page title: "Data Model — [Product Name]"
- Metadata bar: database engine, ORM, generated date
- Summary: N entities, M relationships

**ERD canvas:**
Draw each entity as a styled box. Lay them out in a logical grid — group
related entities together (e.g., user-facing entities in one cluster,
operational entities in another).

Each entity box contains:
- Entity name as the box header (distinct background color per entity)
- A table of fields:
  - Field name (bold if primary key, italic if foreign key)
  - Type (e.g., uuid, text, timestamptz, enum)
  - Constraints badge: PK / FK / NOT NULL / UNIQUE / DEFAULT

**Relationship lines:**
Connect related entity boxes with SVG lines or CSS border-based connectors.
Label each line with the relationship type:
- `1 ──< N` for one-to-many
- `N >──< M` for many-to-many (label the join table too)
- `1 ── 1` for one-to-one

Place cardinality labels at each end of the line.

**Relationships summary panel:**
Below the ERD, add a panel listing every relationship in plain text:
```
users 1──< posts (user_id FK, ON DELETE CASCADE)
posts 1──< comments (post_id FK, ON DELETE CASCADE)
users >──< tags via post_tags
```

**Index reference panel:**
List all indexes with rationale:
```
posts(user_id)          — find all posts by user
users(email) UNIQUE     — login lookup
posts(status, created_at DESC) — feed queries
```

**Style guidance:**
- Each entity box gets a distinct header color (cycle through a palette)
- Primary key fields marked with a key icon or `🔑` prefix
- Foreign key fields marked with a link icon or `→` prefix
- Clean white background, dark text, subtle card shadows
- Monospace font for field names and types

After generating the HTML file, confirm: "Generated `DATAMODEL-<date>.html` —
open in a browser to view the visual ERD."

## Step 11 — Handoff

Tell the user:
- How many entities were defined
- Any normalization tradeoffs made and why
- Any fields or relationships left as open questions
- The HTML visualization filename for sharing with stakeholders
- Suggest `/blueprint-api` to design the API layer on top of this schema
- Suggest `/perform-migrate` when ready to create the schema in the database