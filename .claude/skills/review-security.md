---
name: review-security
version: 0.1.0
description: |
  Security audit of application code and infrastructure. Covers OWASP Top 10,
  authentication and authorization, secrets management, input validation,
  dependency vulnerabilities, and API security. Produces a prioritized
  findings report with remediation steps. Use when asked to "security review",
  "security audit", "check for vulnerabilities", "OWASP review",
  or "is this secure".
allowed-tools:
  - Bash
  - Read
  - Grep
  - AskUserQuestion
triggers:
  - security review
  - security audit
  - check for vulnerabilities
  - owasp review
  - is this secure
  - find security issues
  - pentest
  - threat model
---

# /review-security — Security Audit

Find the vulnerabilities before attackers do. Covers the most common
exploit categories that affect production web applications.

## Step 1 — Establish scope

Confirm:
- What surface is being audited? (frontend, API, database layer, infra)
- Is this a new codebase review or a diff review (pre-PR)?
- Are there compliance requirements? (OWASP Top 10, SOC2, HIPAA, PCI)

## Step 2 — Scan for secrets in code

```bash
# Find hardcoded secrets, API keys, passwords
grep -r "password\s*=\s*['\"]" . --include="*.ts" --include="*.js" \
  --include="*.py" --include="*.env" | grep -v node_modules | grep -v ".example"

grep -rE "(api_key|apikey|secret|token|password)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{8,}" \
  . --include="*.ts" --include="*.js" --include="*.py" | grep -v node_modules

# Check for .env files that may have been committed
git log --all --full-history -- "*.env" | head -10
```

**CRITICAL — mark any finding here as BLOCK immediately.**
A leaked secret is an active incident, not a finding.

## Step 3 — Check authentication

Read authentication-related code and verify:

- [ ] Passwords are hashed with bcrypt/argon2/scrypt — **never MD5/SHA1**
- [ ] JWT secrets are from environment variables — never hardcoded
- [ ] JWT expiry is set — no non-expiring tokens
- [ ] Session tokens are invalidated on logout
- [ ] Password reset tokens expire (15–60 minutes max)
- [ ] Failed login attempts are rate-limited
- [ ] Authentication is required before any auth-protected endpoint is reached

```bash
# Find auth-related files
grep -r "jwt\|bcrypt\|argon2\|session\|cookie\|token" . \
  --include="*.ts" --include="*.js" -l | grep -v node_modules | head -10
```

## Step 4 — Check authorization

Verify that authorization is enforced at the data layer, not just the route layer:

- [ ] Every data fetch filters by the authenticated user's ownership
- [ ] Admin-only operations check role — not just authentication
- [ ] Object-level authorization: user cannot access another user's records
  by guessing an ID (IDOR — Insecure Direct Object Reference)
- [ ] Bulk operations (exports, deletes) verify ownership of every item

```bash
# Find DB queries — check for ownership filters
grep -r "findById\|findOne\|where.*id" . --include="*.ts" --include="*.js" \
  | grep -v node_modules | grep -v test | head -20
```

## Step 5 — Check input validation

- [ ] All user input is validated before use (schema validation, not just type checks)
- [ ] SQL queries use parameterized queries / ORM — never string concatenation
- [ ] File uploads validate type AND magic bytes — not just file extension
- [ ] File upload size limits are enforced
- [ ] HTML output is escaped (XSS prevention) — check template rendering

```bash
# Find raw SQL that might be injectable
grep -rE "query\(.*\$\{|query\(.*\+|execute\(.*\$\{" . \
  --include="*.ts" --include="*.js" | grep -v node_modules | head -20

# Find innerHTML usage (potential XSS)
grep -r "innerHTML\|dangerouslySetInnerHTML" . \
  --include="*.ts" --include="*.tsx" --include="*.js" | grep -v node_modules | head -10
```

## Step 6 — Check API security

- [ ] Rate limiting is in place on all public endpoints
- [ ] CORS is configured to an explicit allowlist — not `*`
- [ ] API errors do not leak stack traces or internal paths in production
- [ ] Sensitive fields (password hash, internal IDs) are not in API responses
- [ ] HTTP security headers are set (Content-Security-Policy, X-Frame-Options,
  X-Content-Type-Options, Referrer-Policy)

```bash
# Find CORS configuration
grep -r "cors\|Access-Control" . --include="*.ts" --include="*.js" \
  | grep -v node_modules | head -10
```

## Step 7 — Check dependency vulnerabilities

```bash
# Node.js projects
npm audit --audit-level=high 2>/dev/null || yarn audit --level high 2>/dev/null

# Python projects
pip-audit 2>/dev/null || safety check 2>/dev/null

# Check for outdated packages with known CVEs
```

Flag any HIGH or CRITICAL vulnerabilities. Provide the upgrade path.

## Step 8 — Check infrastructure and config

- [ ] Environment variables are used for all secrets — no hardcoded values
- [ ] `.env` files are in `.gitignore`
- [ ] Database is not publicly accessible (requires VPC / allowlist)
- [ ] Debug mode / verbose logging is disabled in production
- [ ] Error pages do not expose server version or stack details

## Step 9 — Produce the findings report

Check for an existing security review:

```bash
ls -t SECURITY_REVIEW-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`SECURITY_REVIEW-<YYYY-MM-DD>.md`
If a file for today already exists, append the time:
`SECURITY_REVIEW-<YYYY-MM-DD>-<HHMM>.md`

Organize findings by severity:

```
CRITICAL — exploitable now, active data breach risk
HIGH     — exploitable with moderate effort, must fix before launch
MEDIUM   — exploitable under specific conditions
LOW      — defense-in-depth improvements
INFO     — observations, best practice gaps with no immediate risk
```

File header:

```markdown
# Security Review

**Generated:** <YYYY-MM-DD HH:MM>
**Scope:** <what was audited>
```

For each finding:
```
Severity: HIGH
Category: OWASP A01 — Broken Access Control
Location: src/api/users.ts:42
Finding: User records fetched by ID without ownership check.
         Any authenticated user can read any user's data by
         guessing or enumerating user IDs.
Fix: Add `WHERE user_id = :currentUserId` to the query.
```

At the bottom of the file:
```markdown
## Latest file
This document supersedes: <previous SECURITY_REVIEW-*.md filename, if one exists>
```

## Step 10 — Handoff

Tell the user:
- Count of findings by severity
- The single most critical finding to fix first
- Any finding that is a BLOCK (must not ship with this issue)
- Any dependency upgrade needed
- Suggest `/review-qa` for a full pre-landing review after fixes