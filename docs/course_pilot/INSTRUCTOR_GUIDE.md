# Instructor Guide

This guide is for a small private pilot of AI-ME642 with one assignment and a small roster.

## Pilot Goal

Use the app to make responsible AI-assisted molecular-dynamics work inspectable. The pilot should test whether students can produce a complete evidence package, not whether the platform can replace scientific judgment.

## Before Class

1. Confirm the app is reachable at the pilot URL.
2. Confirm `/api/health/ready` reports `database` and `upload_root` as `ok`.
3. Create or import student accounts in Course Setup.
4. Keep `Require password change` enabled for temporary passwords.
5. Create the pilot assignment from `ASSIGNMENT_01_NVE_ENERGY.md`.
6. Keep the assignment status as `draft` until the roster and policy text are ready.
7. Review the AI policy and prompt templates in Course Setup.
8. Run one instructor-owned sample submission using files from `sample_data`.
9. Take a backup before students begin.

## Recommended Class Flow

### First 10 Minutes

- Explain the evidence chain: prompt log, artifacts, validation, interpretation, grading.
- Emphasize that validation does not assign the grade.
- Show the difference between a warning and a failed scientific conclusion.
- Tell students not to upload private data, credentials, or unrelated files.

### Work Session

Ask students to:

1. Open Dashboard.
2. Read the assignment.
3. Open Prompt Logs and record any AI help used.
4. Open Submission.
5. Create the submission package.
6. Upload the required LAMMPS input and log.
7. Upload optional Slurm, Python, OVITO, README, figure, or data files when available.
8. Run validation.
9. Read plots and interpretation cues.
10. Save interpretation.
11. Submit assignment.

### Instructor or TA Monitoring

Use Instructor Overview and Review Queue during the session.

Look first for:

- Missing required files.
- Validation failed or warning statuses.
- Thin AI disclosure.
- Empty student interpretation.
- Students who created a submission but did not submit.

## Grading Routine

For each submission:

1. Open Instructor Review.
2. Select the assignment and submission.
3. Read the evidence checklist.
4. Inspect validation checks and thermo plots.
5. Read the student interpretation before assigning scores.
6. Review prompt-log evidence when AI assistance is claimed.
7. Enter rubric scores and feedback.
8. Save grade and confirm the success message appears.

Use the validation report as evidence, not as a replacement for grading. A submission can have a warning and still be scientifically strong if the student explains the limitation correctly.

## Common Interventions

### Student Cannot Log In

- Confirm the account is active in Course Setup.
- Reset the password.
- Require password change again if the password was shared through a temporary channel.

### Student Cannot Create Submission

- Confirm the assignment is published.
- Confirm the student selected an assignment.
- Confirm the student has not already created a submission for that assignment.

### Validation Warning

Ask the student to explain:

- Which check produced the warning.
- Whether it affects the scientific claim.
- What additional run, plot, or comparison would reduce uncertainty.

### Weak AI Disclosure

Ask for a corrected prompt log that includes:

- The AI tool or assistant used.
- The prompt or prompt summary.
- Output summary in the student's own words.
- Accepted and rejected advice.
- Manual edits and validation performed.

## After Class

1. Export gradebook and LMS detail CSVs.
2. Export or back up course data.
3. Record instructor observations using `PILOT_FEEDBACK.md`.
4. Preserve two anonymized examples for future calibration if allowed by course policy.
5. File development notes for confusing UI, missing validations, and grading bottlenecks.
