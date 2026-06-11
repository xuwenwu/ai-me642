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
            assignment = next(item for item in assignments.json() if item["validation_profile"] == "nve_energy_conservation")
            assert assignment["interpretation_prompts"]
            assignment_id = assignment["id"]

            public_policy = client.get("/api/prompt-logs/policy", headers=student_headers)
            assert public_policy.status_code == 200
            assert public_policy.json()["disclosure_requirements"]
            assert "Responsible AI" in public_policy.json()["title"]

            public_templates = client.get("/api/prompt-logs/templates", headers=student_headers)
            assert public_templates.status_code == 200
            assert any(item["task_type"] == "lammps_debugging" for item in public_templates.json())

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
            assert validation_body["interpretation_notes"]
            assert any(note["topic"] == "Energy conservation" for note in validation_body["interpretation_notes"])

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
            assert validation_report["interpretation_notes"]

            instructor_login = client.post(
                "/api/auth/login",
                json={"email": "instructor@example.edu", "password": "password123"},
            )
            assert instructor_login.status_code == 200
            instructor_headers = {"Authorization": f"Bearer {instructor_login.json()['access_token']}"}

            instructor_submissions = client.get("/api/instructor/submissions", headers=instructor_headers)
            assert instructor_submissions.status_code == 200
            assert instructor_submissions.json()[0]["status"] == "submitted"

            analytics = client.get("/api/instructor/analytics", headers=instructor_headers)
            assert analytics.status_code == 200
            analytics_body = analytics.json()
            lab3_summary = next(item for item in analytics_body["assignments"] if item["assignment_id"] == assignment_id)
            assert analytics_body["total_students"] == 2
            assert analytics_body["ai_disclosure_missing_count"] >= 0
            assert lab3_summary["submitted_count"] == 1
            assert lab3_summary["missing_count"] == 1
            assert lab3_summary["validation_warning_count"] == 1
            assert lab3_summary["ai_disclosure_missing_count"] == 0
            assert lab3_summary["ungraded_submitted_count"] == 1
            assert analytics_body["needs_attention"]

            roster = client.get("/api/instructor/roster", headers=instructor_headers)
            assert roster.status_code == 200
            assert {student["email"] for student in roster.json()} == {"student@example.edu", "student2@example.edu"}
            assert all(student["section"] == "Pilot Section A" for student in roster.json())

            managed_assignment = client.post(
                "/api/instructor/assignments",
                headers=instructor_headers,
                json={
                    "title": "Lab 4: Phase IV Authoring Smoke",
                    "description": "Instructor-authored assignment from the smoke test.",
                    "assignment_type": "lab",
                    "due_date": "2026-03-17",
                    "total_points": 50,
                    "status": "published",
                    "validation_profile": "lammps_basic_health",
                    "required_file_types": ["lammps_input", "lammps_log"],
                    "optional_file_types": ["readme", "prompt_log"],
                    "validation_settings": {},
                    "interpretation_prompts": ["What changed after instructor setup?"],
                },
            )
            assert managed_assignment.status_code == 200
            managed_body = managed_assignment.json()
            assert managed_body["title"] == "Lab 4: Phase IV Authoring Smoke"
            assert managed_body["criteria"]

            edited_assignment = client.patch(
                f"/api/instructor/assignments/{managed_body['id']}",
                headers=instructor_headers,
                json={**managed_body, "title": "Lab 4: Edited Authoring Smoke", "optional_file_types": ["readme", "figure"]},
            )
            assert edited_assignment.status_code == 200
            assert edited_assignment.json()["title"] == "Lab 4: Edited Authoring Smoke"
            assert edited_assignment.json()["optional_file_types"] == ["readme", "figure"]

            visible_assignments = client.get("/api/assignments", headers=student_headers)
            assert visible_assignments.status_code == 200
            assert any(item["title"] == "Lab 4: Edited Authoring Smoke" for item in visible_assignments.json())

            instructor_policy = client.get("/api/instructor/ai-policy", headers=instructor_headers)
            assert instructor_policy.status_code == 200
            policy_payload = instructor_policy.json()
            edited_policy = client.patch(
                "/api/instructor/ai-policy",
                headers=instructor_headers,
                json={
                    **policy_payload,
                    "body": policy_payload["body"] + " Smoke-test policy update.",
                    "allowed_tools": policy_payload["allowed_tools"] + ["ME642 Test Assistant"],
                },
            )
            assert edited_policy.status_code == 200
            assert "Smoke-test policy update" in edited_policy.json()["body"]

            managed_template = client.post(
                "/api/instructor/prompt-templates",
                headers=instructor_headers,
                json={
                    "title": "Smoke template",
                    "task_type": "data_analysis",
                    "prompt_text": "Help check evidence before interpreting data.",
                    "checklist": ["Check units", "State uncertainty"],
                    "status": "active",
                },
            )
            assert managed_template.status_code == 200
            edited_template = client.patch(
                f"/api/instructor/prompt-templates/{managed_template.json()['id']}",
                headers=instructor_headers,
                json={**managed_template.json(), "title": "Edited smoke template"},
            )
            assert edited_template.status_code == 200
            student_templates = client.get("/api/prompt-logs/templates", headers=student_headers)
            assert any(item["title"] == "Edited smoke template" for item in student_templates.json())

            roster_student = client.post(
                "/api/instructor/roster/students",
                headers=instructor_headers,
                json={"full_name": "Katherine Student", "email": "student3@example.edu", "section": "Pilot Section B", "password": "password123"},
            )
            assert roster_student.status_code == 200
            assert roster_student.json()["section"] == "Pilot Section B"

            roster_import = client.post(
                "/api/instructor/roster/import",
                headers=instructor_headers,
                json={"csv_text": "full_name,email,section\nNia Student,student4@example.edu,Pilot Section B\n", "default_section": "Pilot Section A"},
            )
            assert roster_import.status_code == 200
            assert roster_import.json()["created_count"] == 1

            criteria = assignment["criteria"]
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

            graded_analytics = client.get("/api/instructor/analytics", headers=instructor_headers)
            assert graded_analytics.status_code == 200
            graded_lab3_summary = next(item for item in graded_analytics.json()["assignments"] if item["assignment_id"] == assignment_id)
            assert graded_lab3_summary["graded_count"] == 1
            assert graded_lab3_summary["ungraded_submitted_count"] == 0

            gradebook = client.get(
                f"/api/instructor/gradebook.csv?assignment_id={assignment_id}&grade_state=graded",
                headers=instructor_headers,
            )
            assert gradebook.status_code == 200
            assert "student@example.edu" in gradebook.text
            assert "Pilot Section A" in gradebook.text
            assert "100.0" in gradebook.text
    finally:
        app.dependency_overrides.pop(get_db, None)
        settings.upload_root = original_upload_root
