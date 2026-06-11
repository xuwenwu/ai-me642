# AI-ME642 Responsible Scientific Computing Studio

AI-ME642 is a clean Phase I-plus rebuild of the ME642 Materials Modeling Studio. It is a local-first teaching platform for responsible AI-assisted scientific computing in molecular dynamics coursework.

The core evidence chain is:

```text
scientific specification -> AI prompt log -> simulation artifacts -> validation report -> student interpretation -> instructor grading -> reproducible ZIP package
```

The Phase I-plus rebuild focuses on one complete assignment workflow: **Lab 3: NVE Energy Conservation and Timestep Stability**.

## What This MVP Does

- Seeded login for student, TA, and instructor roles.
- One ME642 course and one Lab 3 assignment with a rubric.
- Student project specification capture.
- AI prompt-log disclosure with accepted/rejected/manual-edit fields.
- Submission creation, artifact upload, validation, interpretation, and submission.
- LAMMPS log parsing for thermo output, warnings, errors, completion, and final values.
- Conservative validation checks for completeness, log health, temperature, energy drift, pressure, volume, and step monotonicity.
- Instructor/TA submission review and rubric grading.
- CSV gradebook export.
- Reproducible ZIP package export.

## What This MVP Does Not Do

- It does not call a live LLM.
- It does not run uploaded LAMMPS, Python, or shell code.
- It does not submit HPC jobs.
- It does not integrate with Canvas yet.
- It does not treat automated validation as a grade.

## Seed Accounts

All seed users use password `password123`.

| Email | Role |
| --- | --- |
| `student@example.edu` | student |
| `student2@example.edu` | student |
| `ta@example.edu` | ta |
| `instructor@example.edu` | instructor |

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend serves `http://127.0.0.1:8000/api`.

## Frontend

```powershell
cd frontend
npm install
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000/api"
npm run dev -- --hostname 127.0.0.1 --port 3000
```

The frontend serves `http://127.0.0.1:3000`.

Using `127.0.0.1` for both services avoids local IPv4/IPv6 `localhost` resolution mismatches during development.

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
pytest
```

## Smoke Test

Follow `docs/SMOKE_TEST.md` to verify the student and instructor workflow before commits or larger changes.

## Design Principle

AI assistance is allowed only when it leaves an inspectable trail. Simulation results are accepted only when paired with reproducible artifacts and scientific interpretation. Instructors and TAs remain responsible for final judgment.
