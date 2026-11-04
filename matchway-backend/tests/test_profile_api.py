import pytest
from fastapi.testclient import TestClient
from app import main, state, auth
from app.storage.profile_repo import MemoryProfileRepository
from app.engine import onboarding

client = TestClient(main.app)

def test_onboarding_logic():
    # Test email_allowed_for_role
    assert onboarding.email_allowed_for_role("test@college.edu.in", "student") is True
    assert onboarding.email_allowed_for_role("TEST@COLLEGE.EDU.IN", "student") is True
    assert onboarding.email_allowed_for_role("test@gmail.com", "student") is False
    assert onboarding.email_allowed_for_role("test@gmail.com", "driver") is True
    assert onboarding.email_allowed_for_role("testgmail.com", "driver") is False
    assert onboarding.email_allowed_for_role("a@b@college.edu.in", "student") is False

    # Test next_step
    # Student
    assert onboarding.next_step("student", False, [], False) == "details"
    assert onboarding.next_step("student", True, [], False) == "college_id"
    assert onboarding.next_step("student", True, ["college_id"], False) == "selfie"
    assert onboarding.next_step("student", True, ["college_id", "selfie"], False) == "done"

    # Driver
    assert onboarding.next_step("driver", False, [], False) == "details"
    assert onboarding.next_step("driver", True, [], False) == "aadhaar"
    assert onboarding.next_step("driver", True, ["aadhaar"], False) == "pan"
    assert onboarding.next_step("driver", True, ["aadhaar", "pan"], False) == "licence"
    assert onboarding.next_step("driver", True, ["aadhaar", "pan", "licence"], False) == "vehicle"
    assert onboarding.next_step("driver", True, ["aadhaar", "pan", "licence"], True) == "rc"
    assert onboarding.next_step("driver", True, ["aadhaar", "pan", "licence", "rc"], True) == "vehicle_photo"
    assert onboarding.next_step("driver", True, ["aadhaar", "pan", "licence", "rc", "vehicle_photo"], True) == "done"

@pytest.fixture(autouse=True)
def setup_test():
    state.reset(repo=MemoryProfileRepository())
    # Manually inject the profile repo because state.reset only resets the main repo
    state.current.profiles = MemoryProfileRepository()

    def fake_verifier(token):
        if token == "student-token":
            return auth.AuthUser("u1", "a@college.edu.in")
        elif token == "gmail-token":
            return auth.AuthUser("u2", "x@gmail.com")
        else:
            raise Exception("Invalid token")

    auth.verifier = fake_verifier

def test_profile_auth():
    # No header
    resp = client.get("/profile/me")
    assert resp.status_code == 401

    # Bad token
    resp = client.get("/profile/me", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 401

def test_profile_me_new_user():
    resp = client.get("/profile/me", headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["exists"] is False
    assert data["next_step"] == "role"

def test_profile_set_role_student():
    # College email can become student
    resp = client.post("/profile/role", json={"role": "student"}, headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "student"

    # Same role again returns 200
    resp = client.post("/profile/role", json={"role": "student"}, headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 200

def test_profile_set_role_student_forbidden():
    # Gmail cannot become student
    resp = client.post("/profile/role", json={"role": "student"}, headers={"Authorization": "Bearer gmail-token"})
    assert resp.status_code == 403
    assert "college email" in resp.json()["detail"]

def test_profile_set_role_driver():
    # Gmail can become driver
    resp = client.post("/profile/role", json={"role": "driver"}, headers={"Authorization": "Bearer gmail-token"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "driver"

def test_profile_role_conflict():
    # Set student
    client.post("/profile/role", json={"role": "student"}, headers={"Authorization": "Bearer student-token"})
    # Try driver
    resp = client.post("/profile/role", json={"role": "driver"}, headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 409

def test_profile_details_success():
    # Set role first
    client.post("/profile/role", json={"role": "student"}, headers={"Authorization": "Bearer student-token"})

    body = {
        "full_name": "John Doe",
        "phone": "9876543210",
        "gender": "male",
        "date_of_birth": "2000-01-01"
    }
    resp = client.post("/profile/details", json=body, headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "John Doe"

    # Check next_step
    resp = client.get("/profile/me", headers={"Authorization": "Bearer student-token"})
    assert resp.json()["next_step"] == "college_id"

def test_profile_details_driver_age():
    # Set role driver
    client.post("/profile/role", json={"role": "driver"}, headers={"Authorization": "Bearer gmail-token"})

    # Under 18 (assuming today is 2026)
    body = {
        "full_name": "Young Driver",
        "phone": "9876543210",
        "gender": "male",
        "date_of_birth": "2010-01-01"
    }
    resp = client.post("/profile/details", json=body, headers={"Authorization": "Bearer gmail-token"})
    assert resp.status_code == 400

def test_profile_details_invalid_inputs():
    # Set role student
    client.post("/profile/role", json={"role": "student"}, headers={"Authorization": "Bearer student-token"})

    # Short name
    resp = client.post("/profile/details", json={"full_name": "A", "phone": "9876543210", "gender": "male", "date_of_birth": "2000-01-01"}, headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 400

    # Bad phone
    resp = client.post("/profile/details", json={"full_name": "John Doe", "phone": "123456789", "gender": "male", "date_of_birth": "2000-01-01"}, headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 400

    # Bad gender
    resp = client.post("/profile/details", json={"full_name": "John Doe", "phone": "9876543210", "gender": "other", "date_of_birth": "2000-01-01"}, headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 400

    # Future date
    resp = client.post("/profile/details", json={"full_name": "John Doe", "phone": "9876543210", "gender": "male", "date_of_birth": "2099-01-01"}, headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 400

def test_profile_details_no_role():
    # No role set
    resp = client.post("/profile/details", json={"full_name": "John Doe", "phone": "9876543210", "gender": "male", "date_of_birth": "2000-01-01"}, headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 404
