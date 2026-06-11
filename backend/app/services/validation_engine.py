from __future__ import annotations
import json
import math
from pathlib import Path
from sqlalchemy.orm import Session
from ..models import FileArtifact, PromptLogEntry, Submission, ValidationCheck, ValidationReport
from .lammps_log_parser import parse_lammps_log


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


def validate_submission(db: Session, submission: Submission) -> ValidationReport:
    files: list[FileArtifact] = list(submission.files)
    file_types = {file.file_type for file in files}
    checks: list[dict] = []
    thermo_series: list[dict] = []
    interpretation_notes: list[dict] = []

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

    present({"lammps_input"}, "LAMMPS input script", True)
    present({"lammps_log"}, "LAMMPS log", True)
    present({"readme"}, "README/reproducibility notes", False)
    present({"python_analysis", "ovito_script", "figure"}, "Analysis script, OVITO script, or figure", False)
    if "readme" not in file_types:
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
        if file.file_type != "lammps_log":
            continue
        parsed = parse_lammps_log(Path(file.file_path))
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
        if "TotEng" in rows[0] and len(rows) > 1:
            initial = rows[0]["TotEng"]
            final = rows[-1]["TotEng"]
            relative = abs(final - initial) / max(abs(initial), 1e-9)
            interpretation_notes.append(
                _note(
                    "Energy conservation",
                    "needs_review" if relative > 0.05 else "supported",
                    (
                        "Total-energy drift is large enough to question timestep stability or setup choices."
                        if relative > 0.05
                        else "Total-energy drift is small for this parsed NVE sample, supporting the timestep-stability interpretation."
                    ),
                    f"initial={initial:.6g}, final={final:.6g}, relative={relative:.3g}",
                )
            )
            checks.append(
                _check(
                    "energy_drift",
                    "warning" if relative > 0.05 else "passed",
                    "medium",
                    "Estimated total-energy drift",
                    f"initial={initial:.6g}, final={final:.6g}, relative={relative:.3g}",
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

    status = "passed"
    if any(check["status"] == "failed" for check in checks):
        status = "failed"
    elif any(check["status"] in {"warning", "needs_review"} for check in checks):
        status = "warning"

    report = ValidationReport(
        submission_id=submission.id,
        status=status,
        summary=f"Automated validation completed with status: {status}. This is advisory evidence, not a grade.",
        thermo_json=json.dumps(thermo_series),
        interpretation_json=json.dumps(interpretation_notes),
    )
    report.checks = [ValidationCheck(**check) for check in checks]
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
