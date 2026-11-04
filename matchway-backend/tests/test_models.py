import pytest
from pydantic import ValidationError
from app.models.rider import Rider
from app.models.driver import Driver
from app.models.ride_request import RideRequest

def test_valid_models():
    # Valid Rider
    r = Rider(id="r1", name="Alice", gender="female", preference="female_only")
    assert r.id == "r1"

    # Valid Driver
    d = Driver(id="d1", name="Bob", vehicle_type="cab", latitude=12.97, longitude=77.59)
    assert d.vehicle_type == "cab"

    # Valid RideRequest
    req = RideRequest(
        id="req1",
        rider_id="r1",
        flow="campus_to_destination",
        destination="Airport",
        vehicle_type="cab",
        time_window_start=540,
        time_window_end=600
    )
    assert req.id == "req1"

def test_rider_gender_preference_rejection():
    # Male choosing female_only
    with pytest.raises(ValidationError):
        Rider(id="r1", name="Bob", gender="male", preference="female_only")

    # Female choosing male_only
    with pytest.raises(ValidationError):
        Rider(id="r2", name="Alice", gender="female", preference="male_only")

def test_invalid_vehicle_type():
    with pytest.raises(ValidationError):
        Driver(id="d1", name="Bob", vehicle_type="truck", latitude=12.97, longitude=77.59)

def test_invalid_time_window():
    with pytest.raises(ValidationError):
        RideRequest(
            id="req1",
            rider_id="r1",
            flow="campus_to_destination",
            destination="Airport",
            vehicle_type="cab",
            time_window_start=600,
            time_window_end=540
        )

def test_missing_pickup_spot():
    with pytest.raises(ValidationError):
        RideRequest(
            id="req1",
            rider_id="r1",
            flow="pickup_to_campus",
            destination="Campus",
            vehicle_type="cab",
            time_window_start=540,
            time_window_end=600
            # pickup_spot missing
        )
