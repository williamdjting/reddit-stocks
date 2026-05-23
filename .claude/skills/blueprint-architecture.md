---
name: blueprint-architecture
version: 0.1.0
description: |
  Design the system architecture for an application. Covers component
  breakdown, data flow, integration points, scalability approach, and
  key architectural decisions with rationale. Use when asked to "design
  the architecture", "system design", "architecture doc", "how should
  this be structured", or "architecture review".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - design the architecture
  - system design
  - architecture doc
  - how should this be structured
  - architecture document
  - design the system
  - system architecture
---

# /blueprint-architecture — System Architecture

Design the system before building it. An architecture doc is a decision log —
it records what was chosen and why, so future engineers do not have to
reverse-engineer intent from code.

## Step 1 — Read existing context

Find the most recent version of each context file:

```bash
ls -t PRD-*.md TECHSTACK-*.md DATAMODEL-*.md API-*.md 2>/dev/null | head -5
```

Open the most recent files found.

## Step 2 — Establish constraints

Before designing, identify the hard constraints:

- **Scale:** How many users at launch? In 12 months? 10x from there?
- **Team size:** How many engineers will maintain this system?
- **Latency SLA:** What response time does the user expect?
- **Availability SLA:** Can the app go down for maintenance? For how long?
- **Compliance:** GDPR, HIPAA, SOC2, PCI — any data handling requirements?
- **Budget:** Hosting cost ceiling?

Design to your constraints, not to hypothetical future scale.
A system for 100 users that can scale to 10,000 is correct.
A system over-engineered for 10,000,000 from day one is waste.

## Step 3 — Identify the components

Break the system into distinct components. For each, define:

```
Component: <name>
Purpose: <one sentence>
Technology: <what it is built with>
Owns: <data or state this component is authoritative for>
Exposes: <API, events, or interface it provides to other components>
Depends on: <components or external services it calls>
```

Common component types for app development:
- **Client** — web app, mobile app, CLI
- **API server** — handles requests, orchestrates business logic
- **Background worker** — async processing, scheduled jobs
- **Database** — primary data store
- **Cache** — Redis, Memcached — session, hot data
- **Object storage** — files, images, uploads (S3, R2, GCS)
- **Queue** — task distribution (SQS, BullMQ, Sidekiq)
- **External services** — auth (Clerk, Auth0), email (Resend), payments (Stripe)

Only include components that the PRD actually requires.

## Step 4 — Draw the data flow

For the most important user action, trace the full request path:

```
User → Client → API Server → Database
                           → Cache (read-through)
                           → Queue → Worker → External Service
```

Then draw the ASCII architecture diagram:

```
┌─────────┐   HTTPS    ┌───────────┐   SQL    ┌──────────┐
│  React  │──────────▶ │  Next.js  │─────────▶│ Postgres │
│  SPA    │            │  API      │          └──────────┘
└─────────┘            │  Routes   │   Redis  ┌──────────┐
                       │           │─────────▶│  Cache   │
                       └─────────┬─┘          └──────────┘
                                 │  BullMQ    ┌──────────┐
                                 └───────────▶│  Worker  │
                                              └────┬─────┘
                                                   │ SMTP
                                              ┌────▼─────┐
                                              │  Resend  │
                                              └──────────┘
```

## Step 5 — Identify integration points

For every external service:

```
Service: Stripe
Purpose: payment processing
Data in: order amount, customer id
Data out: payment intent id, webhook events
Failure mode: payment API down — queue the order, retry with exponential backoff
Fallback: none — block checkout until available
```

Every integration is a failure point. Document how the system behaves
when each external service is unavailable.

## Step 6 — Record architectural decisions (ADRs)

For every non-obvious choice, write a one-paragraph ADR:

```markdown
### ADR-001: Use PostgreSQL over MongoDB

**Decision:** PostgreSQL

**Reason:** Data is relational (users, orgs, memberships, resources all
join). Transactions are needed for billing operations. The team knows SQL.
MongoDB would require denormalization upfront or expensive cross-document
lookups later.

**Rejected alternative:** MongoDB — document model fits the API response
shape but creates join pain at the DB layer, which is worse than the
occasional schema migration.

**Reversibility:** Low — migration from PG to Mongo would require a full
data export/import and API rewrite.
```

ADRs that are not written get re-litigated every quarter.

## Step 7 — Define the deployment topology

```
Environments: local → staging → production
Deploy target: <Vercel / Railway / Fly.io / AWS / GCP / VPS>

Production topology:
  API: 2 instances minimum, autoscale on CPU
  Worker: 1 instance, scale manually
  Database: single primary, daily backups, 7-day retention
  Cache: single instance (Redis is optional — add only if needed)
```

## Step 8 — Identify risks

List the top 3–5 technical risks with mitigation:

```
Risk: Single database is a SPOF
Mitigation: Automated backups, promote replica if available

Risk: No rate limiting on API
Mitigation: Add per-IP rate limiting at API layer before launch

Risk: External auth provider (Clerk) outage
Mitigation: Session tokens allow 7 days of offline auth, display status page
```

## Step 9 — Write the architecture doc

Check for an existing architecture doc:

```bash
ls -t ARCHITECTURE-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`ARCHITECTURE-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`ARCHITECTURE-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# Architecture

**Generated:** <YYYY-MM-DD HH:MM>

## Overview
<2–3 sentences: what is being built and how it fits together>

## Components
<component table>

## Data flow
<ASCII diagram>

## Integration points
<external service table>

## Architectural decisions
<ADRs>

## Deployment topology
<env map>

## Known risks
<risk table>

## Latest file
This document supersedes: <previous ARCHITECTURE-*.md filename, if one exists>
```

## Step 10 — Check for system diagram readiness

After writing the ARCHITECTURE file, check whether the other two system design
artifacts are also present:

```bash
ls SCENARIOS-*.md TECHSTACK-*.md 2>/dev/null
```

If both `SCENARIOS-*.md` AND `TECHSTACK-*.md` exist (any version), generate
`SYSTEM_DIAGRAM.html` now. Follow the **System Diagram HTML** specification
in `blueprint-scenarios/SKILL.md` — read it for the full structure and
style requirements.

If either is missing, skip this step — the diagram will be generated when
the missing skill completes.

## Step 11 — Handoff

Tell the user:
- How many components were identified
- The top architectural risk and mitigation
- Any decisions left open that must be resolved before building
- Whether `SYSTEM_DIAGRAM.html` was generated or what is still needed
- Suggest `/blueprint-datamodel` if the data layer is not yet designed
- Suggest `/review-eng` for a technical challenge of the architecture