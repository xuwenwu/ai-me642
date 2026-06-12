# Phase II Pilot Readiness

Use this checklist when reviewing the app for a small real-class pilot.

## Student Flow

1. Sign in as `student@example.edu`.
2. Open Dashboard and confirm three labs appear:
   - Lab 1: LAMMPS Setup and Equilibration
   - Lab 2: NVT Temperature Control
   - Lab 3: NVE Energy Conservation and Timestep Stability
3. Open Submission Workflow.
4. Create one submission for each lab.
5. Confirm each selected lab shows its validation profile, required evidence, optional evidence, and reflection cues.
6. Open AI Prompt Logs and confirm the course AI policy, allowed tools, disclosure checklist, and prompt templates appear.
7. Choose a template, save a prompt log connected to Lab 3, and confirm it appears in Recorded Logs.
8. Upload `sample_input.in`, `sample_good_nve.log`, `sample_slurm.sbatch`, `sample_analysis.py`, and `sample_ovito.py` from `sample_data` for Lab 3.
9. Optionally upload `sample_warning.log` as a second `lammps_log` to review multi-log comparison.
10. Run validation and confirm thermo plots, interpretation notes, validation checks, and the AI Disclosure cue appear.
11. Confirm Phase VI checks appear for LAMMPS input structure, Slurm directives/resources/launch safety, Python analysis structure/safety, OVITO script structure/safety, and multi-log comparison when two logs are present.
12. Save a student interpretation and submit the package.

## Instructor Flow

1. Sign in as `instructor@example.edu` or `ta@example.edu`.
2. Open Instructor Overview.
3. Confirm assignment analytics, needs-attention rows, and roster readiness appear.
4. Open Course Setup.
5. Confirm seeded assignments are editable and roster rows are visible.
6. Confirm the AI policy and prompt templates can be edited.
7. Confirm the Course Assistant is disabled by default, then enable offline mode for a test prompt if reviewing Phase X.
8. Create or edit a test assignment, then confirm it appears in the student assignment list if its status is `published`.
9. Add one test student, import a small CSV with `full_name,email,section`, and download `roster_export.csv`.
10. Open Instructor Review.
11. Use the assignment, submission status, validation status, grade state, and search filters.
12. Select the submitted Lab 3 package.
13. Confirm assignment-aware evidence, thermo plots, interpretation notes, files, and student interpretation are visible.
14. Enter rubric scores and save a grade.
15. Confirm the grade-save message appears beside the rubric form.
16. Open Gradebook Dashboard.
17. Confirm course totals, assignment operations, and student gradebook rows appear.
18. Download `course_gradebook.csv` and confirm missing/submitted/graded cells are included.
19. Download `canvas_gradebook_import.csv` and confirm it has one row per student with Canvas identity columns and assignment score columns.
20. Download `lms_submission_detail.csv` and confirm it includes student, section, assignment, score, status, validation status, submitted time, and feedback fields.

## Backend Checks

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\reset_demo_data.py
.\.venv\Scripts\python.exe -m pytest
```

## Deployment Checks

1. Confirm `.github/workflows/ci.yml` exists.
2. Confirm `.env.production.example` includes `APP_ENV=production`, `SEED_DEMO_DATA=false`, and non-wildcard `CORS_ORIGINS`.
3. Read `docs/DEPLOYMENT.md`.
4. Read `docs/SECURITY_CHECKLIST.md`.
5. For a local backup dry run, use:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\backup_local_data.py
```

## Frontend Checks

```powershell
cd frontend
npm run typecheck
npm run build
```

## Pilot Limits

- The app does not run uploaded simulation code.
- Automated validation is advisory evidence, not a grade.
- No live LLM calls are made unless both instructor policy and server environment explicitly enable an external provider.
- AI-disclosure analytics flag missing or thin evidence but do not score students automatically.
- Phase VI validation statically inspects uploaded scripts; it does not execute LAMMPS, Python, OVITO, or Slurm.
- Canvas export is a CSV handoff, not a live Canvas API integration.
- Production deployment still requires instructor-controlled hosting, HTTPS, backups, and real course secrets.
- Controlled AI external provider mode still requires institutional/privacy review and API billing ownership.
