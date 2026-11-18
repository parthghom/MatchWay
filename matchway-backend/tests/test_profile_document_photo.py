import base64
import pytest
from fastapi.testclient import TestClient
from app import main, state, auth
from app.storage.profile_repo import MemoryProfileRepository

client = TestClient(main.app)
JPEG = b"\xff\xd8\xff\xe0" + b"fake-jpeg-bytes"
HEAD = {"Authorization": "Bearer driver-token"}


@pytest.fixture(autouse=True)
def setup_test():
    state.reset(repo=MemoryProfileRepository())
    state.current.profiles = MemoryProfileRepository()

    def fake_verifier(token):
        if token == "driver-token":
            return auth.AuthUser("d1", "driver@gmail.com")
        raise Exception("Invalid token")

    auth.verifier = fake_verifier


def make_driver_with_aadhaar():
    client.post("/profile/role", json={"role": "driver"}, headers=HEAD)
    client.post("/profile/details", json={
        "full_name": "Test Driver", "phone": "9876543210",
        "gender": "male", "date_of_birth": "1995-01-01",
    }, headers=HEAD)
    client.post("/profile/document", json={
        "doc_type": "aadhaar", "image_base64": base64.b64encode(JPEG).decode(),
    }, headers=HEAD)


def test_get_own_document_photo():
    make_driver_with_aadhaar()
    resp = client.get("/profile/document/aadhaar", headers=HEAD)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.content == JPEG


def test_photo_not_uploaded_yet():
    make_driver_with_aadhaar()
    assert client.get("/profile/document/pan", headers=HEAD).status_code == 404


def test_photo_wrong_doc_type_for_role():
    make_driver_with_aadhaar()
    assert client.get("/profile/document/college_id", headers=HEAD).status_code == 400


def test_photo_needs_sign_in():
    assert client.get("/profile/document/aadhaar").status_code == 401
