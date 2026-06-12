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
