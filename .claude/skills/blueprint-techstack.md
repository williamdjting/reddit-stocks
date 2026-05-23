---
name: blueprint-techstack
version: 0.1.0
description: |
  Recommend and document the technology stack for a product or feature.
  Covers frontend, backend, database, infrastructure, and tooling with
  rationale for each choice. Use when asked to "choose a tech stack",
  "what should we build with", "architecture decision", or "tech stack".
allowed-tools:
  - Bash
  - Read
  - Write
  - WebSearch
  - AskUserQuestion
triggers:
  - choose a tech stack
  - what should we build with
  - architecture decision
  - tech stack
  - what technology should we use
---

# /blueprint-techstack — Tech Stack Recommendation

Choose the right tools for the job and document the decisions so future
engineers understand not just what was chosen, but why.

## Step 1 — Read existing context

Find and read the most recent context files:

```bash
ls -t PRD-*.md OPPORTUNITY-*.md DESIGN-*.md 2>/dev/null | head -5
```

Open the most recent files found. Extract:
- Scale requirements (users, requests/sec, data volume)
- Non-functional requirements (performance, uptime, security)
- Team constraints or existing tech mentioned

## Step 2 — Gather constraints

Use AskUserQuestion to collect what cannot be changed:

1. **Team** — What languages and frameworks does the team know well?
2. **Existing systems** — Is this greenfield or integrated into an existing codebase? What does it need to talk to?
3. **Scale** — Expected users at launch? In 12 months?
4. **Budget** — Any infrastructure cost ceiling?
5. **Compliance** — Any regulatory requirements (HIPAA, SOC2, GDPR)?
6. **Timeline** — When must this ship? Does that constrain the choice?

Record hard constraints (cannot be violated) and soft constraints (prefer to satisfy).

## Step 3 — Research options

For each layer, identify 2–3 candidate options and evaluate against constraints.
Use WebSearch to check ecosystem health (last major release, community activity).

Layers to cover:
- **Frontend** (framework, state management, styling)
- **Backend** (language, framework, API style: REST vs GraphQL vs RPC)
- **Database** (relational vs document vs time-series; managed vs self-hosted)
- **Authentication** (managed vs DIY; session vs JWT)
- **Infrastructure** (cloud provider, container vs serverless vs VMs)
- **Observability** (logging, metrics, error tracking)
- **CI/CD** (build, test, deploy pipeline)

## Step 4 — Recommend and justify each layer

```
### <Layer Name>

**Chosen:** <technology>
**Rejected alternatives:** <option A> (reason), <option B> (reason)
**Rationale:** <why this one wins given our constraints>
**Risks:** <what could go wrong with this choice>
```

Flag any choice where the team has no prior experience as a risk.

## Step 5 — Draw the architecture

Write an ASCII architecture diagram showing how the layers connect:

```
[Browser / Mobile App]
        │ HTTPS
        ▼
[API Gateway / Load Balancer]
        │
        ▼
[Application Server]
    │           │
    ▼           ▼
[Primary DB]  [Cache]
```

Label every arrow with the protocol or mechanism.

## Step 6 — Identify key architectural decisions

List the 3–5 most consequential choices that are hard to reverse:

| Decision | Options considered | Choice | Reversibility |
|----------|--------------------|--------|---------------|
| | | | Easy / Hard / Painful |

For Hard or Painful decisions, note the exit path if the choice turns out wrong.

## Step 7 — Write the tech stack doc

Check for an existing tech stack doc:

```bash
ls -t TECHSTACK-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`TECHSTACK-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`TECHSTACK-<YYYY-MM-DD>-<HHMM>.md`

```markdown
# Tech Stack: <Product / Feature Name>

**Generated:** <YYYY-MM-DD HH:MM>
**Status:** Draft | Approved

## Constraints
**Hard:** <list>
**Soft:** <list>

## Stack Overview
| Layer | Technology | Version / Tier |
|-------|-----------|----------------|
| Frontend | | |
| Backend | | |
| Database | | |
| Auth | | |
| Infrastructure | | |
| Observability | | |
| CI/CD | | |

## Architecture Diagram
<ASCII diagram from Step 5>

## Layer Decisions
<Sections from Step 4>

## Key Architectural Decisions
<Table from Step 6>

## What We Will NOT Use and Why
<Explicit rejections. Prevents re-litigating decisions later.>

## Risks and Mitigations
<Top 3 technical risks with mitigation plan.>

## Latest file
This document supersedes: <previous TECHSTACK-*.md filename, if one exists>
```

## Step 8 — Check for system diagram readiness

After writing the TECHSTACK file, check whether the other two system design
artifacts are also present:

```bash
ls SCENARIOS-*.md ARCHITECTURE-*.md 2>/dev/null
```

If both `SCENARIOS-*.md` AND `ARCHITECTURE-*.md` exist (any version), generate
`SYSTEM_DIAGRAM.html` now. Follow the **System Diagram HTML** specification
in `blueprint-scenarios/SKILL.md` — read it for the full structure and
style requirements.

If either is missing, skip this step — the diagram will be generated when
the missing skill completes.

## Step 9 — Handoff

Tell the user:
- Any layer where confidence is low (team unfamiliarity, immature ecosystem)
- The one decision that, if wrong, is most expensive to reverse
- Whether `SYSTEM_DIAGRAM.html` was generated or what is still needed
- Suggest `/blueprint-prd` or `/blueprint-design` if not already done
- Suggest `/review-eng` to validate architecture before implementation