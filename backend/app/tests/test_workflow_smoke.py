from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.services.seed_data import seed


ROOT = Path(__file__).resolve().parents[3]


def test_student_to_instructor_lab3_workflow(tmp_path):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = testing_session()
    seed(db)
    db.close()

    settings = get_settings()
    original_upload_root = settings.upload_root
    settings.upload_root = tmp_path / "uploads"
    settings.upload_root.mkdir(parents=True, exist_ok=True)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            student_login = client.post(
                "/api/auth/login",
                json={"email": "student@example.edu", "password": "password123"},
            )
            assert student_login.status_code == 200
            student_headers = {"Authorization": f"Bearer {student_login.json()['access_token']}"}

            assignments = client.get("/api/assignments", headers=student_headers)
            assert assignments.status_code == 200
            assignment_id = assignments.json()[0]["id"]

            project = client.post(
                "/api/projects",
                headers=student_headers,
                json={
                    "title": "Lab 3 smoke-test project",
                    "material_system": "Lennard-Jones teaching sample",
                    "research_question": "Does the sample NVE log conserve total energy?",
                    "physical_property": "Total-energy drift",
                    "ensemble": "NVE",
                    "validation_strategy": "Inspect errors, warnings, thermo data, and energy drift.",
                },
            )
            assert project.status_code == 200
            project_id = project.json()["id"]

            prompt_log = client.post(
                "/api/prompt-logs",
                headers=student_headers,
                json={
                    "title": "Smoke-test AI disclosure",
                    "project_id": project_id,
                    "assignment_id": assignment_id,
                    "ai_tool_name": "ChatGPT",
                    "task_type": "lammps_debugging",
                    "prompt_text": "Help inspect a LAMMPS NVE log for energy drift.",
                    "ai_output_summary": "Suggested checking log health and thermo trends.",
                    "accepted_parts": "Used validation checklist.",
                    "rejected_parts": "Did not accept unverified simulation conclusions.",
                    "manual_edits": "Adapted to Lab 3.",
                    "validation_performed": "Ran platform validation.",
                    "remaining_concerns": "Pressure still needs interpretation.",
                },
            )
            assert prompt_log.status_code == 200

            submission = client.post(
                "/api/submissions",
                headers=student_headers,
                json={
                    "assignment_id": assignment_id,
                    "project_id": project_id,
                    "title": "Lab 3 smoke-test package",
                },
            )
            assert submission.status_code == 200
            submission_id = submission.json()["id"]

            for file_type, filename in [
                ("lammps_input", "sample_input.in"),
                ("lammps_log", "sample_good_nve.log"),
            ]:
                with (ROOT / "sample_data" / filename).open("rb") as handle:
                    upload = client.post(
                        f"/api/submissions/{submission_id}/files?file_type={file_type}",
                        headers=student_headers,
                        files={"upload": (filename, handle, "text/plain")},
                    )
                assert upload.status_code == 200

            validation = client.post(f"/api/validation/submissions/{submission_id}", headers=student_headers)
            assert validation.status_code == 200
            validation_body = validation.json()
            assert validation_body["status"] == "warning"
            assert not [check for check in validation_body["checks"] if check["status"] == "failed"]
            assert any(check["check_type"] == "energy_drift" for check in validation_body["checks"])
            assert validation_body["thermo_series"]
            assert "TotEng" in validation_body["thermo_series"][0]["columns"]

            interpretation = client.patch(
                f"/api/submissions/{submission_id}/interpretation",
                headers=student_headers,
                json={
                    "student_interpretation": (
                        "Energy drift is small in the sample log, while pressure requires advisory review."
                    )
                },
            )
            assert interpretation.status_code == 200

            submitted = client.post(f"/api/submissions/{submission_id}/submit", headers=student_headers)
            assert submitted.status_code == 200
            assert submitted.json()["status"] == "submitted"

            package = client.get(f"/api/submissions/{submission_id}/package", headers=student_headers)
            assert package.status_code == 200
            assert package.headers["content-type"] == "application/zip"
            assert b"README.md" in package.content
            assert b"validation_report.json" in package.content
            with ZipFile(BytesIO(package.content)) as zf:
                validation_report = json.loads(zf.read("validation_report.json"))
            assert validation_report["thermo_series"]

            instructor_login = client.post(
                "/api/auth/login",
                json={"email": "instructor@example.edu", "password": "password123"},
            )
            assert instructor_login.status_code == 200
            instructor_headers = {"Authorization": f"Bearer {instructor_login.json()['access_token']}"}

            instructor_submissions = client.get("/api/instructor/submissions", headers=instructor_headers)
            assert instructor_submissions.status_code == 200
            assert instructor_submissions.json()[0]["status"] == "submitted"

            criteria = assignments.json()[0]["criteria"]
            grade = client.post(
                "/api/instructor/grades",
                headers=instructor_headers,
                json={
                    "submission_id": submission_id,
                    "late_penalty": 0,
                    "feedback": "Automated smoke-test grade.",
                    "criterion_scores": [
                        {"criterion_id": criterion["id"], "score": criterion["max_points"], "comment": "ok"}
                        for criterion in criteria
                    ],
                },
            )
            assert grade.status_code == 200
            assert grade.json()["final_score"] == 100

            gradebook = client.get("/api/instructor/gradebook.csv", headers=instructor_headers)
            assert gradebook.status_code == 200
            assert "student@example.edu" in gradebook.text
            assert "100.0" in gradebook.text
    finally:
        app.dependency_overrides.pop(get_db, None)
        settings.upload_root = original_upload_root
