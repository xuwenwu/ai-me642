# Sample Submission Calibration

Use these examples to calibrate expectations before grading real student work. They are not complete answer keys.

## Strong Submission Pattern

### Files

- LAMMPS input file is present and matches the described run.
- LAMMPS log contains thermo output with Step, Temp, and TotEng.
- Optional Slurm or README explains how the run was produced.
- Python or plotting script is included when the student used post-processing.

### Validation

- Validation runs to completion.
- Status may be `passed` or `warning`.
- If status is `warning`, the student explains why the warning does or does not weaken the claim.
- Thermo plots are referenced directly in the interpretation.

### Interpretation

Example strong wording:

```text
The run completed and the thermo table includes Step, Temp, and TotEng. The total-energy plot is nearly flat over the short sampled interval, so this timestep appears acceptable for this teaching-scale NVE check. The pressure fluctuates substantially, so I would not make a pressure-equilibration claim from this run. The validation warning about LAMMPS warnings should be checked before using the result for production. AI suggested checking only the final energy, but I instead inspected the full trend and the warning list.
```

### Instructor Note

This submission can earn high marks even if validation has a warning, provided the warning is interpreted honestly and the scientific claim stays narrow.

## Needs-Work Submission Pattern

### Files

- Input file is present but no log is uploaded, or the log lacks thermo rows.
- Optional files are named ambiguously.
- README is absent when the run command or timestep choice is unclear.

### Validation

- Validation was not run, or failed checks are not addressed.
- Student reports "passed" without identifying what was checked.
- Thermo plots are missing or ignored.

### Interpretation

Example weak wording:

```text
The simulation worked and energy is conserved. ChatGPT said the timestep is stable. Everything looks good.
```

### Instructor Note

This should not receive high interpretation or validation credit. The claim is generic, AI-dependent, and not tied to uploaded evidence. Feedback should ask for a specific reference to completion status, warnings, energy drift, and remaining uncertainty.

## Borderline Warning Case

### Situation

The log completes and includes thermo output, but validation reports warning status because one LAMMPS warning appears or energy drift is near the configured threshold.

### Acceptable Student Response

The student acknowledges the warning, limits the claim, and proposes an additional run with a smaller timestep or longer sampling.

### Unacceptable Student Response

The student ignores the warning and states the simulation proves physical stability.

## TA Calibration Questions

Before grading, compare two submissions and ask:

- Which evidence supports the student's main claim?
- Which warning or missing file would change the grade?
- Did the student distinguish simulation completion from scientific validity?
- Did the student disclose AI assistance in an auditable way?
- What feedback would help the student improve the next submission?
