# Security Checklist

Use this before exposing the app beyond a trusted local workstation.

## Required Before A Private Pilot

- Set `APP_ENV=production`.
- Replace `SECRET_KEY=dev-secret-change-me` with a strong private value.
- Set `SEED_DEMO_DATA=false`.
- Keep external AI provider calls disabled unless explicitly approved.
- Store `OPENAI_API_KEY` only as a server-side secret if external AI is enabled.
- Configure `CORS_ORIGINS` to the real frontend origin only.
- Serve the site over HTTPS.
- Store `.env` outside Git and never commit secrets.
- Back up the database and `UPLOAD_ROOT`.
- Confirm `backend/scripts/reset_demo_data.py` is only used on local SQLite demo data.
- Run GitHub Actions or local checks before deploy.

## Current Guardrails

- Uploaded scripts are statically inspected; they are not executed.
- Role checks protect instructor/TA routes.
- Students can access only their own submissions/projects.
- Production startup rejects unsafe demo defaults.
- Basic security headers are added to backend responses.
- Controlled AI provider calls require instructor policy and server environment opt-in.
- External AI calls block prompts with simple private-data flags.

## Known Limits

- Seeded/demo accounts are still intended for local pilots, not public deployment.
- There is no password reset or self-service account management yet.
- Canvas export is CSV handoff only, not a live Canvas API integration.
- Live AI provider calls are disabled by default.
- Privacy checks for AI prompts are advisory and conservative, not a full institutional data-loss-prevention system.
- Production file scanning/virus scanning is not implemented.
