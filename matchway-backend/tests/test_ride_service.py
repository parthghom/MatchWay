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


def test_cancel_request_leaves_room_and_matching():
    dispatcher = DriverDispatcher()
    service = RideService(dispatcher)
    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="q1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    r2 = Rider(id="r2", name="B", gender="male", preference="mix")
    req2 = RideRequest(id="q2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=120, time_window_end=220)
    service.request_ride(r1, req1, ["S1", "S2"], 12.0, 77.0, 10.0)
    service.cancel_request("r1")

    res2 = service.request_ride(r2, req2, ["S1", "S2"], 12.0, 77.0, 10.0)
    assert "r1" not in res2.matches                     # cancelled rider no longer matches
    with pytest.raises(KeyError):
        service.cancel_request("r1")                    # already cancelled


def test_cancel_request_not_allowed_after_driver_assigned():
    dispatcher = DriverDispatcher()
    dispatcher.update_driver(Driver(id="d1", name="D", vehicle_type="cab", latitude=12.0, longitude=77.0))
    service = RideService(dispatcher)
    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="q1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    res = service.request_ride(r1, req1, ["S1", "S2"], 12.0, 77.0, 10.0)
    assert service.confirm_ride(res.room_id) is not None
    with pytest.raises(ValueError):
        service.cancel_request("r1")


def _group_service(n, vehicle="auto"):
    service = RideService(DriverDispatcher())
    for i in range(1, n + 1):
        rider = Rider(id=f"r{i}", name=f"P{i}", gender="male", preference="mix")
        req = RideRequest(id=f"q{i}", rider_id=f"r{i}", flow="campus_to_destination", destination="Mall",
                          vehicle_type=vehicle, time_window_start=100, time_window_end=200)
        service.request_ride(rider, req, ["S1", "Mall"], 12.0, 77.0, 10.0)
        service.set_rider_user(f"r{i}", f"user{i}")
    return service


def test_group_two_riders_both_must_continue():
    service = _group_service(2)
    st = service.room_status("room_1", now=0)
    assert [m["name"] for m in st["members"]] == ["P1", "P2"] and st["members"][0]["user_id"] == "user1"
    assert st["seconds_left"] is None and st["ready"] is False        # not full: no timer

    st = service.vote_continue("r1", now=1)
    assert st["accepted"] == ["r1"] and st["ready"] is False
    st = service.vote_continue("r2", now=2)
    assert st["ready"] is True                                         # both agreed


def test_group_new_member_cancels_earlier_votes_and_closed_room_takes_nobody():
    service = _group_service(2)
    service.vote_continue("r1", now=1)
    # a third rider joins: r1's "continue with 2" no longer counts
    r3 = Rider(id="r3", name="P3", gender="male", preference="mix")
    q3 = RideRequest(id="q3", rider_id="r3", flow="campus_to_destination", destination="Mall",
                     vehicle_type="auto", time_window_start=100, time_window_end=200)
    service.request_ride(r3, q3, ["S1", "Mall"], 12.0, 77.0, 10.0)
    st = service.room_status("room_1", now=2)
    assert st["accepted"] == [] and len(st["members"]) == 3

    for rid in ("r1", "r2", "r3"):
        st = service.vote_continue(rid, now=3)
    assert st["ready"] is True
    r4 = Rider(id="r4", name="P4", gender="male", preference="mix")
    q4 = RideRequest(id="q4", rider_id="r4", flow="campus_to_destination", destination="Mall",
                     vehicle_type="auto", time_window_start=100, time_window_end=200)
    service.request_ride(r4, q4, ["S1", "Mall"], 12.0, 77.0, 10.0)
    assert service.room_of("r4").room_id != "room_1"                   # a closed room takes nobody new


def test_full_group_has_15_second_timer_and_resets():
    service = _group_service(3)                                         # auto holds 3
    assert service.room_status("room_1", now=100)["seconds_left"] == 15
    assert service.room_status("room_1", now=105)["seconds_left"] == 10
    service.vote_continue("r1", now=106)
    service.vote_continue("r2", now=107)
    st = service.room_status("room_1", now=116)                         # r3 never accepted: time is up
    assert st["accepted"] == [] and st["seconds_left"] == 15 and st["ready"] is False
    for rid in ("r1", "r2", "r3"):
        st = service.vote_continue(rid, now=118)
    assert st["ready"] is True and st["seconds_left"] is None


def test_alone_can_continue_and_cancel_clears_vote():
    service = _group_service(1)
    assert service.vote_continue("r1", now=0)["ready"] is True
    service2 = _group_service(2)
    service2.vote_continue("r1", now=0)
    service2.cancel_request("r1")
    assert service2.votes.contains("r1") is False
