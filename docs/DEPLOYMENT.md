# Deployment Guide

This project is local-first for development, but Phase XI adds a repeatable private-pilot deployment path. The recommended pilot shape is:

- Next.js frontend exposed through HTTPS.
- FastAPI backend private to the host or container network.
- Frontend `/api` proxy routed to the backend.
- SQLite plus uploads on a backed-up server volume for a small class pilot.
- External AI provider disabled unless approved by the instructor and institution.

## Environments

Use `.env.example` for local development and `.env.production.example` as the production checklist.

Required production choices:

- `APP_ENV=production`
- `SECRET_KEY` set to a strong random value with at least 32 characters.
- `SEED_DEMO_DATA=false`
- `CORS_ORIGINS` set to the real frontend origin, not `*`.
- `UPLOAD_ROOT` set to a backed-up server directory.
- `BACKUP_ROOT` set to a persistent backup directory.
- `DATABASE_URL` set to the production database.
- `AI_PROVIDER_ENABLED=false` unless the course has approved external AI provider use.

The backend refuses to start in production if the default development secret is still present, demo seeding is enabled, or wildcard CORS is configured.

The production example uses server-hosted SQLite because it needs no extra driver for a small private pilot. If you move to PostgreSQL or another managed database, update `DATABASE_URL` and add the matching SQLAlchemy driver to `backend/requirements.txt`.

## Local Deployment Smoke

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\reset_demo_data.py
.\.venv\Scripts\python.exe -m pytest
```

```powershell
cd frontend
npm run typecheck
npm run build
```

## Docker Compose Pilot Stack

Use this for the first stable pilot deployment.

1. Copy the pilot environment template:

```powershell
Copy-Item .env.pilot.example .env.pilot
```

2. Edit `.env.pilot`:

- Replace `SECRET_KEY` with a strong random value.
- Set `CORS_ORIGINS` to the final HTTPS course URL.
- Keep `SEED_DEMO_DATA=false`.
- Keep `AI_PROVIDER_ENABLED=false` unless external AI has been approved.

3. Build and start:

```powershell
.\scripts\pilot-start.ps1 -Port 3000
```

4. Verify local readiness:

```powershell
.\scripts\pilot-status.ps1 -Port 3000
```

5. Put HTTPS in front of `127.0.0.1:3000`. The backend should stay private behind the frontend proxy.

6. Create the first instructor account:

```powershell
docker compose -f docker-compose.pilot.yml exec backend python scripts/create_admin.py --email instructor@your.edu --full-name "Course Instructor" --password "replace-with-temporary-password"
```

See `docs/PILOT_OPERATIONS.md` for backups, upgrades, rollback, and incident procedures.

## Hosted HTTPS Stack

For a real class URL, copy `Caddyfile.example` to `Caddyfile`, replace `your-course-domain.example.edu`, and point DNS at the host. Then start the pilot stack with the hosted override:

```powershell
Copy-Item Caddyfile.example Caddyfile
docker compose -f docker-compose.pilot.yml -f docker-compose.hosted.yml --env-file .env.pilot up -d --build
```

The hosted override exposes only Caddy on ports `80` and `443`. The frontend and backend stay inside the Docker network.

## Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\alembic.exe upgrade head
python seed.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For production, run migrations first, then start the server with production environment variables. Do not run the demo reset script against production data.

Readiness endpoint:

```text
GET /api/health/ready
```

Expected successful response:

```json
{"status":"ok","checks":{"database":"ok","upload_root":"ok"}}
```

## Frontend

```powershell
cd frontend
npm ci
$env:NEXT_PUBLIC_API_URL="/api"
$env:BACKEND_PROXY_URL="http://127.0.0.1:8000"
npm run build
npm run start -- --hostname 127.0.0.1 --port 3000
```

Use a reverse proxy or hosting platform to terminate HTTPS and route `/api` to the backend.

## Backups

For local SQLite pilots, create a backup ZIP of the SQLite database and uploaded files:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\backup_local_data.py
```

Backups are written under `backend/data/backups/`, which is ignored by Git.

For the Docker pilot stack, prefer the top-level wrapper because it runs the container backup and copies the ZIP to a host folder:

```powershell
.\scripts\pilot-backup.ps1 -Port 3000
```

For production databases other than SQLite, use the database provider's backup tool and separately back up `UPLOAD_ROOT`.

## Controlled AI

External AI calls are disabled by default. For a controlled pilot, start with offline course guidance. If enabling OpenAI provider mode, set `AI_PROVIDER_ENABLED=true`, `AI_PROVIDER_MODE=openai`, an approved `AI_PROVIDER_MODEL`, and a server-side `OPENAI_API_KEY`. Do not expose the key to the frontend.

## CI

GitHub Actions runs on pull requests and pushes to `main` and `codex/phase-2-pilot-readiness`:

- backend tests with Python 3.12
- frontend typecheck
- frontend production build
- backend and frontend Docker build smoke checks

## Temporary Phone Tunnels

Temporary tunnels such as localhost.run or localtunnel are acceptable only for review. They are not a pilot deployment because the URL can change, the workstation must stay awake, and there is no backup, uptime, or HTTPS domain control beyond the tunnel provider. Use the Compose pilot stack plus an HTTPS reverse proxy for student-facing use.
