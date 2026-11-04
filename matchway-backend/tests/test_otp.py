from app.engine.otp import OTPService
import pytest

def test_otp_generation():
    service = OTPService()
    code = service.generate("ride123")
    assert len(code) == 4
    assert code.isdigit()

def test_otp_verification_cycle():
    service = OTPService()
    ride_id = "ride123"
    code = service.generate(ride_id)

    # Right code verifies once
    assert service.verify(ride_id, code) is True

    # Fails a second time
    assert service.verify(ride_id, code) is False

def test_otp_wrong_code():
    service = OTPService()
    ride_id = "ride123"
    service.generate(ride_id)

    assert service.verify(ride_id, "0000") is False

def test_otp_unknown_ride():
    service = OTPService()
    assert service.verify("unknown", "1234") is False
