# Zero-to-Deploy API Runbook

This runbook is the operating manual for the Zero-to-Deploy API. It explains how to deploy, verify, roll back, and respond to incidents when the service is unhealthy.

Use this file during demos, production checks, and 2 AM incidents.

## Service Summary

| Field | Value |
| --- | --- |
| Service name | Zero-to-Deploy API |
| Repository | `https://github.com/siddharth0998/zero-to-deploy-api` |
| Runtime | FastAPI on Uvicorn |
| Container | Multi-stage Python Docker image |
| Registry | `ghcr.io/siddharth0998/zero-to-deploy-api` |
| Host | Render web service |
| Health endpoint | `GET /health` |
| Public URL | `https://siddharth-todo-api.onrender.com` |
| Primary branch | `main` |
| CI | GitHub Actions, `.github/workflows/main.yml` |
| Logs | Render service logs plus application stdout |
| Uptime monitor | External monitor pointed at `/health` |

Set this shell variable before using commands in this runbook:

```bash
export LIVE_API_URL="https://siddharth-todo-api.onrender.com"
```

## Golden Signals

For this small API, the most important signals are:

| Signal | Source | Healthy value |
| --- | --- | --- |
| Availability | External uptime monitor | `/health` returns `200`. |
| Readiness | Render health check | `/health` returns `2xx` before traffic shift. |
| Error rate | Render logs and client reports | No sustained `5xx` responses. |
| Latency | Render metrics or monitor timing | Stable for free-tier baseline. |
| Deploy status | Render events and GitHub Actions | Latest deploy successful. |
| Image build | GitHub Actions and GHCR | SHA tag exists for deployed commit. |

## Endpoint Contracts

### `GET /health`

Purpose:

- Render readiness check
- external uptime monitor
- incident verification
- post-deploy smoke test

Expected response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

Healthy criteria:

- HTTP status is `200`.
- JSON response contains `"status": "healthy"`.
- Response arrives within the monitor timeout.

Unhealthy criteria:

- DNS failure
- TLS failure
- HTTP timeout
- HTTP `5xx`
- HTTP `404` on `/health`
- non-JSON response from the application
- Render reports no running instance

### `GET /`

Purpose:

- basic functional check for users
- confirms routing reaches the application

### `GET /data`

Purpose:

- confirms prototype business endpoint is responding
- emits an application log entry

## Normal Deployment Flow

Use this when shipping a normal code change.

### 1. Prepare locally

```bash
git status --short
ruff check .
pytest -q
docker build -t zero-to-deploy-api:local .
```

Expected:

- no unrelated local changes mixed into the release
- ruff passes
- pytest passes
- Docker image builds successfully

### 2. Make the change

Keep changes small and reversible.

Examples:

- endpoint response change
- dependency patch
- logging improvement
- health metadata improvement
- documentation update

### 3. Run local verification

```bash
ruff check .
pytest -q
docker build -t zero-to-deploy-api:local .
```

Optional container smoke test:

```bash
docker run --rm -p 8000:8000 zero-to-deploy-api:local
curl -i http://localhost:8000/health
```

Expected `/health` result:

```json
{"status":"healthy","version":"1.0.0","environment":"dev"}
```

### 4. Commit and push

```bash
git add .
git commit -m "feat: describe the change"
git push origin main
```

### 5. Watch GitHub Actions

Open:

```text
https://github.com/siddharth0998/zero-to-deploy-api/actions
```

Expected pipeline behavior:

1. Dependencies install successfully.
2. `ruff check .` passes.
3. `pytest -q` passes.
4. Docker image builds.
5. On `main`, the image is pushed to GHCR as `latest` and the commit SHA.

If CI fails, do not deploy the change. See "CI Failure Response".

### 6. Watch Render deploy

Open the Render service dashboard.

Expected deployment behavior if Render is connected to the GitHub repo:

1. Render sees the push to `main`.
2. Render builds the Dockerfile.
3. Render starts a new instance.
4. Render checks `/health`.
5. Render shifts traffic after the new instance is healthy.

Expected deployment behavior if Render pulls from GHCR:

1. GitHub Actions pushes the image.
2. A manual deploy or deploy hook tells Render to pull the new image.
3. Render starts the new container.
4. Render checks `/health`.
5. Render shifts traffic after the new instance is healthy.

### 7. Smoke test production

```bash
curl -i "$LIVE_API_URL/health"
curl -i "$LIVE_API_URL/"
curl -i "$LIVE_API_URL/data"
```

Expected:

- `/health` returns `200`
- `/` returns `200`
- `/data` returns `200`
- logs show the `/data` access
- external uptime monitor returns to healthy if it briefly showed deploy activity

### 8. Record evidence

For case submission, capture:

- GitHub Actions green check
- GHCR image tag
- Render successful deploy event
- live `/health` response
- uptime monitor success
- walkthrough video showing code change to deployed result

## Rollback

Use rollback when a release causes errors, failed health checks, broken endpoint behavior, or unacceptable latency.

### Rollback decision guide

| Situation | Recommended action |
| --- | --- |
| Render deploy failed before traffic shift | Usually no rollback needed; previous version should still be serving. Investigate failed deploy. |
| New version deployed and `/health` fails | Use Render rollback to previous successful deploy. |
| New version deployed and `/data` behavior is wrong | Roll back or revert depending on severity. |
| Bad config or secret | Correct the Render environment variable and redeploy. |
| Bad image tag from GHCR | Redeploy previous known-good SHA tag. |
| Documentation-only issue | Fix forward with a new commit. |

### Fast rollback through Render

1. Open the Render dashboard.
2. Select the Zero-to-Deploy API service.
3. Go to deploy history or events.
4. Choose the last known-good successful deploy.
5. Click rollback or redeploy that version.
6. Wait for Render to report success.
7. Verify:

```bash
curl -i "$LIVE_API_URL/health"
curl -i "$LIVE_API_URL/data"
```

8. Watch the external uptime monitor for at least two successful checks.

### Rollback through Git revert

Use this when the safest long-term fix is to undo a bad commit in source control.

```bash
git log --oneline -5
git revert <bad-commit-sha>
ruff check .
pytest -q
git push origin main
```

Then watch:

- GitHub Actions
- Render deploy
- `/health`
- external monitor

### Rollback to a previous GHCR image

Use this only if Render is configured to deploy from GHCR.

1. Find the last known-good commit SHA.
2. Use the matching image:

```text
ghcr.io/siddharth0998/zero-to-deploy-api:<known-good-sha>
```

3. Update the Render image tag or trigger the deploy method used by the service.
4. Verify `/health` and `/data`.

Avoid using `latest` for rollback because it moves. Prefer SHA-specific image tags.

## 2 AM Incident Response

This section is deliberately direct. Use it when the monitor says the service is down.

### First five minutes

1. Acknowledge the alert.
2. Open the live health endpoint:

```bash
curl -i --max-time 15 "$LIVE_API_URL/health"
```

3. Open Render dashboard.
4. Check service status, latest deploy, and logs.
5. Check GitHub Actions for the latest commit.
6. Decide whether this is:

- a cold start or free-tier sleep delay
- a bad deploy
- a Render platform issue
- a DNS/TLS/routing issue
- an app crash
- an external monitor false positive

### If `/health` is slow but eventually returns `200`

Likely cause:

- Render free-tier cold start
- temporary platform latency

Actions:

```bash
curl -i "$LIVE_API_URL/health"
curl -i "$LIVE_API_URL/data"
```

Then:

- check whether the monitor recovered
- look at response time trend
- no rollback needed if the service recovers and no deploy happened
- document it as cold start behavior if this is expected on free tier

### If `/health` returns `404`

Likely causes:

- wrong URL
- Render route not attached to a running service
- service name or custom domain mismatch
- bad deploy serving a different app

Actions:

1. Confirm the URL in Render dashboard.
2. Confirm the service is a web service, not a private service.
3. Confirm health check path is `/health`.
4. Confirm the deployed code includes `app/main.py`.
5. Check Render logs for startup messages.

If Render shows `x-render-routing: no-server`, the hostname is not attached to an active Render service. Use the dashboard URL instead of the guessed URL.

### If `/health` returns `5xx`

Likely causes:

- application exception
- dependency mismatch
- startup succeeded but endpoint crashes
- bad environment variable

Actions:

1. Open Render logs.
2. Look for Python tracebacks.
3. Check latest deploy timestamp.
4. If a deploy happened recently, roll back to previous successful deploy.
5. If no deploy happened, restart service once from Render.
6. If restart does not fix it, roll back or redeploy previous known-good commit.

Verification:

```bash
curl -i "$LIVE_API_URL/health"
curl -i "$LIVE_API_URL/data"
```

### If the service will not start

Likely causes:

- Docker image build error
- app import error
- Uvicorn command failure
- wrong port binding
- missing runtime dependency

Actions:

1. Check Render build logs.
2. Check Render runtime logs.
3. Confirm Docker command is:

```text
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

4. Confirm Render has `ENV=production`.
5. Confirm `PORT` is not set to a reserved or incorrect value.
6. Run local Docker build:

```bash
docker build -t zero-to-deploy-api:debug .
docker run --rm -p 8000:8000 zero-to-deploy-api:debug
```

7. If the current release is bad, roll back.

### If GitHub Actions fails

Do not force deployment unless this is a documented emergency.

Common causes:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Ruff failure | formatting/import/style issue | Run `ruff check .`, fix code, push again. |
| Pytest failure | endpoint contract changed | Update code or tests intentionally. |
| Docker build failure | dependency or Dockerfile problem | Build locally, fix Dockerfile or requirements. |
| GHCR push failure | package permission issue | Check workflow `packages: write` permission and repo package settings. |
| Pull request push failure | workflow tried to push image on PR | Current workflow avoids this by pushing only on `main`. |

### If Render deploy fails but current production still works

Render should keep the previous successful deploy serving if the new deploy fails before becoming healthy.

Actions:

1. Confirm current production `/health` is healthy.
2. Do not restart production unless necessary.
3. Investigate failed build/startup logs.
4. Fix forward with a new commit.
5. Confirm CI and Render pass.

### If external monitor reports down but manual curl works

Likely causes:

- monitor region issue
- monitor timeout too aggressive
- transient Render cold start
- monitor configured to wrong URL
- monitor expects wrong keyword

Actions:

1. Check monitor URL exactly.
2. Confirm it points to `/health`.
3. Confirm expected status is `200`.
4. Confirm expected keyword is `healthy`.
5. Check monitor incident details.
6. If manual checks from multiple networks pass, mark as monitor false positive.

## Deployment Configuration Checklist

Render service should have:

- type: Web Service
- runtime/language: Docker
- branch: `main`, if building from GitHub
- health check path: `/health`
- environment variable: `ENV=production`
- auto-deploy: enabled if using GitHub source deploys
- HTTPS: enabled automatically by Render
- custom domain: optional
- persistent disk: not needed

GitHub repository should have:

- public repository for free GHCR visibility
- GitHub Actions enabled
- package permissions allowing GHCR publish
- branch protection recommended for `main`
- CI badge in README

External monitor should have:

- URL: `https://siddharth-todo-api.onrender.com/health`
- expected status: `200`
- expected keyword: `healthy`
- alert contact: email or Slack webhook
- interval: 5 minutes or better

## Logs

Application logs go to stdout and are collected by Render.

Example structured log:

```json
{"time":"2026-05-12 12:00:00,000", "level":"INFO", "msg":"Data endpoint accessed"}
```

Important log patterns:

| Pattern | Meaning |
| --- | --- |
| `Application startup complete` | Uvicorn started successfully. |
| `Data endpoint accessed` | `/data` endpoint was called. |
| Python traceback | Application error. |
| Port binding error | App did not bind to the expected host/port. |
| Dependency import error | Missing or incompatible package. |

During an incident, capture:

- timestamp
- endpoint tested
- HTTP status
- Render deploy ID or commit SHA
- relevant log lines
- action taken
- verification result

## Health Monitor Setup

Recommended free setup with UptimeRobot:

1. Create an account.
2. Add a new monitor.
3. Choose HTTP(s).
4. URL:

```text
https://siddharth-todo-api.onrender.com/health
```

5. Monitoring interval: 5 minutes.
6. Alert contacts: email or Slack webhook.
7. Optional keyword check: `healthy`.
8. Save.
9. Wait for first successful check.
10. Take a screenshot for the case deliverable.

Better Stack or Healthchecks.io can be used similarly.

## Incident Severity

| Severity | Definition | Example | Response |
| --- | --- | --- | --- |
| SEV1 | API unavailable for all users | `/health` down, Render service down | Immediate rollback/restart, notify stakeholders. |
| SEV2 | Major endpoint broken | `/health` OK, `/data` failing | Roll back if recent deploy caused it. |
| SEV3 | Degraded but usable | slow responses, cold starts | Monitor, optimize, upgrade if needed. |
| SEV4 | Non-production issue | README typo, CI badge stale | Fix during normal hours. |

## Communication Template

Use this for an incident update:

```text
Status: Investigating
Service: Zero-to-Deploy API
Impact: <what users see>
Started: <timestamp and timezone>
Current finding: <latest known fact>
Action underway: <rollback/restart/investigation>
Next update: <time>
```

Resolution update:

```text
Status: Resolved
Service: Zero-to-Deploy API
Impact: <what happened>
Root cause: <short explanation>
Fix: <rollback/revert/config change>
Verified by: /health, /data, Render, uptime monitor
Follow-up: <ticket or action item>
```

## Post-Incident Review

Write a short review for any SEV1 or SEV2.

Include:

- timeline
- customer or team impact
- root cause
- detection method
- what worked
- what slowed response
- action items

Good action items:

- add a regression test
- improve health check coverage
- add request IDs
- make deploys more automated
- document a missing dashboard link
- pin or update dependencies

Poor action items:

- "be more careful"
- "restart faster"
- "watch logs more"

## Common Maintenance Tasks

### Update dependencies

```bash
source .venv/bin/activate
pip install --upgrade fastapi uvicorn
pytest -q
ruff check .
docker build -t zero-to-deploy-api:local .
```

Then pin updated versions in `requirements.txt` or `requirements-dev.txt`.

### Change the health version

Current version is hardcoded in `app/main.py`.

For a better production setup, derive it from:

- Git tag
- commit SHA
- environment variable set by CI
- package version

### Add a new endpoint

1. Add endpoint in `app/main.py`.
2. Add tests in `tests/test_api.py` or a new test file.
3. Run:

```bash
ruff check .
pytest -q
docker build -t zero-to-deploy-api:local .
```

4. Push and watch CI.
5. Verify production after deploy.

## Backpressure and Failure Behavior

The current API is stateless and has no queue, database, or external dependency. That makes failure handling simple:

- requests are safe to retry
- no write idempotency problem exists yet
- no background jobs need draining
- no database migration rollback exists yet

If the API later accepts writes or calls other services, add:

- request timeouts
- retry budget
- idempotency keys for writes
- rate limiting
- circuit breaker or graceful degradation
- database migration playbook
- separate liveness and readiness checks

## Security Notes

Current state:

- no secrets in the repo
- no `.env` committed
- app runs as non-root inside the container
- HTTPS is terminated by Render
- dependencies are pinned

Recommended next steps:

- add Dependabot or similar dependency alerts
- add image vulnerability scanning
- add branch protection for `main`
- restrict GHCR write access
- add authentication if `/data` becomes sensitive

## Blue/Green or Canary Option

Not implemented in this repository yet.

Simple blue/green design:

1. Create two Render services:

```text
zero-to-deploy-api-blue
zero-to-deploy-api-green
```

2. Both run the same image but can point to different tags.
3. Put Cloudflare or a tiny routing layer in front.
4. Route 100 percent of traffic to blue.
5. Deploy new version to green.
6. Verify green `/health` and `/data`.
7. Shift traffic to green.
8. Keep blue warm for rollback.

Rollback:

- point traffic back to blue
- investigate green offline

Canary design:

- route 5 percent of traffic to green
- compare health, errors, and latency
- increase to 25, 50, then 100 percent if healthy

## L1/L2 Support Agent Stretch Goal

Not implemented yet.

Suggested design for a small local SLM agent running within a 4 GB vCPU environment:

- L1 agent watches uptime monitor alerts, Render deploy status, and `/health`.
- L1 agent posts first response to Slack with service, status, and likely cause.
- L1 agent can run read-only diagnostics:
  - latest GitHub Actions status
  - latest Render deploy status
  - current `/health` response
  - recent log snippets if API access is configured
- L2 agent performs deeper triage:
  - compare latest commit with last known-good commit
  - suggest rollback path
  - draft incident update
  - create follow-up issue

Guardrails:

- read-only by default
- no production changes without human approval
- no secret exposure in Slack
- all actions logged

## Known Gaps Before Final Case Submission

1. Confirm external uptime monitor is live and capture screenshot or link.
2. Confirm Render health check path is `/health`.
3. Confirm the deployment mode: GitHub source deploy or GHCR image deploy.
4. Add a deploy hook if GHCR image deploys need to be automatic.
5. Record the walkthrough video.
6. Consider deriving version from Git SHA instead of hardcoding `1.0.0`.
7. Add request-level logs if this becomes more than a prototype.

## Quick Reference

Local checks:

```bash
ruff check .
pytest -q
docker build -t zero-to-deploy-api:local .
```

Production checks:

```bash
curl -i "$LIVE_API_URL/health"
curl -i "$LIVE_API_URL/"
curl -i "$LIVE_API_URL/data"
```

Docker run:

```bash
docker run --rm -p 8000:8000 zero-to-deploy-api:local
```

Render-style Docker run:

```bash
docker run --rm -e PORT=10000 -p 10000:10000 zero-to-deploy-api:local
```

Last-resort rollback:

```bash
git revert <bad-commit-sha>
git push origin main
```
