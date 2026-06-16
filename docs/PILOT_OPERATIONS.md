# Pilot Operations Runbook

Use this runbook when the app is deployed for a small private class pilot.

## Pre-Pilot Setup

1. Create the production environment file:

```powershell
Copy-Item .env.pilot.example .env.pilot
```

2. Edit `.env.pilot`:
   - Replace `SECRET_KEY` with a strong random value.
   - Set `CORS_ORIGINS` to the final HTTPS course URL.
   - Keep `SEED_DEMO_DATA=false`.
   - Keep `AI_PROVIDER_ENABLED=false` unless external AI use has been approved.

3. Build and start the pilot stack:

```powershell
.\scripts\pilot-start.ps1 -Port 3000
```

4. Confirm both services are healthy:

```powershell
.\scripts\pilot-status.ps1 -Port 3000
.\scripts\pilot-smoke.ps1 -Port 3000
```

5. Put HTTPS in front of `127.0.0.1:3000` with the hosting provider or reverse proxy. The backend stays private inside the Compose network.

## Account Setup

Seeded demo accounts are not automatically created in production mode. Before students use the site, an instructor-controlled setup step must create or import roster accounts through Course Setup.

Recommended pilot process:

1. Start with one instructor account created by a trusted administrator:

```powershell
docker compose -f docker-compose.pilot.yml exec backend python scripts/create_admin.py --email instructor@your.edu --full-name "Course Instructor" --password "replace-with-temporary-password"
```

2. Sign in as instructor.
3. Import the roster CSV with `full_name,email,section`; `docs/course_pilot/roster_template.csv` includes optional password and account-status columns.
4. Assign temporary passwords through the agreed class communication channel.
5. Ask students to confirm login before the first graded activity.

The current app does not include self-service password reset. Keep a manual password-reset plan for the pilot.

## Daily Checks

Run these checks before each class activity:

```powershell
.\scripts\pilot-status.ps1 -Port 3000
.\scripts\pilot-smoke.ps1 -Port 3000 -InstructorEmail instructor@your.edu -InstructorPassword "temporary-password"
```

Expected readiness response:

```json
{"status":"ok","checks":{"database":"ok","upload_root":"ok"}}
```

Also confirm:

- Students can reach `/login`.
- Instructor can open Course Setup.
- At least one sample submission can run validation.
- Course-facing materials in `docs/course_pilot` have been adapted for the current class.
- Backups completed after the previous class activity.

## Backups

For the Compose pilot, SQLite, uploads, and generated backup ZIP files live in the `ai_me642_data` Docker volume. Take a backup before and after each class activity:

```powershell
.\scripts\pilot-backup.ps1 -Port 3000
```

The script runs the backend backup helper and copies the newest ZIP from the Docker volume to `pilot_backups/`. Store backups outside the deployment host.

## Upgrade Procedure

1. Announce a short maintenance window.
2. Take a backup.
3. Pull or checkout the approved release branch.
4. Rebuild and restart:

```powershell
.\scripts\pilot-start.ps1 -Port 3000
```

5. Check readiness:

```powershell
.\scripts\pilot-status.ps1 -Port 3000
```

6. Smoke test one student login and one instructor review page.

## Rollback Procedure

1. Stop the current stack:

```powershell
.\scripts\pilot-stop.ps1 -Port 3000 -RemoveContainers
```

2. Check out the last known good commit.
3. Restore the latest known good data backup if the upgrade changed data unexpectedly.
4. Rebuild and restart.
5. Run readiness and smoke tests.

## Incident Response

For login failures:

- Check `/api/health/ready`.
- Confirm the frontend is using `/api`.
- Confirm the backend service is healthy in Compose.
- Confirm browser storage is enabled if one user is affected.

For missing uploads:

- Check the `upload_root` readiness result.
- Confirm the Docker volume is mounted.
- Check available disk space on the host.

For validation failures:

- Confirm the uploaded file type and extension are allowed.
- Download the reproducible package and inspect `validation_report.json`.
- Treat automated validation as evidence, not as a final grade.

For suspected privacy or AI-policy issues:

- Disable external AI provider mode.
- Export prompt logs for the affected assignment.
- Preserve the relevant submission package and logs for review.

## Pilot Exit Criteria

At the end of the pilot, export:

- Course gradebook CSV.
- Canvas import CSV if needed.
- LMS submission detail CSV.
- Roster CSV.
- Full data/upload backup ZIP.

Then document:

- Number of active students.
- Number of submissions.
- Validation failure/warning patterns.
- Instructor grading time and pain points.
- Any login, upload, or deployment incidents.

For the class-day checklist, use `docs/LAUNCH_DAY.md`.
