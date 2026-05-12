# Zero-to-Deploy API

[![CI Pipeline](https://github.com/siddharth0998/zero-to-deploy-api/actions/workflows/main.yml/badge.svg)](https://github.com/siddharth0998/zero-to-deploy-api/actions/workflows/main.yml)

Production-ready FastAPI service for **Case 5 - Zero-to-Deploy: Ship a Service Like You Mean It**.

The goal of this project is intentionally simple: take a tiny prototype API and make it operationally credible. That means the repository includes a container image, a CI pipeline, health checks, structured logs, deployment guidance, rollback guidance, and an incident runbook.

## Project Status

| Area | Status | Evidence |
| --- | --- | --- |
| API service | Implemented | `app/main.py` exposes `/`, `/data`, and `/health`. |
| Containerization | Implemented | Multi-stage `Dockerfile`, non-root runtime user, slim Python base image. |
| CI pipeline | Implemented | GitHub Actions lints, tests, builds Docker image, and pushes to GHCR on `main`. |
| Registry | Implemented | Image tags are published to `ghcr.io/siddharth0998/zero-to-deploy-api`. |
| Render deployment | Live | `https://siddharth-todo-api.onrender.com` is documented below. |
| HTTPS | Covered by Render | Render web services provide managed TLS for `*.onrender.com` and custom domains. |
| Health check | Implemented | `GET /health` returns service status, version, and environment. |
| Structured logging | Implemented, basic | Logs are emitted to stdout in JSON-shaped format. |
| External uptime monitor | Required external setup | Configure UptimeRobot, Better Stack, or Healthchecks.io against `/health`. |
| Runbook | Implemented | See `RUNBOOK.md`. |
| Walkthrough video | Not stored in repo | Record the flow described in the walkthrough section. |

## Live Service

Live Render URL:

```text
https://siddharth-todo-api.onrender.com
```

Suggested verification commands:

```bash
export LIVE_API_URL="https://siddharth-todo-api.onrender.com"

curl -i "$LIVE_API_URL/"
curl -i "$LIVE_API_URL/data"
curl -i "$LIVE_API_URL/health"
```

## Repository

- GitHub: <https://github.com/siddharth0998/zero-to-deploy-api>
- Container image: `ghcr.io/siddharth0998/zero-to-deploy-api`
- CI workflow: `.github/workflows/main.yml`
- Runtime app: `app/main.py`
- Operational runbook: `RUNBOOK.md`

## Why FastAPI?

The case allows either Flask or Node. This implementation uses **FastAPI** because it is small enough for a prototype but production-friendly for an API:

- automatic JSON responses
- simple endpoint declarations
- automatic OpenAPI docs
- first-class testing support through `TestClient`
- clean deployment with `uvicorn`

For this case, the application intentionally stays small. The engineering work is focused on making deployment, monitoring, rollback, and support behavior clear.

## Architecture

```text
Developer
   |
   | git push / pull request
   v
GitHub Repository
   |
   | GitHub Actions
   | - install dependencies
   | - lint with ruff
   | - test with pytest
   | - build Docker image
   | - push image to GHCR on main
   v
GitHub Container Registry
   |
   | Render deployment
   v
Render Web Service
   |
   | HTTPS
   v
API Consumers

External uptime monitor checks:
   GET /health
```

## API Endpoints

### `GET /`

Basic service landing endpoint.

Example:

```bash
curl http://localhost:8000/
```

Response:

```json
{
  "message": "Welcome to the Internal API",
  "status": "active"
}
```

### `GET /data`

Prototype data endpoint.

Example:

```bash
curl http://localhost:8000/data
```

Response:

```json
{
  "items": ["unit_01", "unit_02"],
  "authorized": true
}
```

### `GET /health`

Health endpoint for Render health checks and the external uptime monitor.

Example:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "dev"
}
```

Health check contract:

- HTTP status `200` means the API process is alive and ready for traffic.
- `status` should be `healthy` for normal operation.
- `version` should change when the deployed application version changes.
- `environment` is read from the `ENV` environment variable and defaults to `dev`.

## Local Development

### Prerequisites

- Python 3.11 or newer
- Docker Desktop or Docker Engine
- Git

### Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Run the API locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:

- API root: <http://localhost:8000/>
- Health check: <http://localhost:8000/health>
- OpenAPI schema: <http://localhost:8000/openapi.json>
- Swagger UI: <http://localhost:8000/docs>

### Run lint and tests

```bash
ruff check .
pytest -q
```

Expected result:

```text
All checks passed!
3 passed
```

## Docker

The `Dockerfile` uses two stages:

1. `builder`: installs pinned Python runtime dependencies into `/install`.
2. `runner`: copies installed dependencies and app code into a slim runtime image.

Runtime hardening choices:

- uses `python:3.11-slim`
- does not run as root
- copies only application code and installed dependencies
- uses `.dockerignore` to keep local caches, Git metadata, tests, and docs out of the runtime build context
- binds to `0.0.0.0`
- respects the `PORT` environment variable, with `8000` as the local fallback

Build:

```bash
docker build -t zero-to-deploy-api:local .
```

Run:

```bash
docker run --rm -p 8000:8000 zero-to-deploy-api:local
```

Run using a Render-style dynamic port:

```bash
docker run --rm -e PORT=10000 -p 10000:10000 zero-to-deploy-api:local
```

Verify:

```bash
curl http://localhost:8000/health
```

## CI/CD

CI is defined in `.github/workflows/main.yml`.

Triggers:

- push to `main`
- pull request targeting `main`

Pipeline steps:

1. Check out the repository.
2. Install Python 3.11.
3. Install dependencies from `requirements-dev.txt`.
4. Run `ruff check .`.
5. Run `pytest -q`.
6. Set up Docker Buildx.
7. Log in to GitHub Container Registry on `main` pushes.
8. Build the Docker image.
9. Push image tags to GHCR on `main` pushes only.

Image tags:

```text
ghcr.io/siddharth0998/zero-to-deploy-api:latest
ghcr.io/siddharth0998/zero-to-deploy-api:<git-sha>
```

Pull requests build the image but do not push it. This keeps PR validation useful while avoiding registry writes from pull request events.

## Render Deployment

This project can be deployed to Render in either of two ways.

### Option A - Build from the GitHub repository

This is the simplest setup for the case.

1. Create a new Render **Web Service**.
2. Connect the GitHub repository.
3. Choose the `main` branch.
4. Set the runtime/language to **Docker**.
5. Use the repository `Dockerfile`.
6. Set health check path to:

```text
/health
```

7. Add environment variables:

| Key | Value | Notes |
| --- | --- | --- |
| `ENV` | `production` | Used by `/health`. |

8. Keep auto-deploy enabled after CI passes, if configured in Render.
9. Deploy.

Render web services provide HTTPS automatically for `onrender.com` domains. For a custom domain, add the domain in Render and point DNS as instructed by Render.

### Option B - Deploy the GHCR image

Use this if you want Render to pull the CI-built image instead of building from source.

1. Ensure the GHCR package is public, or configure registry credentials in Render.
2. Create a Render service from an existing Docker image.
3. Image:

```text
ghcr.io/siddharth0998/zero-to-deploy-api:latest
```

4. Set `ENV=production`.
5. Set health check path to `/health`.
6. Add the Render deploy hook URL to GitHub Actions as `RENDER_DEPLOY_HOOK_URL`.
7. Push to `main`; GitHub Actions will build, push, and trigger Render automatically.

This repository uses the deploy-hook approach for image-backed Render services. After the image is pushed to GHCR, GitHub Actions calls the Render deploy hook with the exact commit-SHA image tag. That keeps production tied to an immutable build instead of relying only on the moving `latest` tag.

To configure the secret:

1. In Render, open `siddharth-todo-api`.
2. Go to **Settings**.
3. Copy the **Deploy Hook URL**.
4. In GitHub, open the repository settings.
5. Go to **Secrets and variables** > **Actions**.
6. Add a repository secret named:

```text
RENDER_DEPLOY_HOOK_URL
```

7. Paste the Render deploy hook URL as the secret value.

Do not commit the deploy hook URL to the repository. Treat it like a secret because anyone with the URL can trigger a deploy.

## External Uptime Monitor

Use one free-tier monitor such as UptimeRobot, Better Stack, or Healthchecks.io.

Recommended monitor:

| Setting | Value |
| --- | --- |
| Monitor type | HTTPS keyword or HTTP status monitor |
| URL | `https://siddharth-todo-api.onrender.com/health` |
| Expected status | `200` |
| Expected keyword | `healthy` |
| Check interval | 5 minutes on free tier |
| Alert contact | your email or Slack webhook |

Why monitor `/health` instead of `/`:

- `/health` is intentionally stable.
- It gives environment and version context.
- It is the endpoint Render should also use for readiness.

## Structured Logging

The service logs to stdout. Render collects stdout and stderr automatically.

Current log format:

```json
{"time":"2026-05-12 12:00:00,000", "level":"INFO", "msg":"Data endpoint accessed"}
```

The `/data` endpoint emits an info log when accessed.

For a larger production service, the next logging improvements would be:

- request ID or trace ID
- HTTP method and path
- latency
- response status
- client IP or forwarded IP
- JSON escaping through a structured logging library instead of a string formatter

## Secrets and Configuration

No secrets are required for the current API.

Rules for future secrets:

- do not commit `.env` files
- store production secrets in Render environment variables or secret files
- store CI secrets in GitHub Actions secrets
- prefer short-lived tokens where possible
- rotate any exposed token immediately

Current environment variables:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `ENV` | No | `dev` | Displayed by `/health`. |
| `PORT` | No | `8000` | Used by Docker command. Render sets this for web services. |

## Operational Behavior

Expected normal behavior:

- `/health` returns `200` and `status=healthy`.
- Render service logs show Uvicorn startup and normal request logs.
- GitHub Actions is green on `main`.
- GHCR has `latest` and SHA-specific image tags.
- External monitor reports uptime.

Expected free-tier behavior:

- Render free-tier services may sleep after inactivity.
- First request after sleep can be slow.
- A cold start should not be treated as an incident unless the service fails to recover.

## Rollback Summary

See `RUNBOOK.md` for detailed steps.

Fast rollback options:

- Render dashboard: rollback to the previous successful deploy.
- Git revert: revert the bad commit, push to `main`, let CI and Render deploy.
- GHCR image deploy: redeploy a previous SHA image tag.

Always verify after rollback:

```bash
curl -i "$LIVE_API_URL/health"
curl -i "$LIVE_API_URL/data"
```

## Cost Estimate at 100x Traffic

Current traffic is assumed to be small prototype traffic.

At 100x current traffic, the first bottleneck is likely the free Render instance limits rather than the API code itself. The service is stateless and lightweight, so scaling is straightforward.

Rough estimate:

| Item | Current | 100x likely path |
| --- | --- | --- |
| Hosting | Render free web service | Upgrade to a paid Render instance or multiple instances. |
| Registry | GHCR free for public package | Still likely fine for this project. |
| Monitoring | Free uptime monitor | Still likely fine unless shorter intervals or incident tooling are needed. |
| Database | None | Add managed database only if the API becomes stateful. |
| Logging | Render logs | Add log retention/export if debugging volume grows. |

First optimization:

- Add response caching or CDN only if `/data` becomes expensive.
- Before optimizing, add request/latency metrics so the team can see whether CPU, memory, cold starts, or upstream latency is the real issue.

## Stretch Goal Notes

Not implemented yet:

- blue/green or canary deploy strategy
- Slack-based L1/L2 support agent
- full request/response observability
- authenticated endpoints
- database or persistent storage

Reasonable next stretch implementation:

- add a `DEPLOY_COLOR=blue|green` or `CANARY_PERCENT` flag
- deploy two Render services, for example `zero-to-deploy-api-blue` and `zero-to-deploy-api-green`
- use Cloudflare or a small gateway to route traffic between them
- keep `/health` on both services
- rollback by routing traffic back to the previous color

## Remaining Work

The service now covers the core case deliverables, but these items should be completed or confirmed before final submission:

1. Confirm the Render health check path is set to `/health`.
2. Add the external uptime monitor link or screenshot for evidence.
3. Record the walkthrough video.
4. Add the `RENDER_DEPLOY_HOOK_URL` GitHub Actions secret if it is not already configured.
5. Consider stronger structured logging with request IDs and real JSON serialization.
6. Consider versioning from Git SHA or release tag instead of the hardcoded `1.0.0`.

## References

- Render web services: <https://render.com/docs/web-services>
- Render Docker deployments: <https://render.com/docs/docker>
- Render health checks: <https://render.com/docs/health-checks>
- Render environment variables: <https://render.com/docs/environment-variables>
- GitHub Actions: <https://docs.github.com/actions>
- GitHub Container Registry: <https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry>
