import pytest
from app.models.rider import Rider
from app.models.ride_request import RideRequest
from app.models.driver import Driver
from app.engine.driver_dispatch import DriverDispatcher
from app.engine.ride_service import RideService
from app.engine.fare import vehicle_fare

def make_service():
    dispatcher = DriverDispatcher()
    driver = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.9716, longitude=77.5946)
    dispatcher.update_driver(driver)
    return RideService(dispatcher)

def request(service, rider_id, gender="male", preference="mix"):
    rider = Rider(id=rider_id, name=rider_id, gender=gender, preference=preference)
    req = RideRequest(id="q"+rider_id, rider_id=rider_id, flow="campus_to_destination",
                      destination="Mall", vehicle_type="cab", time_window_start=600,
                      time_window_end=660)
    result = service.request_ride(rider, req, ["Gate", "Road", "Mall"], 12.9716, 77.5946, 5.0)
    return result

def confirmed_ride(service, rider_ids):
    results = [request(service, rid) for rid in rider_ids]
    room_id = results[0].room_id
    for res in results[1:]:
        assert res.room_id == room_id
    return service.confirm_ride(room_id)

def test_wrong_otp(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1"])
    assert service.start_ride(ride.ride_id, "abcd") is False
    assert ride.status == "confirmed"

def test_right_otp(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1"])
    assert service.start_ride(ride.ride_id, ride.otp) is True
    assert ride.status == "in_progress"

def test_start_twice(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1"])
    service.start_ride(ride.ride_id, ride.otp)
    with pytest.raises(ValueError):
        service.start_ride(ride.ride_id, ride.otp)

def test_complete_before_start(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1"])
    with pytest.raises(ValueError):
        service.complete_ride(ride.ride_id)

def test_driver_release(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1"])
    service.start_ride(ride.ride_id, ride.otp)
    service.complete_ride(ride.ride_id)

    assert service.dispatcher.drivers.get("d1").is_busy is False

    res = request(service, "r3")
    ride2 = service.confirm_ride(res.room_id)
    assert ride2.driver_id == "d1"

def test_payment_sum(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1", "r2"])
    service.start_ride(ride.ride_id, ride.otp)
    payments = service.complete_ride(ride.ride_id)

    total = sum(p[1] for p in payments)
    assert round(total, 2) == round(vehicle_fare("cab", 5.0), 2)

def test_riders_removed_after_complete(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1"])
    service.start_ride(ride.ride_id, ride.otp)
    service.complete_ride(ride.ride_id)

    res = request(service, "r3")
    assert service.engine.find_matches("r3") == []

def test_review_score_update(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1", "r2"])
    service.start_ride(ride.ride_id, ride.otp)
    service.complete_ride(ride.ride_id)

    service.submit_review(ride.ride_id, "r1", "r2", 5)
    assert service.riders.get("r2").rider.compatibility_score == 3.6

def test_review_blocking(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1", "r2"])
    service.start_ride(ride.ride_id, ride.otp)
    service.complete_ride(ride.ride_id)

    service.submit_review(ride.ride_id, "r1", "r2", 1)

    # Fresh Rider objects, same IDs
    service2 = service_factory()
    # We need the block to persist across service instances if we use a real ReviewService
    # In our codebase, ReviewService is instantiated inside RideService.
    # To test this, we must use the SAME service instance but fresh requests.

    # Re-request with same IDs
    res1 = request(service, "r1")
    res2 = request(service, "r2")
    assert res1.room_id != res2.room_id

def test_review_before_completion(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1"])
    with pytest.raises(ValueError):
        service.submit_review(ride.ride_id, "r1", "d1", 5)

def test_review_invalid_participants(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1"])
    service.start_ride(ride.ride_id, ride.otp)
    service.complete_ride(ride.ride_id)

    with pytest.raises(ValueError):
        service.submit_review(ride.ride_id, "r1", "r99", 5)
    with pytest.raises(ValueError):
        service.submit_review(ride.ride_id, "r99", "d1", 5)

def test_duplicate_review(service_factory):
    service = service_factory()
    ride = confirmed_ride(service, ["r1", "r2"])
    service.start_ride(ride.ride_id, ride.otp)
    service.complete_ride(ride.ride_id)

    service.submit_review(ride.ride_id, "r1", "r2", 5)
    with pytest.raises(ValueError):
        service.submit_review(ride.ride_id, "r1", "r2", 5)

def test_unknown_ride_ids(service_factory):
    service = service_factory()
    with pytest.raises(KeyError):
        service.start_ride("unknown", "1234")
    with pytest.raises(KeyError):
        service.complete_ride("unknown")
    with pytest.raises(KeyError):
        service.submit_review("unknown", "r1", "r2", 5)

@pytest.fixture
def service_factory():
    return make_service
