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
2. Open Instructor Review.
3. Use the assignment, submission status, validation status, grade state, and search filters.
4. Select the submitted Lab 3 package.
5. Confirm assignment-aware evidence, thermo plots, interpretation notes, files, and student interpretation are visible.
6. Enter rubric scores and save a grade.
7. Download `gradebook.csv` and confirm the submission row includes validation and grade values.

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
- Canvas, sections, TA assignment, and cohort analytics remain future work.
