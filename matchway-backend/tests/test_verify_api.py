import pytest
import base64
from fastapi.testclient import TestClient
from app.main import app
from app import state

client = TestClient(app)

def test_verify_email():
    state.reset()
    # College email passes
    resp = client.post("/verify/email", json={"user_id": "u1", "email": "student@college.edu"})
    assert resp.status_code == 200
    assert resp.json()["passed"] is True

    # Gmail fails
    resp = client.post("/verify/email", json={"user_id": "u1", "email": "student@gmail.com"})
    assert resp.status_code == 200
    assert resp.json()["passed"] is False

def test_verify_id_card():
    state.reset()

    def fake_ocr(img):
        if img == b"valid":
            return "1234567890 Valid till 2099"
        return "hello"

    state.current.ocr = fake_ocr

    # Valid ID passes
    img_valid = base64.b64encode(b"valid").decode()
    resp = client.post("/verify/id-card", json={"user_id": "u1", "image_base64": img_valid})
    assert resp.status_code == 200
    assert resp.json()["passed"] is True

    # Invalid ID fails
    img_invalid = base64.b64encode(b"invalid").decode()
    resp = client.post("/verify/id-card", json={"user_id": "u1", "image_base64": img_invalid})
    assert resp.status_code == 200
    assert resp.json()["passed"] is False

def test_verify_licence():
    state.reset()

    def fake_ocr(img):
        return "MH12 20190001234"

    state.current.ocr = fake_ocr

    img = base64.b64encode(b"x").decode()
    resp = client.post("/verify/licence", json={"user_id": "u1", "image_base64": img})
    assert resp.status_code == 200
    assert resp.json()["passed"] is True

def test_verify_vehicle():
    state.reset()

    def fake_ocr(img):
        return "MH12AB1234"

    state.current.ocr = fake_ocr

    img = base64.b64encode(b"x").decode()
    resp = client.post("/verify/vehicle", json={"user_id": "u1", "image_base64": img})
    assert resp.status_code == 200
    assert resp.json()["passed"] is True

def test_verify_selfie():
    state.reset()

    def fake_face(id_img, selfie_img):
        return id_img == b"match"

    state.current.face = fake_face

    # Match passes
    id_img = base64.b64encode(b"match").decode()
    selfie_img = base64.b64encode(b"match").decode()
    resp = client.post("/verify/selfie", json={"user_id": "u1", "id_image_base64": id_img, "selfie_base64": selfie_img})
    assert resp.status_code == 200
    assert resp.json()["passed"] is True

    # No match fails
    id_img = base64.b64encode(b"no").decode()
    selfie_img = base64.b64encode(b"no").decode()
    resp = client.post("/verify/selfie", json={"user_id": "u1", "id_image_base64": id_img, "selfie_base64": selfie_img})
    assert resp.status_code == 200
    assert resp.json()["passed"] is False

def test_verify_full_flow():
    state.reset()

    # Mock OCR and Face
    state.current.ocr = lambda img: "1234567890 Valid till 2099"
    state.current.face = lambda id, s: True

    # 1. Email
    client.post("/verify/email", json={"user_id": "u1", "email": "student@college.edu"})
    # 2. ID Card
    img = base64.b64encode(b"x").decode()
    client.post("/verify/id-card", json={"user_id": "u1", "image_base64": img})
    # 3. Selfie
    client.post("/verify/selfie", json={"user_id": "u1", "id_image_base64": img, "selfie_base64": img})

    resp = client.get("/verify/u1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "u1"
    assert data["student_verified"] is True
    assert data["driver_verified"] is False

def test_ocr_runtime_error():
    state.reset()

    def fake_ocr_error(img):
        raise RuntimeError("OCR is not installed")

    state.current.ocr = fake_ocr_error

    img = base64.b64encode(b"x").decode()
    resp = client.post("/verify/id-card", json={"user_id": "u1", "image_base64": img})
    assert resp.status_code == 503
    assert resp.json()["detail"] == "OCR is not installed"

def test_invalid_base64():
    state.reset()

    resp = client.post("/verify/id-card", json={"user_id": "u1", "image_base64": "not-base64!!!"})
    assert resp.status_code == 400
    assert "base64" in resp.json()["detail"].lower()
