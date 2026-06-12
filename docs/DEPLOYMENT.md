# Deployment Guide

This project is still local-first, but Phase VIII adds enough guardrails to prepare a small private pilot deployment.

## Environments

Use `.env.example` for local development and `.env.production.example` as the production checklist.

Required production choices:

- `APP_ENV=production`
- `SECRET_KEY` set to a strong random value with at least 32 characters.
- `SEED_DEMO_DATA=false`
- `CORS_ORIGINS` set to the real frontend origin, not `*`.
- `UPLOAD_ROOT` set to a backed-up server directory.
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

For production databases other than SQLite, use the database provider's backup tool and separately back up `UPLOAD_ROOT`.

## Controlled AI

External AI calls are disabled by default. For a controlled pilot, start with offline course guidance. If enabling OpenAI provider mode, set `AI_PROVIDER_ENABLED=true`, `AI_PROVIDER_MODE=openai`, an approved `AI_PROVIDER_MODEL`, and a server-side `OPENAI_API_KEY`. Do not expose the key to the frontend.

## CI

GitHub Actions runs on pull requests and pushes to `main`:

- backend tests with Python 3.12
- frontend typecheck
- frontend production build
