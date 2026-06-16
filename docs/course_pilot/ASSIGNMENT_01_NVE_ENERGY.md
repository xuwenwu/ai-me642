# Pilot Assignment 1: NVE Energy Conservation and Timestep Stability

## Purpose

Use a short LAMMPS NVE simulation to evaluate whether total energy is conserved well enough to support a cautious timestep-stability claim. The assignment emphasizes reproducible evidence, responsible AI disclosure, and interpretation of validation results.

## Learning Goals

By the end of this assignment, you should be able to:

- Explain why total-energy drift matters in an NVE simulation.
- Upload a reproducible simulation evidence package.
- Use validation output and thermo plots to identify warnings or caveats.
- Distinguish automated validation evidence from final scientific interpretation.
- Disclose AI assistance in a way an instructor can audit.

## Required Evidence

Upload these file types:

- `lammps_input`: the LAMMPS input script.
- `lammps_log`: the LAMMPS log file containing thermo output.

## Recommended Evidence

Upload these when available:

- `slurm_script`: the batch script used to run the job.
- `python_analysis`: analysis or plotting script.
- `ovito_script`: visualization or structural-analysis script.
- `readme`: short run instructions, parameters, and known caveats.
- `figure`: plot or screenshot that supports your interpretation.
- `data`: processed table or comparison data.

## Simulation Task

Run a short NVE molecular-dynamics simulation for a simple material or teaching system selected by the instructor.

Your run should produce thermo output with at least:

- Step.
- Temperature.
- Total energy.
- Pressure when available.
- Volume when available.

If you compare two timesteps, upload the most relevant log first and optionally upload the second log as another `lammps_log`.

## Validation Profile

Use:

```text
nve_energy_conservation
```

## Course Setup Field Values

Use these values when creating the assignment in Course Setup:

```text
Title: Pilot Assignment 1: NVE Energy Conservation and Timestep Stability
Assignment type: lab
Points: 100
Status: published when ready for students; draft while preparing
Validation profile: nve_energy_conservation
Required file types: lammps_input, lammps_log
Optional file types: readme, prompt_log, python_analysis, ovito_script, slurm_script, figure, data
```

Recommended validation settings:

```json
{
  "energy_drift_warning_threshold": 0.05,
  "required_thermo_columns": ["Step", "Temp", "TotEng"],
  "minimum_thermo_rows": 5,
  "max_lammps_warnings": 2
}
```

The instructor may adjust these settings depending on the system and run length.

## Student Interpretation Prompts

Answer these in the Student Interpretation box:

1. What does the total-energy trend suggest about timestep stability?
2. Did the run complete, and were there LAMMPS errors or warnings?
3. How do temperature and pressure fluctuations affect your confidence?
4. What additional run or comparison would strengthen the conclusion?
5. What AI assistance did you use, and how did validation change your final answer?

## Submission Checklist

Before clicking Submit assignment, confirm:

- Required files are uploaded.
- Validation has been run.
- You read all warnings and failed checks.
- Thermo plots are visible or you explained why they are missing.
- AI prompt logs are recorded if AI assistance shaped the work.
- Student interpretation is complete and specific.

## Suggested Due-Date Language

Submit through AI-ME642 before class on the due date. Late policy follows the course syllabus. If the validation tool reports a warning, do not hide it; explain what it means and what you would do next.
