# Ratings over the API: reviews after a ride, the profile rating, and rebuilding the scores after a restart.
import pytest
from fastapi.testclient import TestClient
from app import main, state, auth
from app.storage.memory_repo import MemoryRepository
from app.storage.profile_repo import MemoryProfileRepository

client = TestClient(main.app)

RIDER_A = {"Authorization": "Bearer token-a"}
RIDER_B = {"Authorization": "Bearer token-b"}
DRIVER = {"Authorization": "Bearer token-d"}


@pytest.fixture(autouse=True)
def setup_state():
    state.reset(repo=MemoryRepository())
    state.current.profiles = MemoryProfileRepository()
    users = {"token-a": ("userA", "a@college.edu.in"), "token-b": ("userB", "b@college.edu.in"),
             "token-d": ("driverD", "d@gmail.com")}
    old = auth.verifier
    def verifier(token):
        if token in users:
            return auth.AuthUser(*users[token])
        raise Exception("bad token")
    auth.verifier = verifier
    yield
    auth.verifier = old


def _book(rider_id, user_id, headers=None):
    return client.post("/rides/request", json={
        "rider": {"id": rider_id, "name": rider_id, "gender": "male", "preference": "mix"},
        "request": {"id": "q" + rider_id, "rider_id": rider_id, "flow": "campus_to_destination",
                    "destination": "Mall", "vehicle_type": "cab", "time_window_start": 600, "time_window_end": 660},
        "route": ["Gate", "Mall"], "pickup_lat": 12.97, "pickup_lon": 77.59, "km": 5.0,
        "pickup_name": "Gate", "drop_lat": 12.99, "drop_lon": 77.61, "drop_name": "Mall",
        "user_id": user_id,
    }).json()


def _finished_ride():
    client.post("/drivers", json={"id": "driverD", "name": "Dev", "vehicle_type": "cab",
                                  "latitude": 12.97, "longitude": 77.59})
    room = _book("r1", "userA")["room_id"]
    assert _book("r2", "userB")["room_id"] == room
    client.post("/rides/confirm", json={"room_id": room})
    ride = state.current.rides.ride_for_room(room)
    client.post("/rides/driver/accept", json={"ride_id": ride.ride_id, "driver_id": "driverD"})
    otp = client.post("/rides/confirm", json={"room_id": room}).json()["otp"]
    client.post("/rides/start", json={"ride_id": ride.ride_id, "otp": otp})
    client.post("/rides/complete", json={"ride_id": ride.ride_id})
    return ride.ride_id


def test_ride_status_lists_the_riders_and_the_driver_rating():
    ride_id = _finished_ride()
    data = client.get(f"/rides/{ride_id}").json()
    assert [r["rider_id"] for r in data["riders"]] == ["r1", "r2"]
    assert data["driver_rating"] == {"score": 3.0, "count": 0}


def test_review_driver_and_copassenger_updates_profile_ratings():
    ride_id = _finished_ride()
    r = client.post("/rides/review", json={"ride_id": ride_id, "reviewer_id": "r1", "target_id": "driverD", "stars": 5},
                    headers=RIDER_A)
    assert r.status_code == 200 and r.json()["target_score"] == 3.6
    r = client.post("/rides/review", json={"ride_id": ride_id, "reviewer_id": "r1", "target_id": "r2", "stars": 4},
                    headers=RIDER_A)
    assert r.status_code == 200 and r.json()["role"] == "rider"

    assert client.get("/ratings/me", headers=DRIVER).json() == {"score": 3.6, "count": 1}
    assert client.get("/ratings/me", headers=RIDER_B).json() == {"score": 3.3, "count": 1}
    # a rider nobody reviewed yet
    assert client.get("/ratings/me", headers=RIDER_A).json() == {"score": 3.0, "count": 0}


def test_cannot_review_as_somebody_else():
    ride_id = _finished_ride()
    body = {"ride_id": ride_id, "reviewer_id": "r1", "target_id": "driverD", "stars": 1}
    assert client.post("/rides/review", json=body).status_code == 401          # not signed in
    assert client.post("/rides/review", json=body, headers=RIDER_B).status_code == 403   # r1 belongs to userA


def test_duplicate_review_is_refused():
    ride_id = _finished_ride()
    body = {"ride_id": ride_id, "reviewer_id": "r1", "target_id": "driverD", "stars": 5}
    assert client.post("/rides/review", json=body, headers=RIDER_A).status_code == 200
    assert client.post("/rides/review", json=body, headers=RIDER_A).status_code == 400


def test_ratings_are_rebuilt_from_saved_reviews_after_a_restart():
    ride_id = _finished_ride()
    client.post("/rides/review", json={"ride_id": ride_id, "reviewer_id": "r1", "target_id": "driverD", "stars": 5},
                headers=RIDER_A)
    client.post("/rides/review", json={"ride_id": ride_id, "reviewer_id": "r2", "target_id": "driverD", "stars": 4},
                headers=RIDER_B)
    saved = state.current.repo

    state.reset(repo=saved)              # "the server restarted": new memory, same database
    # 3.0 -> 3.6 -> 0.3*4 + 0.7*3.6 = 3.72
    assert state.current.rides.rating_summary("driverD") == {"score": 3.7, "count": 2}
