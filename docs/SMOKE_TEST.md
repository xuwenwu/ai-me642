# Local Smoke Test

Use this checklist after setup, after major changes, or before making a commit. It verifies the Phase II pilot evidence chain without requiring external services.

The automated API version of this workflow is `backend/app/tests/test_workflow_smoke.py`. Run it with:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest app\tests\test_workflow_smoke.py
```

## Start The App

Run these commands from the repository root in two separate terminals.

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
cd frontend
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000/api"
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open `http://127.0.0.1:3000/login`.

## Student Workflow

This checklist is easiest against a fresh local database. If this student already has a Lab 3 submission, reuse the existing submission or run the local reset script before repeating the create-submission step:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\reset_demo_data.py
```

Log in with:

- Email: `student@example.edu`
- Password: `password123`

Expected:

- Dashboard loads.
- The three pilot lab assignments are visible.
- The user does not see the instructor navigation link.

Create a project specification:

- Open Project Spec.
- Fill or accept the default Lab 3 fields.
- Save the specification.

Expected:

- A saved project specification message appears.

Create an AI prompt log:

- Open Prompt Logs.
- Select the Lab 3 assignment.
- Select the project specification.
- Fill prompt text, output summary, accepted/rejected parts, manual edits, validation performed, and remaining concerns.
- Save the prompt log.

Expected:

- The new prompt log appears under Recorded Logs.

Create a submission:

- Open Submission.
- Select the Lab 3 assignment.
- Select the project specification.
- Create the submission.

Expected:

- A draft submission appears.

Upload sample artifacts:

- Upload `sample_data/sample_input.in` as `lammps_input`.
- Upload `sample_data/sample_good_nve.log` as `lammps_log`.
- Upload `sample_data/sample_slurm.sbatch` as `slurm_script`.
- Upload `sample_data/sample_analysis.py` as `python_analysis`.
- Upload `sample_data/sample_ovito.py` as `ovito_script`.
- Optional: upload `sample_data/sample_warning.log` as a second `lammps_log` to review multi-log comparison.

Expected:

- The file table lists the uploaded sample files.

Run validation:

- Click Run validation.

Expected:

- Latest validation is `warning`.
- Required LAMMPS input and log checks pass.
- Log health, LAMMPS input lint, thermo data, run completion, step monotonicity, temperature sanity, energy drift, and volume checks pass.
- Slurm, Python analysis, and OVITO script static checks appear when those artifacts are uploaded.
- Multi-log comparison appears when two or more LAMMPS logs are uploaded.
- Thermo plots appear for available columns such as temperature, total energy, pressure, and volume.
- Optional README or analysis-artifact checks may warn.
- Pressure is marked for review.

Complete the student submission:

- Write a short interpretation that mentions energy drift, pressure review, and advisory validation.
- Save interpretation.
- Download the ZIP package.
- Submit assignment.

Expected:

- Submission status changes to `submitted`.
- The ZIP contains:
  - `README.md`
  - `metadata.json`
  - `prompt_logs.json`
  - `validation_report.json`
  - `artifacts/lammps_input/sample_input.in`
  - `artifacts/lammps_log/sample_good_nve.log`
  - `artifacts/slurm_script/sample_slurm.sbatch`
  - `artifacts/python_analysis/sample_analysis.py`
  - `artifacts/ovito_script/sample_ovito.py`

## Instructor Workflow

Log out, then log in with:

- Email: `instructor@example.edu`
- Password: `password123`

Expected:

- Dashboard loads.
- The instructor navigation link is visible.

Open Instructor Review:

- Select the submitted Lab 3 package.
- Review the files, validation status, and student interpretation.
- Enter rubric scores and feedback.
- Save grade.

Expected:

- A Grade saved message appears.

Download gradebook:

- Click Download gradebook.

Expected:

- The CSV contains the submitted row with validation status and final score.

Review course operations:

- Open Gradebook Dashboard from Instructor Overview.
- Confirm totals, assignment operations, and student rows appear.
- Download the course CSV.
- Download the Canvas import CSV.
- Download the LMS detail CSV.

Expected:

- The gradebook dashboard includes missing/submitted/graded counts.
- The course CSV includes one row per student with assignment status and score columns.
- The Canvas import CSV includes Student, SIS User ID, SIS Login ID, Section, and one score column per assignment.
- The LMS detail CSV includes Student, SIS User ID, Section, Assignment, Points Possible, Score, Submission Status, Validation Status, Submitted At, and Feedback columns.

## Notes

- Automated validation is advisory evidence, not the final course grade.
- The backend never executes uploaded files.
- Local ZIP exports include student name and email for grading context. Redact or avoid sharing them outside the course workflow.
