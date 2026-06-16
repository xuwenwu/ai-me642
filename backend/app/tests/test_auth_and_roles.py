from fastapi.testclient import TestClient
import pytest
from app.config import Settings, validate_runtime_security
from app.main import app


def test_health_reports_environment_and_security_headers():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["environment"] == "development"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "same-origin"


def test_readiness_checks_database_and_upload_root():
    with TestClient(app) as client:
        response = client.get("/api/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["checks"]["database"] == "ok"
        assert response.json()["checks"]["upload_root"] == "ok"


def test_production_runtime_rejects_unsafe_defaults():
    settings = Settings(app_env="production", secret_key="dev-secret-change-me", seed_demo_data=True)
    with pytest.raises(RuntimeError, match="Production configuration is not safe"):
        validate_runtime_security(settings)


def test_production_runtime_rejects_placeholder_secret():
    settings = Settings(
        app_env="production",
        secret_key="replace-with-at-least-32-random-characters",
        seed_demo_data=False,
        cors_origins_raw="https://course.example.edu",
    )
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_runtime_security(settings)


def test_production_runtime_accepts_hardened_settings():
    settings = Settings(
        app_env="production",
        secret_key="x" * 40,
        seed_demo_data=False,
        cors_origins_raw="https://course.example.edu",
    )
    validate_runtime_security(settings)


def test_seeded_student_login_and_staff_guard():
    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"email": "student@example.edu", "password": "password123"})
        assert login.status_code == 200
        token = login.json()["access_token"]

        staff_only = client.get("/api/instructor/submissions", headers={"Authorization": f"Bearer {token}"})
        assert staff_only.status_code == 403


def test_seeded_instructor_can_access_instructor_api():
    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"email": "instructor@example.edu", "password": "password123"})
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = client.get("/api/instructor/submissions", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200


def test_temporary_password_requires_change_before_app_use():
    with TestClient(app) as client:
        instructor_login = client.post("/api/auth/login", json={"email": "instructor@example.edu", "password": "password123"})
        instructor_headers = {"Authorization": f"Bearer {instructor_login.json()['access_token']}"}

        created = client.post(
            "/api/instructor/roster/students",
            headers=instructor_headers,
            json={
                "full_name": "Temporary Password Student",
                "email": "temporary-password@example.edu",
                "section": "Pilot Section A",
                "password": "temporary123",
                "must_change_password": True,
            },
        )
        assert created.status_code == 200
        assert created.json()["must_change_password"] is True

        login = client.post("/api/auth/login", json={"email": "temporary-password@example.edu", "password": "temporary123"})
        assert login.status_code == 200
        assert login.json()["user"]["must_change_password"] is True
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        blocked = client.get("/api/assignments", headers=headers)
        assert blocked.status_code == 403
        assert blocked.json()["detail"] == "Password change required"

        changed = client.post(
            "/api/auth/change-password",
            headers=headers,
            json={"current_password": "temporary123", "new_password": "student-new-pass-123"},
        )
        assert changed.status_code == 200
        assert changed.json()["must_change_password"] is False

        allowed = client.get("/api/assignments", headers=headers)
        assert allowed.status_code == 200


def test_instructor_can_reset_password_and_disable_student_account():
    with TestClient(app) as client:
        instructor_login = client.post("/api/auth/login", json={"email": "instructor@example.edu", "password": "password123"})
        instructor_headers = {"Authorization": f"Bearer {instructor_login.json()['access_token']}"}

        created = client.post(
            "/api/instructor/roster/students",
            headers=instructor_headers,
            json={
                "full_name": "Reset Target",
                "email": "reset-target@example.edu",
                "section": "Pilot Section A",
                "password": "temporary123",
                "must_change_password": False,
            },
        )
        assert created.status_code == 200
        student_id = created.json()["student_id"]

        reset = client.post(
            f"/api/instructor/roster/students/{student_id}/reset-password",
            headers=instructor_headers,
            json={"new_password": "reset-pass-123", "must_change_password": True},
        )
        assert reset.status_code == 200
        assert reset.json()["account_status"] == "password_change_required"

        login = client.post("/api/auth/login", json={"email": "reset-target@example.edu", "password": "reset-pass-123"})
        assert login.status_code == 200
        assert login.json()["user"]["must_change_password"] is True

        disabled = client.patch(
            f"/api/instructor/roster/students/{student_id}/account",
            headers=instructor_headers,
            json={"is_active": False, "must_change_password": False},
        )
        assert disabled.status_code == 200
        assert disabled.json()["account_status"] == "inactive"

        blocked_login = client.post("/api/auth/login", json={"email": "reset-target@example.edu", "password": "reset-pass-123"})
        assert blocked_login.status_code == 403


def test_seeded_assignments_include_phase2_validation_profiles():
    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"email": "student@example.edu", "password": "password123"})
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = client.get("/api/assignments", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assignments = response.json()
        profiles = {assignment["validation_profile"] for assignment in assignments}
        assert len(assignments) >= 3
        assert {"lammps_basic_health", "nvt_temperature_control", "nve_energy_conservation"} <= profiles
        assert all(assignment["required_file_types"] for assignment in assignments)
        assert all(assignment["interpretation_prompts"] for assignment in assignments)
