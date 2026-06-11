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
6. Upload `sample_input.in` and `sample_good_nve.log` from `sample_data` for Lab 3.
7. Run validation and confirm thermo plots, interpretation notes, and validation checks appear.
8. Save a student interpretation and submit the package.

## Instructor Flow

1. Sign in as `instructor@example.edu` or `ta@example.edu`.
2. Open Instructor Overview.
3. Confirm assignment analytics, needs-attention rows, and roster readiness appear.
4. Open Course Setup.
5. Confirm seeded assignments are editable and roster rows are visible.
6. Create or edit a test assignment, then confirm it appears in the student assignment list if its status is `published`.
7. Add one test student or import a small CSV with `full_name,email,section`.
8. Open Instructor Review.
9. Use the assignment, submission status, validation status, grade state, and search filters.
10. Select the submitted Lab 3 package.
11. Confirm assignment-aware evidence, thermo plots, interpretation notes, files, and student interpretation are visible.
12. Enter rubric scores and save a grade.
13. Confirm the grade-save message appears beside the rubric form.
14. Download `gradebook.csv` and confirm the submission row includes validation, section, and grade values.

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
- Canvas, TA assignment, and richer AI-disclosure analytics remain future work.
