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
- Instructor-only provider readiness check, test prompt, and monthly external-call guardrails.
- Provider metadata, response id, model, and privacy flags on prompt logs.
- Prompt privacy checks before external provider calls.
- Controlled AI setup documentation.

## Phase XI: Deployable Pilot Release

- Docker-based backend and frontend runtime packaging for a private pilot host.
- Compose stack with private backend networking, persistent data volume, restart policy, and service health checks.
- Production pilot environment template kept separate from local development secrets.
- Backend readiness endpoint that verifies database access and upload storage writeability.
- Pilot operations runbook for setup, health checks, backups, upgrades, rollback, incidents, and exit exports.
- Documentation updates that distinguish temporary workstation tunnels from a stable course deployment.

## Phase XII: Account and Password Management

- User accounts include active/inactive status and a required password-change flag.
- Login blocks inactive accounts and routes temporary-password users to password change.
- Backend guards prevent app use until required password changes are completed.
- Logged-in users can change their own password.
- Instructors can reset student passwords, require/clear password changes, and deactivate/reactivate student accounts.
- Roster import accepts optional password, active status, and force-password-change columns.

## Phase XIII: Real Hosting / Domain / HTTPS

- Caddy reverse-proxy template for a stable HTTPS course domain.
- Hosted Compose override that exposes only ports 80/443 and keeps app services private.
- Deployment docs distinguish review tunnels from hosted class use.

## Phase XIV: Course Data Retention and Privacy

- Course archive script exports roster, assignments, submissions, grades, prompt logs, and uploaded files.
- Retention documentation separates operational backups from course-record archives.
- Environment templates include archive storage locations.

## Phase XV: Better Instructor Workflow

- Instructor Review includes a direct needs-attention panel.
- Needs-attention items select the related submission in the review workflow.
- Review page combines triage, filters, evidence, plots, interpretation, and grading.

## Phase XVI: Student Experience Polish

- Student Dashboard gives assignment-specific next-step guidance.
- Empty assignment state is clearer for fresh production pilots.
- Next-step cues distinguish create, validate, interpret, submit, wait-for-grade, and review-feedback states.

## Phase XVII: Canvas / LMS API Scaffolding

- Server-side Canvas configuration is available but disabled by default.
- Instructor Canvas status endpoint reports whether integration is configured without exposing tokens.
- CSV export remains the stable LMS workflow until institutional approval and test-course verification.

## Phase XVIII: More Scientific Validation Depth

- Assignment validation settings can require thermo columns.
- Assignment validation settings can enforce minimum parsed run length.
- Assignment validation settings can fail excessive LAMMPS warning counts.
- Validation tests cover the new assignment-level thresholds.

## Phase XIX: E2E Browser Test Automation

- Playwright browser tests cover student submission, validation, interpretation, and submit flow.
- Instructor browser tests cover review queue, validation evidence, grading, gradebook, and course setup checks.
- Mobile viewport tests cover student and instructor core page rendering.
- E2E tests create unique pilot data through instructor APIs, then verify behavior through the browser UI.
