# Phase Plan

## Phase I-Plus: Local Reliable Spine

- One Lab 3 workflow.
- Seeded auth.
- Project specification.
- Prompt log.
- Artifact upload.
- LAMMPS validation.
- Student interpretation.
- Instructor grading.
- Reproducible ZIP export.

## Phase II: Small-Class Pilot Readiness

- Three seeded lab assignments.
- Assignment-specific validation profiles.
- Assignment-specific reflection prompts.
- Student submission workflow that reads assignment requirements.
- Instructor queue filters for assignment, status, validation, grade state, and search.
- Grade summaries on submissions and CSV gradebook export.
- Alembic bootstrap for migration-aware environments.

## Phase III: Instructor Operations and Pilot Analytics

- Instructor overview dashboard.
- Assignment-level submission, validation, grading, and attention counts.
- Needs-attention queue for submitted packages with warnings, missing validation, missing interpretation, or ungraded state.
- Roster/section groundwork for small-class pilots.
- Filter-aware gradebook export.
- Clear grade-save confirmation on the instructor review page.

## Phase IV: Assignment Authoring and Course Setup

- Instructor assignment management page.
- Create and edit title, due date, description, validation profile, status, evidence requirements, validation settings, and reflection prompts.
- Manual student add/update.
- CSV roster import.
- Keep seeded demo assignments while enabling instructor-managed course setup.

## Phase V: Responsible AI Pedagogy and Analytics

- Instructor AI-use policy configuration.
- Prompt templates by task type.
- Student-facing policy, allowed-tool list, disclosure checklist, and template picker on AI Prompt Logs.
- Submission AI-disclosure cue connected to validation evidence.
- Instructor analytics for missing or thin AI disclosure.
- Course Setup controls for policy and template authoring.

## Phase VI: Rich Scientific Validation

- Slurm script linting without execution.
- OVITO/Python artifact metadata checks.
- Static LAMMPS input linting for setup, force-field, thermo, run, and ensemble cues.
- Richer multi-run comparison when multiple LAMMPS logs are uploaded.
- Sample Slurm, Python, and OVITO artifacts for pilot review.

## Phase VII: Course Operations

- Instructor/TA gradebook dashboard.
- Roster-aware gradebook matrix with missing, submitted, graded, validation warning, and average-score summaries.
- Course CSV export that includes missing students and all assignment cells.
- Canvas/LMS handoff CSV export with student, section, assignment, score, status, and feedback fields.
- Gradebook navigation from instructor overview and review queue.

## Phase VIII: Deployment, Security, and CI

- GitHub Actions CI for backend tests and frontend typecheck/build.
- Production environment mode and deployment templates.
- Runtime guardrails that reject unsafe production defaults.
- Optional demo seeding controlled by environment.
- Basic backend security headers.
- Local SQLite/upload backup helper.
- Deployment and security checklists.

## Phase IX: LMS / Canvas Handoff

- Canvas-import-style wide gradebook CSV with one row per student and assignment score columns.
- Assignment-filtered Canvas and LMS exports.
- Detailed LMS handoff CSV with submission status, validation status, timestamps, and feedback.
- Roster CSV export.
- Roster import aliases for common Canvas-style column names.

## Phase X: Controlled AI Integration

- Instructor-controlled course assistant switch in Course Setup.
- Offline course-guidance provider for safe pilot testing without external calls.
- Optional OpenAI provider path gated by instructor policy and server environment.
- Provider metadata, response id, model, and privacy flags on prompt logs.
- Prompt privacy checks before external provider calls.
- Controlled AI setup documentation.
