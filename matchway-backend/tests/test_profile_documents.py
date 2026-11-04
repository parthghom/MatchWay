import pytest
import base64
from fastapi.testclient import TestClient
from app import main, state, auth
from app.storage.profile_repo import MemoryProfileRepository
from app.engine import onboarding

client = TestClient(main.app)

def test_onboarding_helpers():
    # PAN
    assert onboarding.clean_pan(" abcde1234f ") == "ABCDE1234F"
    with pytest.raises(ValueError, match="Enter a valid PAN"):
        onboarding.clean_pan("ABC123")

    # Licence
    assert onboarding.clean_licence("MH12 20190001234") == "MH12 20190001234"
    with pytest.raises(ValueError, match="Enter a valid driving licence number"):
        onboarding.clean_licence("hello")

    # Plate
    assert onboarding.clean_plate("mh 12 ab 1234") == "MH12AB1234"
    with pytest.raises(ValueError, match="Enter a valid vehicle number"):
        onboarding.clean_plate("1234")

    # College ID
    assert onboarding.clean_college_id("  STUD123  ") == "STUD123"
    with pytest.raises(ValueError, match="College ID must be 4 to 20"):
        onboarding.clean_college_id("A1")

    # Profile Status
    assert onboarding.profile_status("incomplete", ["approved"]) == "incomplete"
    assert onboarding.profile_status("done", ["approved", "approved"]) == "approved"
    assert onboarding.profile_status("done", ["approved", "pending"]) == "pending"
    assert onboarding.profile_status("done", ["approved", "rejected"]) == "rejected"

@pytest.fixture(autouse=True)
def setup_test(monkeypatch):
    state.reset(repo=MemoryProfileRepository())
    state.current.profiles = MemoryProfileRepository()
    monkeypatch.delenv("DEMO_AUTO_APPROVE", raising=False)

    def fake_verifier(token):
        if token == "student-token":
            return auth.AuthUser("u1", "a@college.edu.in")
        elif token == "gmail-token":
            return auth.AuthUser("u2", "x@gmail.com")
        elif token == "gmail2-token":
            return auth.AuthUser("u3", "y@gmail.com")
        else:
            raise Exception("Invalid token")

    auth.verifier = fake_verifier

def get_img_b64():
    return base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 20).decode()

def test_doc_before_details():
    resp = client.post("/profile/document",
                       json={"doc_type": "college_id", "image_base64": get_img_b64()},
                       headers={"Authorization": "Bearer student-token"})
    # User u1 has no role yet in this fresh state
    client.post("/profile/role", json={"role": "student"}, headers={"Authorization": "Bearer student-token"})
    resp = client.post("/profile/document",
                       json={"doc_type": "college_id", "image_base64": get_img_b64()},
                       headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 400
    assert "Complete your details first" in resp.json()["detail"]

def test_student_wrong_doc():
    client.post("/profile/role", json={"role": "student"}, headers={"Authorization": "Bearer student-token"})
    client.post("/profile/details", json={
        "full_name": "Student One", "phone": "9876543210", "gender": "male", "date_of_birth": "2000-01-01"
    }, headers={"Authorization": "Bearer student-token"})

    resp = client.post("/profile/document",
                       json={"doc_type": "pan", "image_base64": get_img_b64()},
                       headers={"Authorization": "Bearer student-token"})
    assert resp.status_code == 400
    assert "not needed for your role" in resp.json()["detail"]

def test_student_flow():
    headers = {"Authorization": "Bearer student-token"}
    client.post("/profile/role", json={"role": "student"}, headers=headers)
    client.post("/profile/details", json={
        "full_name": "Student One", "phone": "9876543210", "gender": "male", "date_of_birth": "2000-01-01"
    }, headers=headers)

    # College ID with number
    resp = client.post("/profile/document",
                      json={"doc_type": "college_id", "image_base64": get_img_b64(), "doc_number": "COL123"},
                      headers=headers)
    assert resp.status_code == 200
    assert resp.json()["next_step"] == "selfie"

    # Selfie
    resp = client.post("/profile/document",
                      json={"doc_type": "selfie", "image_base64": get_img_b64()},
                      headers=headers)
    assert resp.status_code == 200
    assert resp.json()["next_step"] == "done"

    # Check profile status
    resp = client.get("/profile/me", headers=headers)
    assert resp.json()["profile"]["status"] == "pending"

def test_invalid_images():
    headers = {"Authorization": "Bearer student-token"}
    client.post("/profile/role", json={"role": "student"}, headers=headers)
    client.post("/profile/details", json={
        "full_name": "Student One", "phone": "9876543210", "gender": "male", "date_of_birth": "2000-01-01"
    }, headers=headers)

    # Invalid base64
    resp = client.post("/profile/document",
                       json={"doc_type": "college_id", "image_base64": "not-base64!!!", "doc_number": "COL123"},
                       headers=headers)
    assert resp.status_code == 400
    assert "Invalid image" in resp.json()["detail"]

    # Text bytes
    resp = client.post("/profile/document",
                       json={"doc_type": "college_id", "image_base64": base64.b64encode(b"this is just text").decode(), "doc_number": "COL123"},
                       headers=headers)
    assert resp.status_code == 400
    assert "Invalid image" in resp.json()["detail"]

    # Too large (> 5MB)
    large_img = base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * (6 * 1024 * 1024)).decode()
    resp = client.post("/profile/document",
                       json={"doc_type": "college_id", "image_base64": large_img, "doc_number": "COL123"},
                       headers=headers)
    assert resp.status_code == 400
    assert "Image is too large" in resp.json()["detail"]

def test_driver_flow():
    headers = {"Authorization": "Bearer gmail-token"}
    client.post("/profile/role", json={"role": "driver"}, headers=headers)
    client.post("/profile/details", json={
        "full_name": "Driver One", "phone": "9876543210", "gender": "male", "date_of_birth": "1990-01-01"
    }, headers=headers)

    # Aadhaar with number -> 400
    resp = client.post("/profile/document",
                      json={"doc_type": "aadhaar", "image_base64": get_img_b64(), "doc_number": "123456789012"},
                      headers=headers)
    assert resp.status_code == 400
    assert "Aadhaar number is not collected" in resp.json()["detail"]

    # Aadhaar without number -> 200
    resp = client.post("/profile/document",
                      json={"doc_type": "aadhaar", "image_base64": get_img_b64()},
                      headers=headers)
    assert resp.status_code == 200

    # PAN
    resp = client.post("/profile/document",
                      json={"doc_type": "pan", "image_base64": get_img_b64(), "doc_number": "abcde1234f"},
                      headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

    # Licence
    resp = client.post("/profile/document",
                      json={"doc_type": "licence", "image_base64": get_img_b64(), "doc_number": "MH12 20190001234"},
                      headers=headers)
    assert resp.status_code == 200

def test_driver_vehicle_flow():
    headers = {"Authorization": "Bearer gmail-token"}
    client.post("/profile/role", json={"role": "driver"}, headers=headers)
    client.post("/profile/details", json={
        "full_name": "Driver One", "phone": "9876543210", "gender": "male", "date_of_birth": "1990-01-01"
    }, headers=headers)

    # Upload personal docs first
    for doc in ["aadhaar", "pan", "licence"]:
        num = None if doc == "aadhaar" else ("PAN12345F" if doc == "pan" else "MH12 20190001234")
        client.post("/profile/document",
                    json={"doc_type": doc, "image_base64": get_img_b64(), "doc_number": num},
                    headers=headers)

    # Set vehicle
    resp = client.post("/profile/vehicle",
                      json={"vehicle_type": "cab", "plate_number": "mh 12 ab 1234"},
                      headers=headers)
    assert resp.status_code == 200
    assert resp.json()["plate_number"] == "MH12AB1234"

    # RC and vehicle_photo
    resp = client.post("/profile/document",
                      json={"doc_type": "rc", "image_base64": get_img_b64()},
                      headers=headers)
    assert resp.status_code == 200

    resp = client.post("/profile/document",
                      json={"doc_type": "vehicle_photo", "image_base64": get_img_b64()},
                      headers=headers)
    assert resp.status_code == 200
    assert resp.json()["next_step"] == "done"

    # Check profile status
    resp = client.get("/profile/me", headers=headers)
    assert resp.json()["profile"]["status"] == "pending"

def test_student_add_vehicle():
    headers = {"Authorization": "Bearer student-token"}
    client.post("/profile/role", json={"role": "student"}, headers=headers)
    client.post("/profile/details", json={
        "full_name": "Student One", "phone": "9876543210", "gender": "male", "date_of_birth": "2000-01-01"
    }, headers=headers)

    resp = client.post("/profile/vehicle",
                      json={"vehicle_type": "cab", "plate_number": "MH12AB1234"},
                      headers=headers)
    assert resp.status_code == 403
    assert "Only drivers add vehicles" in resp.json()["detail"]

def test_vehicle_plate_collision():
    headers1 = {"Authorization": "Bearer gmail-token"}
    headers2 = {"Authorization": "Bearer gmail2-token"}

    # Driver 1 setup
    client.post("/profile/role", json={"role": "driver"}, headers=headers1)
    client.post("/profile/details", json={
        "full_name": "Driver One", "phone": "9876543210", "gender": "male", "date_of_birth": "1990-01-01"
    }, headers=headers1)
    for doc in ["aadhaar", "pan", "licence"]:
        num = None if doc == "aadhaar" else ("PAN12345F" if doc == "pan" else "MH12 20190001234")
        client.post("/profile/document",
                    json={"doc_type": doc, "image_base64": get_img_b64(), "doc_number": num},
                    headers=headers1)
    client.post("/profile/vehicle",
                      json={"vehicle_type": "cab", "plate_number": "MH12AB1234"},
                      headers=headers1)

    # Driver 2 setup
    client.post("/profile/role", json={"role": "driver"}, headers=headers2)
    client.post("/profile/details", json={
        "full_name": "Driver Two", "phone": "9876543210", "gender": "male", "date_of_birth": "1990-01-01"
    }, headers=headers2)
    for doc in ["aadhaar", "pan", "licence"]:
        num = None if doc == "aadhaar" else ("PAN12345F" if doc == "pan" else "MH12 20190001234")
        client.post("/profile/document",
                    json={"doc_type": doc, "image_base64": get_img_b64(), "doc_number": num},
                    headers=headers2)

    resp = client.post("/profile/vehicle",
                      json={"vehicle_type": "cab", "plate_number": "MH12AB1234"},
                      headers=headers2)
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"]

def test_demo_auto_approve():
    # Use monkeypatch to set env var
    import os
    os.environ["DEMO_AUTO_APPROVE"] = "true"
    headers = {"Authorization": "Bearer student-token"}
    client.post("/profile/role", json={"role": "student"}, headers=headers)
    client.post("/profile/details", json={
        "full_name": "Student One", "phone": "9876543210", "gender": "male", "date_of_birth": "2000-01-01"
    }, headers=headers)

    resp = client.post("/profile/document",
                      json={"doc_type": "college_id", "image_base64": get_img_b64(), "doc_number": "COL123"},
                      headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # All docs approved -> profile approved
    client.post("/profile/document",
                      json={"doc_type": "selfie", "image_base64": get_img_b64()},
                      headers=headers)

    resp = client.get("/profile/me", headers=headers)
    assert resp.json()["profile"]["status"] == "approved"

    # Clean up env
    del os.environ["DEMO_AUTO_APPROVE"]

def test_get_me_no_paths():
    headers = {"Authorization": "Bearer student-token"}
    client.post("/profile/role", json={"role": "student"}, headers=headers)
    client.post("/profile/details", json={
        "full_name": "Student One", "phone": "9876543210", "gender": "male", "date_of_birth": "2000-01-01"
    }, headers=headers)
    client.post("/profile/document",
                      json={"doc_type": "college_id", "image_base64": get_img_b64(), "doc_number": "COL123"},
                      headers=headers)

    resp = client.get("/profile/me", headers=headers)
    docs = resp.json()["documents"]
    for d in docs:
        assert "storage_path" not in d
