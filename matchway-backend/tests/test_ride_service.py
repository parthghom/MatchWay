import pytest
from app.engine.ride_service import RideService
from app.engine.driver_dispatch import DriverDispatcher
from app.models.rider import Rider
from app.models.ride_request import RideRequest
from app.models.driver import Driver

def test_ride_service_basic_flow():
    dispatcher = DriverDispatcher()
    service = RideService(dispatcher)

    # Two compatible riders
    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]

    r2 = Rider(id="r2", name="B", gender="male", preference="mix")
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=120, time_window_end=220)
    route2 = ["Stop1", "Stop2", "Stop4"]

    res1 = service.request_ride(r1, req1, route1, 12.0, 77.0, 10.0)
    res2 = service.request_ride(r2, req2, route2, 12.0, 77.0, 12.0)

    assert res1.room_id == res2.room_id
    assert res1.fare_range[0] <= res1.fare_range[1]
    assert "r1" in res2.matches

def test_ride_service_blocking():
    dispatcher = DriverDispatcher()
    service = RideService(dispatcher)

    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]

    r2 = Rider(id="r2", name="B", gender="male", preference="mix")
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route2 = ["Stop1", "Stop2", "Stop4"]

    # r1 blocks r2
    service.reviews.submit_review("r1", "r2", 1)

    res1 = service.request_ride(r1, req1, route1, 12.0, 77.0, 10.0)
    res2 = service.request_ride(r2, req2, route2, 12.0, 77.0, 10.0)

    assert res1.room_id != res2.room_id

def test_ride_service_confirm_and_dispatch():
    dispatcher = DriverDispatcher()
    service = RideService(dispatcher)

    # Setup driver
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)

    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]

    res = service.request_ride(r1, req1, route1, 12.0, 77.0, 10.0)

    ride = service.confirm_ride(res.room_id)
    assert ride is not None
    assert ride.driver_id == "d1"
    assert ride.status == "confirmed"
    assert len(ride.otp) == 4
    assert d1.is_busy is True

def test_ride_service_no_driver():
    dispatcher = DriverDispatcher()
    service = RideService(dispatcher)

    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]

    res = service.request_ride(r1, req1, route1, 12.0, 77.0, 10.0)

    # No drivers in system
    ride = service.confirm_ride(res.room_id)
    assert ride is None

    # Room should still be open
    room = service.rooms_by_id.get(res.room_id)
    assert room.closed is False

def test_ride_service_closed_room_new_room():
    dispatcher = DriverDispatcher()
    service = RideService(dispatcher)

    # Driver for room 1
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)

    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]

    res1 = service.request_ride(r1, req1, route1, 12.0, 77.0, 10.0)
    service.confirm_ride(res1.room_id)

    # r2 is compatible but room 1 is closed
    r2 = Rider(id="r2", name="B", gender="male", preference="mix")
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route2 = ["Stop1", "Stop2", "Stop4"]

    res2 = service.request_ride(r2, req2, route2, 12.0, 77.0, 10.0)
    assert res2.room_id != res1.room_id

def test_ride_service_errors():
    dispatcher = DriverDispatcher()
    service = RideService(dispatcher)

    with pytest.raises(KeyError):
        service.confirm_ride("unknown_room")

    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]
    res = service.request_ride(r1, req1, route1, 12.0, 77.0, 10.0)

    # Confirm once
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)
    service.confirm_ride(res.room_id)

    # Confirm twice
    with pytest.raises(ValueError):
        service.confirm_ride(res.room_id)
