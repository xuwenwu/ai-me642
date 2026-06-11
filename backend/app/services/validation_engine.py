from __future__ import annotations
import json
import math
import re
from pathlib import Path
from sqlalchemy.orm import Session
from ..models import FileArtifact, PromptLogEntry, Submission, ValidationCheck, ValidationReport
from .lammps_log_parser import parse_lammps_log


FILE_TYPE_LABELS = {
    "lammps_input": "LAMMPS input script",
    "lammps_log": "LAMMPS log",
    "readme": "README/reproducibility notes",
    "prompt_log": "Uploaded prompt log",
    "python_analysis": "Python analysis script",
    "ovito_script": "OVITO script",
    "slurm_script": "Slurm batch script",
    "figure": "Figure",
    "data": "Data file",
    "other": "Other artifact",
}

FORBIDDEN_SCRIPT_PATTERNS = [
    (re.compile(r"\brm\s+-rf\b", re.IGNORECASE), "destructive recursive delete"),
    (re.compile(r"\b(?:curl|wget)\b", re.IGNORECASE), "network download"),
    (re.compile(r"\b(?:subprocess|os\.system|eval|exec)\b", re.IGNORECASE), "dynamic command execution"),
    (re.compile(r"\b(?:socket|requests|urllib)\b", re.IGNORECASE), "network access"),
]


def _check(check_type: str, status: str, severity: str, message: str, evidence: str = "") -> dict:
    return {
        "check_type": check_type,
        "status": status,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }


def _note(topic: str, status: str, message: str, evidence: str = "") -> dict:
    return {
        "topic": topic,
        "status": status,
        "message": message,
        "evidence": evidence,
    }


def _rows(parsed: dict) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for section in parsed.get("sections", []):
        rows.extend(section.get("rows", []))
    return rows


def _sample_rows(rows: list[dict[str, float]], limit: int = 500) -> list[dict[str, float]]:
    if len(rows) <= limit:
        return rows
    stride = max(math.ceil(len(rows) / limit), 1)
    sampled = rows[::stride]
    return sampled[:limit]


def _thermo_series(source: str, parsed: dict) -> dict | None:
    rows = _rows(parsed)
    if not rows:
        return None

    plottable = ["Step", "Temp", "TotEng", "Press", "Volume"]
    columns = [column for column in plottable if column in rows[0]]
    if "Step" not in columns or len(columns) < 2:
        return None

    points = [
        {column: float(row[column]) for column in columns if column in row}
        for row in _sample_rows(rows)
    ]
    return {
        "source": source,
        "x_field": "Step",
        "columns": columns,
        "points": points,
    }


def _read_text(file: FileArtifact, limit: int = 200_000) -> str:
    try:
        return Path(file.file_path).read_text(errors="replace")[:limit]
    except OSError:
        return ""


def _forbidden_findings(text: str) -> list[str]:
    findings: list[str] = []
    for pattern, label in FORBIDDEN_SCRIPT_PATTERNS:
        if pattern.search(text):
            findings.append(label)
    return findings


def _normalized_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped.lower())
    return lines


def _has_lammps_command(lines: list[str], command: str) -> bool:
    return any(line == command or line.startswith(f"{command} ") for line in lines)


def _lint_lammps_input(file: FileArtifact) -> tuple[list[dict], list[dict]]:
    text = _read_text(file)
    lines = _normalized_lines(text)
    checks: list[dict] = []
    notes: list[dict] = []
    required = {
        "units": _has_lammps_command(lines, "units"),
        "atom_style": _has_lammps_command(lines, "atom_style"),
        "force field": _has_lammps_command(lines, "pair_style") or _has_lammps_command(lines, "pair_coeff"),
        "thermo": _has_lammps_command(lines, "thermo") or _has_lammps_command(lines, "thermo_style"),
        "run": _has_lammps_command(lines, "run"),
    }
    missing = [label for label, present in required.items() if not present]
    fix_lines = [line for line in lines if line.startswith("fix ")]
    ensemble_terms = [" nve", " nvt", " npt", " langevin", " temp/rescale"]
    has_ensemble = any(any(term in f" {line}" for term in ensemble_terms) for line in fix_lines)
    shell_lines = [line for line in lines if line.startswith("shell ")]

    checks.append(
        _check(
            "lammps_input_structure",
            "passed" if not missing else "warning",
            "medium",
            "LAMMPS input includes core setup commands" if not missing else "LAMMPS input is missing core setup commands",
            f"missing={', '.join(missing) if missing else 'none'}",
        )
    )
    checks.append(
        _check(
            "lammps_ensemble_fix",
            "passed" if has_ensemble else "warning",
            "medium",
            "LAMMPS input includes a recognizable time-integration or thermostat fix" if has_ensemble else "No recognizable ensemble/time-integration fix found",
            "; ".join(fix_lines[:3]) if fix_lines else "no fix commands detected",
        )
    )
    if shell_lines:
        checks.append(
            _check(
                "lammps_input_shell_commands",
                "warning",
                "high",
                "LAMMPS input uses shell commands; verify this is safe and reproducible",
                " | ".join(shell_lines[:3]),
            )
        )
    notes.append(
        _note(
            "LAMMPS input lint",
            "supported" if not missing and has_ensemble else "needs_review",
            (
                "The input script includes the expected setup, force-field, thermo, run, and ensemble cues."
                if not missing and has_ensemble
                else "The input script needs instructor/student review for missing setup or ensemble cues."
            ),
            file.original_filename,
        )
    )
    return checks, notes


def _lint_slurm_script(file: FileArtifact) -> tuple[list[dict], list[dict]]:
    text = _read_text(file)
    lower = text.lower()
    directives = [line.strip() for line in text.splitlines() if line.strip().startswith("#SBATCH")]
    has_resources = any(flag in lower for flag in ["--time", "-t ", "--nodes", "--ntasks", "--cpus-per-task", "--mem"])
    has_launch = any(token in lower for token in ["srun", "mpirun", "mpiexec", "lmp", "lammps"])
    forbidden = _forbidden_findings(text)
    checks = [
        _check(
            "slurm_directives",
            "passed" if directives else "warning",
            "medium",
            "Slurm directives detected" if directives else "No #SBATCH directives detected",
            " | ".join(directives[:5]) if directives else file.original_filename,
        ),
        _check(
            "slurm_resources",
            "passed" if has_resources else "warning",
            "medium",
            "Slurm resource/time settings detected" if has_resources else "No clear Slurm resource or time settings detected",
            file.original_filename,
        ),
        _check(
            "slurm_launch_command",
            "passed" if has_launch else "warning",
            "medium",
            "LAMMPS or MPI launch command detected" if has_launch else "No clear LAMMPS/MPI launch command detected",
            file.original_filename,
        ),
        _check(
            "slurm_script_safety",
            "failed" if forbidden else "passed",
            "high",
            "Potentially unsafe script pattern detected" if forbidden else "No obvious destructive/network script patterns detected",
            ", ".join(forbidden) if forbidden else file.original_filename,
        ),
    ]
    notes = [
        _note(
            "Slurm reproducibility",
            "supported" if directives and has_resources and has_launch and not forbidden else "needs_review",
            (
                "The Slurm script includes scheduler directives, resource hints, and a launch command."
                if directives and has_resources and has_launch and not forbidden
                else "Review the Slurm script for scheduler directives, resource requests, launch command, or unsafe patterns."
            ),
            file.original_filename,
        )
    ]
    return checks, notes


def _lint_python_analysis(file: FileArtifact) -> tuple[list[dict], list[dict]]:
    text = _read_text(file)
    lower = text.lower()
    has_analysis_import = any(token in lower for token in ["import numpy", "import pandas", "import matplotlib", "from matplotlib", "import seaborn"])
    has_input_read = any(token in lower for token in [".read_csv", "loadtxt", "genfromtxt", "open(", "read_text", "readtable"])
    has_output = any(token in lower for token in ["savefig", "to_csv", "write_text", "json.dump", ".write("])
    forbidden = _forbidden_findings(text)
    checks = [
        _check(
            "python_analysis_structure",
            "passed" if has_analysis_import and has_input_read else "warning",
            "medium",
            "Python analysis appears to import analysis libraries and read data" if has_analysis_import and has_input_read else "Python analysis script needs clearer imports or data reads",
            f"analysis_import={has_analysis_import}; input_read={has_input_read}",
        ),
        _check(
            "python_analysis_output",
            "passed" if has_output else "warning",
            "low",
            "Python analysis appears to save or write an output" if has_output else "No obvious saved figure/table/output found",
            file.original_filename,
        ),
        _check(
            "python_analysis_safety",
            "failed" if forbidden else "passed",
            "high",
            "Potentially unsafe Python pattern detected" if forbidden else "No obvious command execution or network access detected",
            ", ".join(forbidden) if forbidden else file.original_filename,
        ),
    ]
    notes = [
        _note(
            "Python analysis artifact",
            "supported" if has_analysis_import and has_input_read and has_output and not forbidden else "needs_review",
            (
                "The Python script looks like a static analysis artifact with imports, input reads, and output generation."
                if has_analysis_import and has_input_read and has_output and not forbidden
                else "Review the Python script for analysis inputs, saved outputs, and safe reproducibility."
            ),
            file.original_filename,
        )
    ]
    return checks, notes


def _lint_ovito_script(file: FileArtifact) -> tuple[list[dict], list[dict]]:
    text = _read_text(file)
    lower = text.lower()
    has_ovito = "import ovito" in lower or "from ovito" in lower
    has_import_file = "import_file" in lower
    has_processing = any(token in lower for token in ["modifiers.append", "coordinationanalysismodifier", "export_file", "pipeline.compute"])
    forbidden = _forbidden_findings(text)
    checks = [
        _check(
            "ovito_script_structure",
            "passed" if has_ovito and has_import_file and has_processing else "warning",
            "medium",
            "OVITO script includes import, file load, and processing/export cues" if has_ovito and has_import_file and has_processing else "OVITO script needs clearer import/load/processing cues",
            f"ovito_import={has_ovito}; import_file={has_import_file}; processing={has_processing}",
        ),
        _check(
            "ovito_script_safety",
            "failed" if forbidden else "passed",
            "high",
            "Potentially unsafe OVITO/Python pattern detected" if forbidden else "No obvious command execution or network access detected",
            ", ".join(forbidden) if forbidden else file.original_filename,
        ),
    ]
    notes = [
        _note(
            "OVITO artifact",
            "supported" if has_ovito and has_import_file and has_processing and not forbidden else "needs_review",
            (
                "The OVITO script appears to load data and perform processing/export steps."
                if has_ovito and has_import_file and has_processing and not forbidden
                else "Review the OVITO script for clear data loading, processing, export, and safe reproducibility."
            ),
            file.original_filename,
        )
    ]
    return checks, notes


def _multi_log_comparison(parsed_logs: list[tuple[FileArtifact, dict]]) -> tuple[list[dict], list[dict]]:
    if len(parsed_logs) < 2:
        return [], []
    row_sets = [(file, _rows(parsed)) for file, parsed in parsed_logs]
    logs_with_rows = [(file, rows) for file, rows in row_sets if rows]
    if len(logs_with_rows) < 2:
        return [
            _check("multi_log_comparison", "warning", "medium", "Multiple logs uploaded, but fewer than two include thermo rows", str(len(parsed_logs)))
        ], [
            _note("Multi-run comparison", "needs_context", "Multiple logs were uploaded, but there is not enough thermo data for comparison.", str(len(parsed_logs)))
        ]

    common_columns = set(logs_with_rows[0][1][0])
    for _, rows in logs_with_rows[1:]:
        common_columns &= set(rows[0])
    completed_count = sum(1 for _, parsed in parsed_logs if parsed.get("completed"))
    error_count = sum(1 for _, parsed in parsed_logs if parsed.get("errors"))
    step_ranges = []
    for file, rows in logs_with_rows:
        if "Step" in rows[0]:
            steps = [row["Step"] for row in rows if "Step" in row]
            step_ranges.append(f"{file.original_filename}:{min(steps):.0f}-{max(steps):.0f}")
    has_useful_common = {"Step", "Temp"} <= common_columns
    status = "passed" if has_useful_common and error_count == 0 else "warning"
    return [
        _check(
            "multi_log_comparison",
            status,
            "medium",
            "Multiple LAMMPS logs are comparable" if status == "passed" else "Multiple LAMMPS logs need comparison review",
            f"logs={len(parsed_logs)}; completed={completed_count}; errors={error_count}; common_columns={', '.join(sorted(common_columns))}; steps={' | '.join(step_ranges)}",
        )
    ], [
        _note(
            "Multi-run comparison",
            "supported" if status == "passed" else "needs_review",
            (
                "Multiple logs share common thermo columns, enabling side-by-side comparison of runs."
                if status == "passed"
                else "Multiple logs were detected, but columns, completion, or errors need review before comparing runs."
            ),
            f"common_columns={', '.join(sorted(common_columns))}; steps={' | '.join(step_ranges)}",
        )
    ]


def validate_submission(db: Session, submission: Submission) -> ValidationReport:
    assignment = submission.assignment
    validation_profile = assignment.validation_profile if assignment else "lammps_basic_health"
    validation_settings = assignment.validation_settings if assignment else {}
    required_file_types = assignment.required_file_types if assignment else ["lammps_input", "lammps_log"]
    optional_file_types = assignment.optional_file_types if assignment else ["readme", "prompt_log", "python_analysis", "ovito_script", "figure"]
    files: list[FileArtifact] = list(submission.files)
    file_types = {file.file_type for file in files}
    checks: list[dict] = []
    thermo_series: list[dict] = []
    interpretation_notes: list[dict] = []
    parsed_logs: list[tuple[FileArtifact, dict]] = []

    def present(expected: set[str], label: str, required: bool) -> None:
        ok = bool(expected & file_types)
        checks.append(
            _check(
                "file_completeness",
                "passed" if ok else ("failed" if required else "warning"),
                "high" if required else "medium",
                f"{label} {'present' if ok else 'missing'}",
                ", ".join(sorted(file_types)) or "no files uploaded",
            )
        )

    for file_type in required_file_types:
        present({file_type}, FILE_TYPE_LABELS.get(file_type, file_type), True)

    if "readme" in optional_file_types:
        present({"readme"}, FILE_TYPE_LABELS["readme"], False)

    supporting_optional = set(optional_file_types) - {"readme", "prompt_log"}
    if supporting_optional:
        present(supporting_optional, "Supporting analysis artifact", False)

    if "readme" in optional_file_types and "readme" not in file_types:
        interpretation_notes.append(
            _note(
                "Reproducibility notes",
                "needs_context",
                "Add a README or short reproducibility note so another reader can rerun or audit the workflow.",
                ", ".join(sorted(file_types)) or "no files uploaded",
            )
        )

    prompt_count = (
        db.query(PromptLogEntry)
        .filter(
            PromptLogEntry.user_id == submission.user_id,
            (PromptLogEntry.assignment_id == submission.assignment_id) | (PromptLogEntry.project_id == submission.project_id),
        )
        .count()
    )
    prompt_uploaded = "prompt_log" in file_types
    if not prompt_count and not prompt_uploaded:
        interpretation_notes.append(
            _note(
                "AI disclosure",
                "needs_context",
                "Prompt evidence is missing; explain any AI assistance or state that no AI assistance was used.",
                f"database_entries={prompt_count}; uploaded_prompt_log={prompt_uploaded}",
            )
        )
    else:
        interpretation_notes.append(
            _note(
                "AI disclosure",
                "supported",
                "Prompt evidence is present, so the interpretation can reference an inspectable AI-use trail.",
                f"database_entries={prompt_count}; uploaded_prompt_log={prompt_uploaded}",
            )
        )
    checks.append(
        _check(
            "ai_disclosure",
            "passed" if prompt_count or prompt_uploaded else "warning",
            "medium",
            "Prompt evidence present" if prompt_count or prompt_uploaded else "Prompt evidence missing",
            f"database_entries={prompt_count}; uploaded_prompt_log={prompt_uploaded}",
        )
    )

    for file in files:
        if file.file_type == "lammps_input":
            extra_checks, extra_notes = _lint_lammps_input(file)
            checks.extend(extra_checks)
            interpretation_notes.extend(extra_notes)
        elif file.file_type == "slurm_script":
            extra_checks, extra_notes = _lint_slurm_script(file)
            checks.extend(extra_checks)
            interpretation_notes.extend(extra_notes)
        elif file.file_type == "python_analysis":
            extra_checks, extra_notes = _lint_python_analysis(file)
            checks.extend(extra_checks)
            interpretation_notes.extend(extra_notes)
        elif file.file_type == "ovito_script":
            extra_checks, extra_notes = _lint_ovito_script(file)
            checks.extend(extra_checks)
            interpretation_notes.extend(extra_notes)

        if file.file_type != "lammps_log":
            continue
        parsed = parse_lammps_log(Path(file.file_path))
        parsed_logs.append((file, parsed))
        series = _thermo_series(file.original_filename, parsed)
        if series:
            thermo_series.append(series)
        if parsed["errors"]:
            interpretation_notes.append(
                _note(
                    "LAMMPS log health",
                    "concern",
                    "The log contains LAMMPS ERROR lines, so simulation results should not be interpreted as a completed valid run until the error is resolved.",
                    " | ".join(parsed["errors"][:3]),
                )
            )
        else:
            interpretation_notes.append(
                _note(
                    "LAMMPS log health",
                    "supported",
                    "No LAMMPS ERROR lines were detected in this log.",
                    file.original_filename,
                )
            )
        checks.append(
            _check(
                "lammps_log_health",
                "failed" if parsed["errors"] else "passed",
                "high",
                "LAMMPS ERROR detected" if parsed["errors"] else "No LAMMPS ERROR lines detected",
                " | ".join(parsed["errors"][:3]) if parsed["errors"] else file.original_filename,
            )
        )
        if parsed["warnings"]:
            interpretation_notes.append(
                _note(
                    "LAMMPS warnings",
                    "needs_review",
                    "LAMMPS warning lines were detected; discuss whether they affect the physical interpretation.",
                    " | ".join(parsed["warnings"][:3]),
                )
            )
            checks.append(
                _check(
                    "lammps_warnings",
                    "warning",
                    "medium",
                    "LAMMPS warning lines detected",
                    " | ".join(parsed["warnings"][:3]),
                )
            )
        checks.append(
            _check(
                "thermo_data",
                "passed" if parsed["sections"] else "failed",
                "high",
                "Thermo data detected" if parsed["sections"] else "No thermo data detected",
                ", ".join(parsed["columns_detected"]),
            )
        )
        checks.append(
            _check(
                "run_completion",
                "passed" if parsed["completed"] else "warning",
                "medium",
                "Run appears completed" if parsed["completed"] else "Run completion marker not found",
                file.original_filename,
            )
        )

        rows = _rows(parsed)
        if not rows:
            interpretation_notes.append(
                _note(
                    "Thermo evidence",
                    "concern",
                    "No thermo rows were available for plotting or trend interpretation.",
                    file.original_filename,
                )
            )
            continue
        if "Step" in rows[0]:
            steps = [row["Step"] for row in rows if "Step" in row]
            monotonic = all(b >= a for a, b in zip(steps, steps[1:]))
            checks.append(
                _check(
                    "step_monotonicity",
                    "passed" if monotonic else "failed",
                    "high",
                    "Steps are nondecreasing" if monotonic else "Steps are not monotonic",
                    str(steps[:8]),
                )
            )
        if "Temp" in rows[0]:
            temps = [row.get("Temp", math.nan) for row in rows]
            bad = any(math.isnan(temp) or temp < 0 or temp > 10000 for temp in temps)
            drift = abs(temps[-1] - temps[0]) if len(temps) > 1 else 0
            interpretation_notes.append(
                _note(
                    "Temperature trend",
                    "concern" if bad else ("needs_review" if drift > 1000 else "supported"),
                    (
                        "Temperature contains implausible values; inspect the setup before interpreting the run."
                        if bad
                        else (
                            "Temperature changes strongly across the run; explain whether that is expected for this setup."
                            if drift > 1000
                            else "Temperature values look plausible in the parsed thermo series."
                        )
                    ),
                    f"start={temps[0]:.3g}, end={temps[-1]:.3g}, drift={drift:.3g}",
                )
            )
            checks.append(
                _check(
                    "temperature_sanity",
                    "failed" if bad else ("warning" if drift > 1000 else "passed"),
                    "high" if bad else "medium",
                    "Temperature values are plausible" if not bad else "Temperature contains NaN, negative, or extreme values",
                    f"start={temps[0]:.3g}, end={temps[-1]:.3g}, drift={drift:.3g}",
                )
            )
            if validation_profile == "nvt_temperature_control":
                target = float(validation_settings.get("target_temperature", 300))
                tolerance = float(validation_settings.get("temperature_tolerance", 75))
                tail = temps[len(temps) // 2 :] or temps
                tail_average = sum(tail) / len(tail)
                deviation = abs(tail_average - target)
                passed = not bad and deviation <= tolerance
                checks.append(
                    _check(
                        "nvt_temperature_control",
                        "passed" if passed else "warning",
                        "medium",
                        "Average late-run temperature is near target" if passed else "Average late-run temperature is outside target tolerance",
                        f"target={target:.3g}, tolerance={tolerance:.3g}, late_average={tail_average:.3g}, deviation={deviation:.3g}",
                    )
                )
                interpretation_notes.append(
                    _note(
                        "NVT temperature control",
                        "supported" if passed else "needs_review",
                        (
                            "Late-run temperature is near the configured target, supporting the thermostat-control interpretation."
                            if passed
                            else "Late-run temperature differs from the configured target enough to require discussion."
                        ),
                        f"target={target:.3g}, tolerance={tolerance:.3g}, late_average={tail_average:.3g}",
                    )
                )
        if validation_profile == "nve_energy_conservation" and "TotEng" in rows[0] and len(rows) > 1:
            initial = rows[0]["TotEng"]
            final = rows[-1]["TotEng"]
            relative = abs(final - initial) / max(abs(initial), 1e-9)
            threshold = float(validation_settings.get("energy_drift_warning_threshold", 0.05))
            interpretation_notes.append(
                _note(
                    "Energy conservation",
                    "needs_review" if relative > threshold else "supported",
                    (
                        "Total-energy drift is large enough to question timestep stability or setup choices."
                        if relative > threshold
                        else "Total-energy drift is small for this parsed NVE sample, supporting the timestep-stability interpretation."
                    ),
                    f"initial={initial:.6g}, final={final:.6g}, relative={relative:.3g}, threshold={threshold:.3g}",
                )
            )
            checks.append(
                _check(
                    "energy_drift",
                    "warning" if relative > threshold else "passed",
                    "medium",
                    "Estimated total-energy drift",
                    f"initial={initial:.6g}, final={final:.6g}, relative={relative:.3g}, threshold={threshold:.3g}",
                )
            )
        if "Press" in rows[0]:
            pressures = [row["Press"] for row in rows if "Press" in row]
            interpretation_notes.append(
                _note(
                    "Pressure interpretation",
                    "needs_review",
                    "Instantaneous pressure can fluctuate strongly; interpret pressure with averaging and physical context rather than a single pass/fail threshold.",
                    f"min={min(pressures):.3g}, max={max(pressures):.3g}" if pressures else "Press column detected",
                )
            )
            checks.append(
                _check(
                    "pressure_note",
                    "needs_review",
                    "low",
                    "Pressure can fluctuate strongly; verify averaging in the interpretation",
                    "Press column detected",
                )
            )
        if "Volume" in rows[0]:
            volumes = [row["Volume"] for row in rows if "Volume" in row]
            positive = all(volume > 0 for volume in volumes)
            interpretation_notes.append(
                _note(
                    "Volume sanity",
                    "supported" if positive else "concern",
                    "Volumes are positive in the parsed thermo data." if positive else "A non-positive volume appears in the thermo data.",
                    f"min={min(volumes):.3g}, max={max(volumes):.3g}" if volumes else "",
                )
            )
            checks.append(
                _check(
                    "volume_sanity",
                    "passed" if positive else "failed",
                    "high",
                    "Volumes are positive" if positive else "Non-positive volume detected",
                    str(volumes[:8]),
                )
            )

    extra_checks, extra_notes = _multi_log_comparison(parsed_logs)
    checks.extend(extra_checks)
    interpretation_notes.extend(extra_notes)

    status = "passed"
    if any(check["status"] == "failed" for check in checks):
        status = "failed"
    elif any(check["status"] in {"warning", "needs_review"} for check in checks):
        status = "warning"

    report = ValidationReport(
        submission_id=submission.id,
        status=status,
        summary=f"Automated validation completed with status: {status} using profile: {validation_profile}. This is advisory evidence, not a grade.",
        validation_profile=validation_profile,
        thermo_json=json.dumps(thermo_series),
        interpretation_json=json.dumps(interpretation_notes),
    )
    report.checks = [ValidationCheck(**check) for check in checks]
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
