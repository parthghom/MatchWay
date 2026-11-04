from app.engine.verification import VerificationService

def test_email_verification():
    vs = VerificationService()
    # College email passes
    assert    vs.verify_email("u1", "test@college.edu.in")["passed"] is True
    # Gmail fails
    assert    vs.verify_email("u2", "test@gmail.com")["passed"] is False
    # Two @ fails
    assert    vs.verify_email("u3", "test@@college.edu.in")["passed"] is False
    # Case insensitive domain
    assert    vs.verify_email("u4", "test@COLLEGE.EDU.IN")["passed"] is True

def test_pin_extraction():
    vs = VerificationService()
    # 10 digits inside text
    assert vs.extract_pin("ID Number: 1234567890 Date: 2026") == "1234567890"
    # None when no 10-digit number
    assert vs.extract_pin("No pin here") is None
    assert vs.extract_pin("Short 12345") is None

def test_id_card_verification():
    vs = VerificationService()
    # PIN and Valid till 2027 passes in 2026
    assert    vs.verify_id_card("u1", "PIN 1234567890 Valid till 2027", 2026)["passed"] is True
    # Same card fails in 2028 (expired)
    assert    vs.verify_id_card("u2", "PIN 1234567890 Valid till 2027", 2028)["passed"] is False
    # PIN and no year passes
    assert    vs.verify_id_card("u3", "PIN 1234567890 some other text", 2026)["passed"] is True
    # No PIN fails
    assert    vs.verify_id_card("u4", "Valid till 2027", 2026)["passed"] is False

def test_licence_and_vehicle_verification():
    vs = VerificationService()
    # Licence
    assert    vs.verify_licence("u1", "MH12 20190001234")["passed"] is True
    assert    vs.verify_licence("u2", "hello")["passed"] is False
    # Vehicle
    assert    vs.verify_vehicle("u1", "MH12AB1234")["passed"] is True
    assert    vs.verify_vehicle("u2", "1234")["passed"] is False

def test_verification_status():
    vs = VerificationService()
    uid = "u1"

    # Student: only email step -> not verified
    vs.verify_email(uid, "test@college.edu.in")
    assert vs.is_verified_student(uid) is False

    # Student: all three -> verified
    vs.verify_id_card(uid, "1234567890", 2026)
    vs.verify_selfie(uid, True)
    assert vs.is_verified_student(uid) is True

    # Driver: needs its own steps
    # Currently u1 has email, id_card, selfie.
    # Needs licence and vehicle for driver.
    assert vs.is_verified_driver(uid) is False

    vs.verify_licence(uid, "MH12 20190001234")
    vs.verify_vehicle(uid, "MH12AB1234")
    # selfie is already passed
    assert vs.is_verified_driver(uid) is True

def test_duplicate_steps_and_reset():
    vs = VerificationService()
    uid = "u1"

    vs.verify_email(uid, "test@college.edu.in")
    vs.verify_email(uid, "test@college.edu.in")
    # Listed once
    assert vs.passed_steps(uid) == ["email"]

    # Reset clears everything
    vs.reset(uid)
    assert vs.passed_steps(uid) == []
    assert vs.is_verified_student(uid) is False
