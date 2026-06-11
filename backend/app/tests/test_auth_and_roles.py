from fastapi.testclient import TestClient
from app.main import app


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
