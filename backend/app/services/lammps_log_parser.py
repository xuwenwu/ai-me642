from __future__ import annotations
from pathlib import Path
import re


THERMO_START_RE = re.compile(r"^\s*Step\s+")
NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$")
ERROR_RE = re.compile(r"^\s*ERROR(?::|\s+on|\s*$)", re.IGNORECASE)
WARNING_RE = re.compile(r"^\s*WARNING(?::|\s+on|\s*$)", re.IGNORECASE)


def _is_number(value: str) -> bool:
    return bool(NUMBER_RE.match(value))


def parse_lammps_log(path: Path) -> dict:
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    errors = [line.strip() for line in lines if ERROR_RE.match(line)]
    warnings = [line.strip() for line in lines if WARNING_RE.match(line)]
    completed = any("Loop time of" in line or "Total wall time:" in line for line in lines)
    sections: list[dict] = []
    columns_detected: set[str] = set()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not THERMO_START_RE.match(line):
            i += 1
            continue

        columns = line.split()
        rows: list[dict[str, float]] = []
        i += 1
        while i < len(lines):
            parts = lines[i].strip().split()
            if len(parts) != len(columns) or not parts or not all(_is_number(part) for part in parts):
                break
            row = {col: float(value) for col, value in zip(columns, parts)}
            rows.append(row)
            i += 1

        if rows:
            sections.append({"columns": columns, "rows": rows})
            columns_detected.update(columns)
        else:
            i += 1

    final_values = {}
    for section in reversed(sections):
        if section["rows"]:
            final_values = section["rows"][-1]
            break

    return {
        "path": str(path),
        "errors": errors,
        "warnings": warnings,
        "completed": completed,
        "sections": sections,
        "columns_detected": sorted(columns_detected),
        "final_values": final_values,
        "line_count": len(lines),
    }
