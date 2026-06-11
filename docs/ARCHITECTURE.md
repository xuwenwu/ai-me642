# Architecture

```text
Next.js frontend
  | JSON + multipart upload
  v
FastAPI backend
  |-- auth and role checks
  |-- REST routers
  |-- SQLAlchemy models
  |-- LAMMPS log parser
  |-- validation engine
  |-- reproducible ZIP builder
  |-- CSV gradebook export
  |
  |-- SQLite for local development
  |-- PostgreSQL-ready DATABASE_URL
  |-- local per-submission file storage
```

## Backend Boundaries

The backend stores files, parses text logs, records metadata, creates validation reports, exports CSV files, and builds ZIP packages. It never executes uploaded code.

## Validation Philosophy

Validation produces advisory evidence. It can fail a required-file or LAMMPS-error check, but it does not assign a course grade. The instructor-facing review page should present validation results beside prompt evidence and student interpretation.

## Phase I-Plus Entities

- User
- Course
- Assignment
- Rubric
- RubricCriterion
- ProjectSpecification
- PromptLogEntry
- Submission
- FileArtifact
- ValidationReport
- ValidationCheck
- Grade
- CriterionScore

## Extension Points

- Add more assignment-specific validators.
- Add richer thermo plots from parsed log data.
- Add controlled LLM support behind instructor policy.
- Add Canvas and HPC metadata integrations after the local workflow is stable.

