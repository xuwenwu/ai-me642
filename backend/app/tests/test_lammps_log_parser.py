from pathlib import Path
from app.services.lammps_log_parser import parse_lammps_log


ROOT = Path(__file__).resolve().parents[3]


def test_parse_good_log_detects_thermo_and_completion():
    parsed = parse_lammps_log(ROOT / "sample_data" / "sample_good_nve.log")

    assert parsed["completed"] is True
    assert parsed["errors"] == []
    assert "Step" in parsed["columns_detected"]
    assert "TotEng" in parsed["columns_detected"]
    assert parsed["final_values"]["Step"] == 500


def test_parse_error_log_surfaces_error_and_missing_completion():
    parsed = parse_lammps_log(ROOT / "sample_data" / "sample_error.log")

    assert parsed["completed"] is False
    assert parsed["errors"]
    assert "Lost atoms" in parsed["errors"][0]

