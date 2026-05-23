---
name: perform-deploy
version: 0.1.0
description: |
  Set up deployment infrastructure, CI/CD pipelines, and environment
  configuration for an application. Covers hosting choice, environment
  variables, build pipeline, preview deployments, and production deploy
  process. Use when asked to "set up deployment", "deploy this app",
  "configure CI/CD", "set up hosting", or "get this to production".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - AskUserQuestion
triggers:
  - set up deployment
  - deploy this app
  - configure cicd
  - set up hosting
  - get this to production
  - deployment pipeline
  - set up ci
  - push to production
---

# /perform-deploy — Deploy and Ship

Get the app running in production with a repeatable, automated pipeline.

## Step 1 — Read existing context

Check for:
- `TECHSTACK.md` — hosting and infrastructure decisions
- `CLAUDE.md` — project-specific deploy commands
- `package.json`, `Dockerfile`, or CI config files already present

Understand what stack and hosting target are already decided before
proposing anything.

## Step 2 — Establish deployment requirements

Ask or confirm:

- **Hosting target** — Vercel, Railway, Fly.io, AWS, GCP, VPS, etc.
- **Environments** — preview (per-PR), staging, production
- **Build output** — static site, Node server, Docker container, serverless functions
- **Environment variables** — what secrets need to be injected at runtime
- **Database** — managed service, connection pooling, migration strategy
- **Domain** — custom domain, SSL/TLS setup

## Step 3 — Create the environment variable map

List every variable the app needs:

```
# .env.example (committed — no real values)
DATABASE_URL=
API_KEY=
JWT_SECRET=
NEXT_PUBLIC_API_URL=
NODE_ENV=
```

Separate:
- **Build-time vars** (baked into the bundle)
- **Runtime vars** (injected by the hosting platform)
- **Secrets** (never logged, never committed, rotated on breach)

Create `.env.example` with keys but no values. Verify `.env` is in `.gitignore`.

## Step 4 — Write the build configuration

Ensure the project has a clean, reproducible build:

```bash
# Verify the build succeeds locally
# e.g., npm run build, bun run build, docker build .
```

If there is no build script, create one. The CI pipeline will call this
exact command — it must work without local state.

## Step 5 — Write the CI/CD pipeline

Create the pipeline config for the team's CI system.

**GitHub Actions example structure** (`.github/workflows/deploy.yml`):

```
Triggers: push to main → production deploy
          pull_request → preview deploy + test run

Jobs:
  test:    install → lint → test
  build:   install → build → upload artifact
  deploy:  download artifact → deploy to target
```

Key principles:
- Tests must pass before any deploy runs
- Preview deploys on every PR — never merge blind
- Production deploys only from main, never from feature branches
- Secrets injected from CI secret store, never hardcoded

## Step 6 — Configure the hosting target

Follow the hosting platform's setup:

- Connect the git repo to the platform
- Set all environment variables from Step 3
- Set the build command and output directory
- Set the install command (`npm ci` not `npm install` in CI)
- Configure health check endpoint if applicable

```bash
# Verify platform CLI is available if needed
# e.g., vercel --version, fly version, railway --version
```

## Step 7 — Set up the production database

If the app uses a database:
- Provision the managed database (not self-hosted in production)
- Set connection pooling limits appropriate for the serverless/server model
- Run initial migrations
- Verify the connection from the deployed environment
- Set up automated backups with a retention policy

## Step 8 — First production deploy

```bash
# Trigger the first deploy via the pipeline or CLI
# Monitor the deploy logs in real time
```

After deploy:
- Hit the production URL — verify the app loads
- Check the health endpoint if one exists
- Verify environment variables are being read correctly
- Check error monitoring (Sentry, Datadog, etc.) for silent failures

## Step 9 — Document the deploy process

Check for an existing deploy doc:

```bash
ls -t DEPLOY-*.md 2>/dev/null | head -3
```

**Never overwrite an existing file.** Create a new dated file:
`DEPLOY-<YYYY-MM-DD>.md` (and update `CLAUDE.md` with the deploy commands).
If a file for today already exists, append the time:
`DEPLOY-<YYYY-MM-DD>-<HHMM>.md`

File header: `**Generated:** <YYYY-MM-DD HH:MM>`

Contents:

```markdown
## Deploy

**Production:** Automatic on merge to main via GitHub Actions
**Preview:** Automatic on every PR

**Manual deploy:** <command if applicable>
**Rollback:** <command or steps>
**Environment variables:** Set in <platform dashboard URL>
**Logs:** <where to find them>

## Latest file
This document supersedes: <previous DEPLOY-*.md filename, if one exists>
```

## Step 10 — Handoff

Tell the user:
- Production URL
- Where environment variables are managed
- How to trigger a deploy (auto vs manual)
- How to roll back if something goes wrong
- Suggest `/review-release` before announcing to users