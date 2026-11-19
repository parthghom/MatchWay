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


# ---- ratings belong to people (user ids), show up on the profile and steer matching ----

def _finished_ride(service, users):
    """users = {rider_id: user_id}. Everybody rides together; returns the completed ride."""
    results = []
    for rider_id, user_id in users.items():
        rider = Rider(id=rider_id, name=rider_id, gender="male", preference="mix")
        req = RideRequest(id="q" + rider_id, rider_id=rider_id, flow="campus_to_destination",
                          destination="Mall", vehicle_type="cab", time_window_start=600, time_window_end=660)
        results.append(service.request_ride(rider, req, ["Gate", "Road", "Mall"], 12.9716, 77.5946, 5.0, user_id=user_id))
    ride = service.confirm_ride(results[0].room_id)
    service.start_ride(ride.ride_id, ride.otp)
    service.complete_ride(ride.ride_id)
    return ride


def test_rating_follows_the_user_not_the_ride_id(service_factory):
    service = service_factory()
    ride = _finished_ride(service, {"r1": "userA", "r2": "userB"})
    service.submit_review(ride.ride_id, "r1", "r2", 5)
    assert service.reviews.get_score("userB") == 3.6
    assert service.rating_summary("userB") == {"score": 3.6, "count": 1}

    # next day userB books again with a brand new rider id: the rating is still there
    rider = Rider(id="r77", name="B again", gender="male", preference="mix")
    req = RideRequest(id="q77", rider_id="r77", flow="campus_to_destination", destination="Mall",
                      vehicle_type="cab", time_window_start=600, time_window_end=660)
    service.request_ride(rider, req, ["Gate", "Road", "Mall"], 12.9716, 77.5946, 5.0, user_id="userB")
    assert rider.compatibility_score == 3.6


def test_driver_review_updates_the_driver_rating(service_factory):
    service = service_factory()
    ride = _finished_ride(service, {"r1": "userA"})
    out = service.submit_review(ride.ride_id, "r1", "d1", 5)
    assert out["role"] == "driver" and out["count"] == 1
    assert service.rating_summary("d1") == {"score": 3.6, "count": 1}


def test_phone_cannot_choose_its_own_rating(service_factory):
    service = service_factory()
    rider = Rider(id="r1", name="Cheat", gender="male", preference="mix", compatibility_score=5.0)
    req = RideRequest(id="q1", rider_id="r1", flow="campus_to_destination", destination="Mall",
                      vehicle_type="cab", time_window_start=600, time_window_end=660)
    service.request_ride(rider, req, ["Gate", "Road", "Mall"], 12.9716, 77.5946, 5.0, user_id="userA")
    assert rider.compatibility_score == 3.0


def test_block_by_one_star_works_across_bookings_of_the_same_users(service_factory):
    service = service_factory()
    ride = _finished_ride(service, {"r1": "userA", "r2": "userB"})
    service.submit_review(ride.ride_id, "r1", "r2", 1)

    a = Rider(id="r10", name="A", gender="male", preference="mix")
    b = Rider(id="r11", name="B", gender="male", preference="mix")
    def req(rid):
        return RideRequest(id="q" + rid, rider_id=rid, flow="campus_to_destination", destination="Mall",
                           vehicle_type="cab", time_window_start=600, time_window_end=660)
    res_a = service.request_ride(a, req("r10"), ["Gate", "Road", "Mall"], 12.9716, 77.5946, 5.0, user_id="userA")
    res_b = service.request_ride(b, req("r11"), ["Gate", "Road", "Mall"], 12.9716, 77.5946, 5.0, user_id="userB")
    assert res_a.room_id != res_b.room_id


def test_riders_with_far_apart_ratings_are_not_grouped(service_factory):
    service = service_factory()
    service.reviews.scores.put("star", 4.8)
    service.reviews.scores.put("poor", 2.0)
    def go(rider_id, user_id):
        rider = Rider(id=rider_id, name=rider_id, gender="male", preference="mix")
        req = RideRequest(id="q" + rider_id, rider_id=rider_id, flow="campus_to_destination", destination="Mall",
                          vehicle_type="cab", time_window_start=600, time_window_end=660)
        return service.request_ride(rider, req, ["Gate", "Road", "Mall"], 12.9716, 77.5946, 5.0, user_id=user_id)
    assert go("r1", "star").room_id != go("r2", "poor").room_id


def test_room_status_shows_each_riders_rating(service_factory):
    service = service_factory()
    service.reviews.scores.put("userA", 4.2)
    rider = Rider(id="r1", name="A", gender="male", preference="mix")
    req = RideRequest(id="q1", rider_id="r1", flow="campus_to_destination", destination="Mall",
                      vehicle_type="cab", time_window_start=600, time_window_end=660)
    result = service.request_ride(rider, req, ["Gate", "Road", "Mall"], 12.9716, 77.5946, 5.0, user_id="userA")
    assert service.room_status(result.room_id)["members"][0]["rating"] == 4.2
