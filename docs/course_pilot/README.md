# AI-ME642 Small-Class Pilot Content Pack

Use this folder when preparing a small real-class pilot. The platform is already built around the evidence chain:

```text
scientific specification -> AI prompt log -> simulation artifacts -> validation report -> student interpretation -> instructor grading -> reproducible ZIP package
```

This pack turns that platform workflow into course-facing materials.

## Files

- `INSTRUCTOR_GUIDE.md`: instructor and TA setup, class-session flow, grading routine, and common interventions.
- `STUDENT_QUICK_START.md`: student-facing first-use instructions and submission checklist.
- `ASSIGNMENT_01_NVE_ENERGY.md`: copy-ready pilot assignment for NVE energy conservation and timestep stability.
- `RUBRIC_NVE_ENERGY.md`: grading rubric aligned with the app's default 100-point criteria.
- `SAMPLE_SUBMISSIONS.md`: examples of strong and needs-work submission evidence for calibration.
- `PILOT_FEEDBACK.md`: instructor and student feedback prompts for the first pilot cycle.
- `roster_template.csv`: minimal roster import template.

## Recommended First Pilot Scope

Run the first pilot with one assignment and 2-5 students or trusted testers.

Use `ASSIGNMENT_01_NVE_ENERGY.md` as the first assignment because it exercises the highest-value workflow:

- LAMMPS input and log upload.
- Multi-artifact evidence upload.
- Thermo plot review.
- Validation warnings and scientific caveats.
- AI prompt-log disclosure.
- Student interpretation and instructor rubric grading.

Keep external AI provider mode disabled for the first pilot unless course policy, privacy expectations, and billing ownership are already settled.

## Instructor Setup Checklist

1. Deploy or launch the app using `docs/PILOT_OPERATIONS.md`.
2. Create the instructor account.
3. Import `roster_template.csv` after replacing the example rows.
4. Create or paste the NVE pilot assignment from `ASSIGNMENT_01_NVE_ENERGY.md`.
5. Confirm the AI policy and prompt templates are visible from the student prompt-log page.
6. Ask each student to sign in and change the temporary password.
7. Run one sample submission before assigning the activity.

## Pilot Success Criteria

The pilot is successful if:

- Students can log in, create a submission, upload artifacts, run validation, and submit without instructor intervention.
- Students understand that validation is advisory evidence, not a grade.
- Instructor or TA can review each submission in under 10 minutes after the initial learning curve.
- At least one confusing student-facing message, missing cue, or workflow bottleneck is identified for the next development phase.
