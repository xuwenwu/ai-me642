# Student Quick Start

Use this guide for your first AI-ME642 submission.

## What You Are Submitting

You are not only submitting simulation files. You are submitting an evidence package:

```text
scientific goal -> AI assistance record -> simulation artifacts -> validation evidence -> your interpretation
```

The validation tool helps you inspect the package. It does not decide your grade.

## First Login

1. Open the course app link from your instructor.
2. Sign in with your course email and temporary password.
3. If prompted, change your password.
4. Open Dashboard and confirm the assignment is visible.

## Before Uploading Files

Prepare the files requested by the assignment.

Required for the first pilot assignment:

- LAMMPS input file, usually `.in`.
- LAMMPS log file, usually `.log`.

Recommended when available:

- README or notes explaining how you ran the simulation.
- Slurm script.
- Python analysis script.
- OVITO script.
- Figure, data table, or comparison output.

Do not upload private credentials, API keys, personal data, or unrelated files.

## Record AI Use

If AI assistance shaped your work, open Prompt Logs and record it before submitting.

Your prompt log should explain:

- Which tool you used.
- What you asked.
- What the tool suggested.
- What you accepted.
- What you rejected.
- What you manually changed.
- What validation you performed afterward.
- What concerns remain.

It is acceptable to use AI help when your instructor allows it. It is not acceptable to hide it or treat AI output as proof.

## Submit Your Assignment

1. Open Submission.
2. Select the assignment.
3. Click Create submission.
4. Upload required files.
5. Upload optional evidence files when available.
6. Click Run validation.
7. Read the validation checks and thermo plots.
8. Read the interpretation cues.
9. Write your interpretation.
10. Click Save interpretation.
11. Click Submit assignment.
12. Confirm the button changes to Submitted or Dashboard shows submitted status.

## What A Good Interpretation Includes

A strong interpretation is specific. It should mention:

- Whether the run completed.
- Whether LAMMPS errors or warnings appeared.
- What the thermo plots suggest.
- Whether total energy drift is small enough for your claim.
- Why temperature and pressure fluctuations do or do not change the conclusion.
- What evidence is still missing.
- How AI advice was checked against actual output.

## Common Mistakes

- Uploading only the input file and no log.
- Running validation but not reading the warnings.
- Saying "energy is conserved" without describing the drift evidence.
- Copying AI wording without explaining what was verified.
- Submitting an empty interpretation.
- Treating validation status as the grade.

## Need Help?

Ask your instructor or TA and include:

- Assignment name.
- What step you are on.
- What message or validation warning you see.
- Which file you uploaded most recently.
