---
name: perform-migrate
version: 0.1.0
description: |
  Write and run database migrations safely. Covers schema changes (add/drop
  columns, tables, indexes), data backfills, and rename operations. Produces
  reversible migrations with a rollback plan. Use when asked to "write a
  migration", "add a column", "migrate the database", "schema change",
  or "backfill data".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - AskUserQuestion
triggers:
  - write a migration
  - add a column
  - migrate the database
  - schema change
  - backfill data
  - rename a column
  - drop a table
  - add an index
  - database migration
---

# /perform-migrate — Database Migrations

Schema changes that are safe to run on live production data.

## Step 1 — Read the current schema

Before writing any migration, read the current state:

```bash
# Find the existing migration files
find . -name "*.migration.*" -o -name "*_migration*" -o \
  -path "*/migrations/*" | grep -v node_modules | sort | tail -20

# Find the schema definition file
find . -name "schema.prisma" -o -name "schema.rb" -o \
  -name "models.py" | grep -v node_modules | head -5
```

Read the most recent migration to understand current state. Never
write a migration without knowing what you are starting from.

## Step 2 — Clarify the change

Confirm before writing:

- **What exactly is changing?** (table name, column name, type, constraint)
- **Is this additive or destructive?** (add = safe, drop = dangerous)
- **Is there existing data to migrate?** (backfill needed?)
- **Is this a breaking change?** (will old code break before deploy?)
- **Does this need to be backward compatible?** (dual-write period?)

For any destructive change (drop column, drop table, change type), ask
explicitly whether the data is expendable or needs archiving.

## Step 3 — Plan for zero-downtime (production apps)

For production databases with live traffic, use the expand-contract pattern:

**Never do this in a single migration on a live system:**
- DROP COLUMN with active reads
- RENAME COLUMN (breaks running code immediately)
- Change column type (may lock the table)
- Add NOT NULL without a default (breaks inserts from old code)

**Instead, sequence it:**
```
Phase 1 — Expand:  Add new column (nullable), deploy code that writes to both
Phase 2 — Backfill: Fill existing rows
Phase 3 — Contract: Drop old column after all code stops reading it
```

If this is a dev/staging environment with no live traffic, a single
migration is fine.

## Step 4 — Write the migration

Match the ORM and migration tool already in use in the project.

**Structure every migration with:**
1. An `up` function (apply the change)
2. A `down` function (revert the change)
3. A descriptive name with a timestamp prefix

```
<timestamp>_add_<column>_to_<table>
<timestamp>_create_<table>
<timestamp>_backfill_<column>_from_<source>
<timestamp>_drop_<column>_from_<table>
```

For data backfills, batch the updates — never update all rows in a
single query on a large table:

```sql
-- Process in batches of 1000 to avoid lock escalation
UPDATE users SET full_name = first_name || ' ' || last_name
WHERE id BETWEEN :start AND :end AND full_name IS NULL;
```

## Step 5 — Add the corresponding index

Every foreign key and every column used in a WHERE or JOIN clause needs
an index. Add it in the same migration or a companion migration:

```sql
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
-- CONCURRENTLY avoids locking the table during index build (PostgreSQL)
```

## Step 6 — Test the migration

```bash
# Run on a local copy of the database
# Apply the migration
# Verify the schema changed as expected
# Run the down migration
# Verify the schema reverted cleanly
# Run the up migration again — migrations must be idempotent where possible
```

Run the app's test suite after applying the migration.

## Step 7 — Write the rollback plan

Document how to revert if something goes wrong in production:

```markdown
## Rollback plan for <migration name>

If the migration fails mid-run:
1. Run: <down migration command>
2. Verify: <check command>

If the deploy succeeds but causes a production incident:
1. Revert the code deploy first
2. Then run: <down migration command>
3. If data was written under the new schema: <data recovery steps>
```

## Step 8 — Handoff

Tell the user:
- The migration file created
- How to apply it: exact command
- How to roll it back: exact command
- Any manual steps required (e.g., update seed data, notify other services)
- Whether this requires a code deploy before or after the migration
- Suggest `/review-eng` if this is a complex schema change