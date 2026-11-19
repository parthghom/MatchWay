import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import state
from app.engine.stack import Stack
from app.engine.trip_history import TripHistory, MAX_TRIPS

client = TestClient(app)


def test_stack_is_last_in_first_out():
    s = Stack()
    assert s.is_empty()
    for x in (1, 2, 3):
        s.push(x)
    assert s.peek() == 3 and s.size() == 3
    assert s.to_list() == [3, 2, 1] and s.to_list(2) == [3, 2]
    assert s.pop() == 3 and s.to_list() == [2, 1]
    s.trim(1)
    assert s.to_list() == [2] and s.size() == 1
    s.trim(0)
    assert s.is_empty()
    with pytest.raises(IndexError):
        s.pop()
    with pytest.raises(IndexError):
        s.peek()


def test_history_newest_first_once_only_and_capped():
    h = TripHistory()
    assert h.get("rider", "u1") == []
    assert h.record("rider", "u1", {"id": "a"}) is True
    assert h.record("rider", "u1", {"id": "a"}) is False          # same ride twice
    h.record("rider", "u1", {"id": "b"})
    assert [t["id"] for t in h.get("rider", "u1")] == ["b", "a"]
    assert h.get("driver", "u1") == []                             # roles are separate
    assert h.record("rider", None, {"id": "x"}) is False
    for i in range(MAX_TRIPS + 10):
        h.record("rider", "u2", {"id": f"t{i}"})
    trips = h.get("rider", "u2")
    assert len(trips) == MAX_TRIPS and trips[0]["id"] == f"t{MAX_TRIPS + 9}"


@pytest.fixture(autouse=True)
def fresh():
    state.reset()


def test_finished_ride_shows_in_driver_and_rider_history_via_api():
    client.post("/drivers/location", json={"driver_id": "drv-1", "name": "Raj", "vehicle_type": "cab",
                                           "latitude": 18.5005, "longitude": 73.8005})

    def book(rid, uid):
        return client.post("/rides/request", json={
            "rider": {"id": rid, "name": rid, "gender": "female", "preference": "mix"},
            "request": {"id": "q" + rid, "rider_id": rid, "flow": "campus_to_destination", "destination": "Mall",
                        "vehicle_type": "cab", "time_window_start": 600, "time_window_end": 660},
            "route": ["Gate", "Mall"], "pickup_lat": 18.5, "pickup_lon": 73.8, "km": 8.0,
            "pickup_name": "College Gate", "drop_lat": 18.55, "drop_lon": 73.9, "drop_name": "Mall", "user_id": uid,
        }).json()["room_id"]

    room = book("r1", "user-1")
    client.post("/rooms/continue", json={"rider_id": "r1"})
    client.post("/rides/confirm", json={"room_id": room})
    ride_id = client.get("/drivers/drv-1/ride").json()["ride_id"]
    client.post("/rides/driver/accept", json={"ride_id": ride_id, "driver_id": "drv-1"})
    otp = client.post("/rides/confirm", json={"room_id": room}).json()["otp"]
    client.post("/rides/start", json={"ride_id": ride_id, "otp": otp})
    client.post("/rides/complete", json={"ride_id": ride_id})
    client.post("/rides/complete", json={"ride_id": ride_id})      # a second call must not add it twice

    mine = client.get("/history/rider/user-1").json()["trips"]
    assert len(mine) == 1 and mine[0]["fare"] == 200.0 and mine[0]["pickup"] == "College Gate" and mine[0]["drop"] == "Mall"
    drv = client.get("/history/driver/drv-1").json()["trips"]
    assert len(drv) == 1 and drv[0]["fare"] == 200.0 and drv[0]["riders"] == 1
    assert client.get("/history/driver/nobody").json() == {"trips": []}
    assert client.get("/history/admin/x").status_code == 404


def _finish_one_ride(user="user-9", driver="drv-9"):
    client.post("/drivers/location", json={"driver_id": driver, "name": "Raj", "vehicle_type": "cab",
                                           "latitude": 18.5005, "longitude": 73.8005})
    room = client.post("/rides/request", json={
        "rider": {"id": "r9", "name": "Asha", "gender": "female", "preference": "mix"},
        "request": {"id": "qr9", "rider_id": "r9", "flow": "campus_to_destination", "destination": "Mall",
                    "vehicle_type": "cab", "time_window_start": 600, "time_window_end": 660},
        "route": ["Gate", "Mall"], "pickup_lat": 18.5, "pickup_lon": 73.8, "km": 8.0,
        "pickup_name": "College Gate", "drop_lat": 18.55, "drop_lon": 73.9, "drop_name": "Mall", "user_id": user,
    }).json()["room_id"]
    client.post("/rooms/continue", json={"rider_id": "r9"})
    client.post("/rides/confirm", json={"room_id": room})
    ride_id = client.get(f"/drivers/{driver}/ride").json()["ride_id"]
    client.post("/rides/driver/accept", json={"ride_id": ride_id, "driver_id": driver})
    otp = client.post("/rides/confirm", json={"room_id": room}).json()["otp"]
    client.post("/rides/start", json={"ride_id": ride_id, "otp": otp})
    client.post("/rides/complete", json={"ride_id": ride_id})
    return ride_id


def test_stars_you_gave_show_up_in_your_history():
    ride_id = _finish_one_ride()
    import app.auth as auth
    old = auth.verifier
    auth.verifier = lambda token: auth.AuthUser("user-9", "a@vit.edu")   # pretend user-9 is signed in
    try:
        r = _review(ride_id)
    finally:
        auth.verifier = old
    assert r.status_code == 200, r.text
    trip = client.get("/history/rider/user-9").json()["trips"][0]
    assert trip["ratings"]["driver"]["stars"] == 4 and trip["ratings"]["riders"] == []


def _review(ride_id):
    return client.post("/rides/review", headers={"Authorization": "Bearer x"},
                       json={"ride_id": ride_id, "reviewer_id": "r9", "target_id": "drv-9", "stars": 4})


def test_history_comes_back_after_a_restart():
    from app.storage.memory_repo import MemoryRepository
    repo = MemoryRepository()
    state.reset(repo=repo)
    _finish_one_ride()
    assert len(client.get("/history/rider/user-9").json()["trips"]) == 1
    state.reset(repo=repo)               # the server restarts with the same saved data
    assert len(client.get("/history/rider/user-9").json()["trips"]) == 1
    assert len(client.get("/history/driver/drv-9").json()["trips"]) == 1
