# AI-ME642 Responsible Scientific Computing Studio

AI-ME642 is a pilot-ready rebuild of the ME642 Materials Modeling Studio. It is a local-first teaching platform for responsible AI-assisted scientific computing in molecular dynamics coursework.

The core evidence chain is:

```text
scientific specification -> AI prompt log -> simulation artifacts -> validation report -> student interpretation -> instructor grading -> reproducible ZIP package
```

The current pilot supports configurable assignment workflows with assignment-specific validation profiles, reflection prompts, responsible-AI policy/templates, roster setup, instructor analytics, and grading.

## What This MVP Does

- Seeded login for student, TA, and instructor roles.
- One ME642 course, three seeded demo lab assignments, and instructor assignment authoring.
- Student project specification capture.
- AI prompt-log disclosure with accepted/rejected/manual-edit fields, course policy guidance, and reusable prompt templates.
- Submission creation, artifact upload, validation, interpretation, and submission.
- LAMMPS log parsing for thermo output, warnings, errors, completion, and final values.
- Assignment-aware validation profiles for basic LAMMPS health, NVT temperature control, and NVE energy conservation.
- Static LAMMPS input linting plus Slurm, Python analysis, and OVITO artifact checks without executing uploaded code.
- Multi-log comparison when a submission includes more than one LAMMPS log.
- Thermo plots for temperature, total energy, pressure, and volume when LAMMPS log columns are present.
- Student reflection cues tied to each assignment.
- Instructor/TA course setup, responsible-AI policy/template editing, roster import, overview analytics, roster readiness, submission queue filters, evidence review, and rubric grading.
- AI-disclosure quality indicators for missing or thin prompt evidence.
- CSV gradebook export.
- Filter-aware gradebook export for instructor queues.
- Reproducible ZIP package export.

## What This MVP Does Not Do

- It does not call a live LLM.
- It does not run uploaded LAMMPS, Python, or shell code.
- It does not execute uploaded OVITO scripts or Slurm jobs.
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

For a fresh local database, the reset script is still the fastest path. For migration-aware environments, Alembic is now configured:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

## Frontend

```powershell
cd frontend
npm install
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000/api"
npm run dev -- --hostname 127.0.0.1 --port 3000
```

The frontend serves `http://127.0.0.1:3000`.

Using `127.0.0.1` for both services avoids local IPv4/IPv6 `localhost` resolution mismatches during development.

## Phone Or LAN Testing

If your phone and workstation are on the same network, start the servers on all network interfaces and replace `<WORKSTATION_IP>` with the workstation IPv4 address:

```powershell
cd backend
$env:CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://<WORKSTATION_IP>:3000"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```powershell
cd frontend
$env:NEXT_PUBLIC_API_URL="http://<WORKSTATION_IP>:8000/api"
npm run dev -- --hostname 0.0.0.0 --port 3000
```

Then open `http://<WORKSTATION_IP>:3000/login` on your phone. If the page does not load, check that the phone is on the same network and that Windows Firewall allows Python/Node on ports `8000` and `3000`.

If your phone is not on the same network, use a temporary tunnel to the frontend. The frontend proxies `/api` to the local backend, so only one public URL is needed:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
$env:BACKEND_PROXY_URL="http://127.0.0.1:8000"
npm run dev -- --hostname 127.0.0.1 --port 3000
```

In another frontend terminal:

```powershell
npx --yes localtunnel --port 3000
```

Open the printed `https://...loca.lt` URL on your phone.

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
pytest
```

## Reset Local Demo Data

Use this only for local development when you want a clean seeded database and empty upload/generated folders:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\reset_demo_data.py
```

The reset script refuses non-SQLite databases and only removes local ignored data under `backend/`.

## Smoke Test

Follow `docs/SMOKE_TEST.md` to verify the student and instructor workflow before commits or larger changes.

For pilot review, also use `docs/PILOT_READINESS.md`.

## Design Principle

AI assistance is allowed only when it leaves an inspectable trail. Simulation results are accepted only when paired with reproducible artifacts and scientific interpretation. Instructors and TAs remain responsible for final judgment.
