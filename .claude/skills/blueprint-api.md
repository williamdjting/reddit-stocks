---
name: blueprint-api
version: 0.1.0
description: |
  Design and document a REST or GraphQL API contract before implementation
  begins. Covers resource modeling, endpoint design, request/response schemas,
  authentication, error codes, and versioning strategy. Use when asked to
  "design the API", "write an API spec", "API contract", "REST API design",
  or "define the endpoints".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - design the api
  - write an api spec
  - api contract
  - rest api design
  - define the endpoints
  - api documentation
  - api design
  - spec the api
---

# /blueprint-api — API Contract Design

Design the API before building it. A clear contract prevents frontend/backend
misalignment and prevents breaking changes from becoming production incidents.

## Step 1 — Read existing context

Find the most recent version of each context file:

```bash
ls -t PRD-*.md DATAMODEL-*.md TECHSTACK-*.md 2>/dev/null | head -5
```

Open the most recent files found. Also check for existing API files or OpenAPI specs.

Pull constraints before designing anything.

## Step 2 — Decide the API style

If not already decided, confirm:

- **REST** — resource-oriented, standard HTTP verbs, best for CRUD-heavy apps
- **GraphQL** — query-driven, best for complex data graphs or mobile clients
- **tRPC** — TypeScript-first RPC, best for full-stack TypeScript monorepos
- **WebSocket** — real-time, bidirectional, best for live features

Document the choice and the reason. An undocumented architecture decision
gets relitigated every six months.

## Step 3 — Model the resources

List every entity the API exposes. For each:

```
Resource: <name>
Fields: id, <field> (<type>, <required/optional>), ...
Relationships: belongs_to <resource>, has_many <resource>
Ownership: who can read / write / delete this resource
```

Map directly from `DATAMODEL.md` if it exists.

## Step 4 — Design the endpoints

For each resource, define the full CRUD surface plus any actions:

```
Standard REST pattern:
  GET    /resources          → list (paginated)
  POST   /resources          → create
  GET    /resources/:id      → read one
  PATCH  /resources/:id      → partial update
  PUT    /resources/:id      → full replace
  DELETE /resources/:id      → delete

Actions (non-CRUD operations):
  POST   /resources/:id/activate
  POST   /resources/:id/archive
```

Only include endpoints that are required by the PRD. Do not design
endpoints speculatively.

## Step 5 — Define request and response schemas

For every endpoint, document:

```markdown
### POST /users

Create a new user.

**Auth:** None (public)

**Request**
\```json
{
  "email": "string, required, valid email",
  "password": "string, required, min 8 chars",
  "name": "string, optional"
}
\```

**Response 201**
\```json
{
  "id": "string",
  "email": "string",
  "name": "string | null",
  "createdAt": "ISO 8601 datetime"
}
\```

**Errors**
| Status | Code | Description |
|--------|------|-------------|
| 400 | VALIDATION_ERROR | Request body failed validation |
| 409 | EMAIL_EXISTS | Email already registered |
```

Every field in every request and response must be listed.
Every error that can be returned must be listed.

## Step 6 — Define authentication and authorization

Document:
- **Auth scheme** — Bearer token, API key, session cookie
- **Token format** — JWT (document claims), opaque (document lookup)
- **Per-endpoint auth** — public, authenticated, role-required
- **Ownership rules** — can user A read user B's resource?

```
Auth header: Authorization: Bearer <token>
Token lifetime: 7 days (refresh via POST /auth/refresh)

Roles: user, admin
  user: can read/write own resources only
  admin: can read/write all resources
```

## Step 7 — Define pagination and filtering

For all list endpoints, establish:

```
Pagination: cursor-based preferred for large datasets
  Request:  GET /users?cursor=<cursor>&limit=20
  Response: { data: [...], nextCursor: "...", hasMore: true }

Filtering: explicit allowlist (not passthrough)
  GET /users?status=active&role=admin

Sorting: explicit allowlist
  GET /users?sortBy=createdAt&order=desc
```

## Step 8 — Define error format

All errors across all endpoints use one consistent format:

```json
{
  "error": {
    "code": "MACHINE_READABLE_CODE",
    "message": "Human readable description",
    "details": { }
  }
}
```

List every error code the API can return at the bottom of the document.

## Step 9 — Define versioning strategy

How will breaking changes be handled?
- **URL versioning** — `/v1/users`, `/v2/users` (simple, cacheable)
- **Header versioning** — `API-Version: 2024-01-01` (clean URLs)
- **No versioning** — additive changes only, breaking changes require deprecation

Document the policy. When in doubt, use URL versioning for public APIs.

## Step 10 — Write the API contract

Check for an existing API doc:

```bash
ls -t API-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`API-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`API-<YYYY-MM-DD>-<HHMM>.md`

Save the complete API contract:

```markdown
# API Reference

**Generated:** <YYYY-MM-DD HH:MM>
**Base URL:** https://api.example.com/v1
**Auth:** Bearer token via Authorization header
**Format:** JSON request and response bodies

## Authentication
...

## Resources

### Users
...

## Error codes
...

## Latest file
This document supersedes: <previous API-*.md filename, if one exists>
```

## Step 11 — Generate API Contract HTML

After writing the `API-<YYYY-MM-DD>.md` file, generate a companion HTML
visualization: `API-<YYYY-MM-DD>.html` (same date as the markdown file).

Write a self-contained HTML file (no external dependencies — inline all CSS).
The file should be fully readable by opening it in any browser.

Structure the HTML as follows:

**Header section:**
- Product/API name as the page title
- Base URL, auth scheme, and generated date as a metadata bar
- A summary count: N endpoints across M resources

**Sidebar navigation:**
- List every resource as a nav link
- Each resource expands to show its endpoints (method + path)
- Color-code method badges: GET=green, POST=blue, PUT=orange,
  PATCH=yellow, DELETE=red

**Main content area — one card per endpoint:**
Each card contains:
- Method badge + path (e.g., `POST /users`) as the card heading
- One-line description of the endpoint
- Auth requirement (None / Bearer token / Role required)
- Request body fields as a formatted table (field | type | required | description)
- Response body fields as a formatted table for each status code
- Errors table (status | code | description)

**Auth section:**
- Full auth scheme description
- Token format and lifetime
- Role definitions and what each role can access

**Error codes section:**
- Complete table of all error codes the API can return
- Columns: Code | HTTP Status | Description

**Style guidance:**
- Clean white background, dark text, subtle card shadows
- Monospace font for paths, field names, and JSON values
- Sticky sidebar so navigation stays visible while scrolling
- Responsive: sidebar collapses to a top nav on narrow screens

After generating the HTML file, confirm: "Generated `API-<date>.html` — open
in a browser to view the visual API contract."

## Step 12 — Handoff

Tell the user:
- How many endpoints are defined
- Any decisions deferred as open questions
- The HTML visualization filename for sharing with stakeholders
- Suggest `/blueprint-datamodel` if the data model is not yet specified
- Suggest `/review-eng` for architecture review of the API design
- Suggest `/perform-implement` when ready to build