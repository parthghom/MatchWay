import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import state

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh():
    state.reset()


def online(driver_id, lat, lon, vehicle="cab", name=None):
    return client.post("/drivers/location", json={
        "driver_id": driver_id, "name": name or driver_id, "vehicle_type": vehicle,
        "latitude": lat, "longitude": lon})


def book(rider_id="r1", vehicle="cab", km=8.0):
    res = client.post("/rides/request", json={
        "rider": {"id": rider_id, "name": "Asha", "gender": "female", "preference": "mix"},
        "request": {"id": "q" + rider_id, "rider_id": rider_id, "flow": "campus_to_destination",
                    "destination": "Mall", "vehicle_type": vehicle, "time_window_start": 600, "time_window_end": 660},
        "route": ["Gate", "Mall"], "pickup_lat": 18.5, "pickup_lon": 73.8, "km": km,
        "pickup_name": "College Gate", "drop_lat": 18.55, "drop_lon": 73.9, "drop_name": "Mall",
    })
    return res.json()["room_id"]


def test_offer_shows_pickup_drop_fare_and_people_then_accept_gives_otp():
    online("d1", 18.5005, 73.8005)
    room = book()
    first = client.post("/rides/confirm", json={"room_id": room}).json()
    assert first == {"confirmed": False, "offered": True, "message": "Waiting for the driver to accept"}

    offer = client.get("/drivers/d1/ride").json()
    assert offer["status"] == "offered"
    assert offer["pickup"]["name"] == "College Gate" and offer["drop"]["name"] == "Mall"
    assert offer["riders"] == 1 and offer["rider_names"] == ["Asha"]
    assert offer["total_fare"] == 200.0          # cab 8 km: 40 + 20*8
    assert offer["seconds_left"] > 0

    # nothing for riders to start with until he accepts
    assert client.post("/rides/start", json={"ride_id": offer["ride_id"], "otp": "0000"}).status_code == 400

    ok = client.post("/rides/driver/accept", json={"ride_id": offer["ride_id"], "driver_id": "d1"})
    assert ok.status_code == 200
    done = client.post("/rides/confirm", json={"room_id": room}).json()
    assert done["confirmed"] is True and len(done["otp"]) == 4 and done["driver_name"] == "d1"

    # driver types the OTP, trip starts, driver completes, riders see the payment
    assert client.get("/drivers/d1/ride").json()["status"] == "confirmed"
    assert client.post("/rides/start", json={"ride_id": done["ride_id"], "otp": done["otp"]}).status_code == 200
    assert client.get(f"/rides/{done['ride_id']}").json()["status"] == "in_progress"
    assert client.post("/rides/complete", json={"ride_id": done["ride_id"]}).status_code == 200
    final = client.get(f"/rides/{done['ride_id']}").json()
    assert final["status"] == "completed" and final["payments"] == [{"rider_id": "r1", "amount": 200.0}]
    assert client.get("/drivers/d1/ride").json() is None


def test_reject_goes_to_next_driver_and_rejecter_is_not_asked_again():
    online("near", 18.5002, 73.8002)
    online("far", 18.51, 73.81)
    room = book()
    client.post("/rides/confirm", json={"room_id": room})
    assert client.get("/drivers/near/ride").json()["status"] == "offered"
    assert client.get("/drivers/far/ride").json() is None

    r = client.post("/rides/driver/reject", json={"ride_id": client.get("/drivers/near/ride").json()["ride_id"], "driver_id": "near"})
    assert r.status_code == 200
    assert client.get("/drivers/near/ride").json() is None

    client.post("/rides/confirm", json={"room_id": room})        # riders poll again
    assert client.get("/drivers/far/ride").json()["status"] == "offered"
    assert client.get("/drivers/near/ride").json() is None


def test_no_answer_expires_the_offer():
    online("d1", 18.5005, 73.8005)
    online("d2", 18.51, 73.81)
    room = book()
    svc = state.current.rides
    svc.request_driver(room, now=1000)
    assert svc.ride_for_room(room).driver_id == "d1"
    svc.request_driver(room, now=1031)                           # 31 s later, nobody answered
    assert svc.ride_for_room(room).driver_id == "d2"
    with pytest.raises(ValueError):
        svc.driver_accept(svc.ride_for_room(room).ride_id, "d1")  # not his ride any more


def test_busy_driver_keeps_busy_when_location_updates_and_cannot_go_offline():
    online("d1", 18.5005, 73.8005)
    room = book()
    client.post("/rides/confirm", json={"room_id": room})
    assert online("d1", 18.501, 73.801).json()["is_busy"] is True
    assert client.post("/drivers/offline", json={"driver_id": "d1"}).status_code == 400


def test_rider_can_cancel_while_only_offered():
    online("d1", 18.5005, 73.8005)
    room = book()
    client.post("/rides/confirm", json={"room_id": room})
    assert client.post("/rides/cancel", json={"rider_id": "r1"}).status_code == 200
    assert client.get("/drivers/d1/ride").json() is None
    assert client.get("/drivers/nearby", params={"lat": 18.5, "lon": 73.8, "vehicle_type": "cab"}).json()["count"] == 1


def test_riders_see_the_drivers_live_position():
    online("d1", 18.5005, 73.8005)
    room = book()
    client.post("/rides/confirm", json={"room_id": room})
    ride_id = client.get("/drivers/d1/ride").json()["ride_id"]
    client.post("/rides/driver/accept", json={"ride_id": ride_id, "driver_id": "d1"})
    seen = client.get(f"/rides/{ride_id}").json()
    assert (seen["driver_lat"], seen["driver_lon"]) == (18.5005, 73.8005)
    online("d1", 18.52, 73.83)                       # the vehicle moves
    seen = client.get(f"/rides/{ride_id}").json()
    assert (seen["driver_lat"], seen["driver_lon"]) == (18.52, 73.83)
