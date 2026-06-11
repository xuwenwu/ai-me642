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
8. Upload `sample_input.in` and `sample_good_nve.log` from `sample_data` for Lab 3.
9. Run validation and confirm thermo plots, interpretation notes, validation checks, and the AI Disclosure cue appear.
10. Save a student interpretation and submit the package.

## Instructor Flow

1. Sign in as `instructor@example.edu` or `ta@example.edu`.
2. Open Instructor Overview.
3. Confirm assignment analytics, needs-attention rows, and roster readiness appear.
4. Open Course Setup.
5. Confirm seeded assignments are editable and roster rows are visible.
6. Confirm the AI policy and prompt templates can be edited.
7. Create or edit a test assignment, then confirm it appears in the student assignment list if its status is `published`.
8. Add one test student or import a small CSV with `full_name,email,section`.
9. Open Instructor Review.
10. Use the assignment, submission status, validation status, grade state, and search filters.
11. Select the submitted Lab 3 package.
12. Confirm assignment-aware evidence, thermo plots, interpretation notes, files, and student interpretation are visible.
13. Enter rubric scores and save a grade.
14. Confirm the grade-save message appears beside the rubric form.
15. Download `gradebook.csv` and confirm the submission row includes validation, section, and grade values.

## Backend Checks

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\reset_demo_data.py
.\.venv\Scripts\python.exe -m pytest
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
- No live LLM calls are made.
- AI-disclosure analytics flag missing or thin evidence but do not score students automatically.
- Canvas, TA assignment, and richer scientific validation remain future work.
