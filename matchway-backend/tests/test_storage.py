from fastapi.testclient import TestClient
from app.main import app
from app import state
from app.state import reset
from app.storage import get_repository, MemoryRepository
from app.models.rider import Rider
from app.models.ride_request import RideRequest
from app.models.driver import Driver

def test_storage_basic_flow():
    reset()
    client = TestClient(app)

    # 1. Driver and Spot
    driver_payload = {"id": "d1", "name": "Driver 1", "vehicle_type": "cab", "latitude": 12.9, "longitude": 77.5}
    client.post("/drivers", json=driver_payload)

    spot_payload = {"spot_id": "s1", "name": "Spot 1", "latitude": 12.9, "longitude": 77.5}
    client.post("/spots", json=spot_payload)

    # Check repo
    assert "d1" in state.current.repo.drivers
    assert "s1" in state.current.repo.spots

    # 2. Full Ride Flow
    rider1_data = {"id": "r1", "name": "Rider 1", "gender": "male", "preference": "mix"}
    rider2_data = {"id": "r2", "name": "Rider 2", "gender": "male", "preference": "mix"}

    req_payload = {
        "rider": rider1_data,
        "request": {"id": "req1", "rider_id": "r1", "flow": "campus_to_destination", "destination": "Mall", "vehicle_type": "cab", "time_window_start": 100, "time_window_end": 200},
        "route": ["Campus", "Mall"],
        "pickup_lat": 12.9,
        "pickup_lon": 77.5,
        "km": 10.0
    }

    res1 = client.post("/rides/request", json=req_payload)
    room_id = res1.json()["room_id"]

    # Rider 2
    req_payload2 = {
        "rider": rider2_data,
        "request": {"id": "req2", "rider_id": "r2", "flow": "campus_to_destination", "destination": "Mall", "vehicle_type": "cab", "time_window_start": 100, "time_window_end": 200},
        "route": ["Campus", "Mall"],
        "pickup_lat": 12.9,
        "pickup_lon": 77.5,
        "km": 10.0
    }
    client.post("/rides/request", json=req_payload2)

    # Confirm
    conf_res = client.post("/rides/confirm", json={"room_id": room_id})
    ride_id = conf_res.json()["ride_id"]
    otp = conf_res.json()["otp"]

    # Start
    client.post("/rides/start", json={"ride_id": ride_id, "otp": otp})

    # Complete
    client.post("/rides/complete", json={"ride_id": ride_id})

    # Review
    client.post("/rides/review", json={"ride_id": ride_id, "reviewer_id": "r1", "target_id": "r2", "stars": 5})

    # Verify Repo
    ride_obj = state.current.repo.rides.get(ride_id)
    assert ride_obj.status == "completed"
    assert len(state.current.repo.reviews) == 1
    assert state.current.repo.riders.get("r2").compatibility_score == 3.6

def test_state_rebuild_from_repo():
    reset()
    client = TestClient(app)

    driver_payload = {"id": "d_persist", "name": "Driver Persist", "vehicle_type": "cab", "latitude": 12.9, "longitude": 77.5}
    client.post("/drivers", json=driver_payload)

    spot_payload = {"spot_id": "s_persist", "name": "Spot Persist", "latitude": 12.9, "longitude": 77.5}
    client.post("/spots", json=spot_payload)

    repo = state.current.repo

    # Rebuild state on SAME repo
    from app.state import reset as state_reset
    state_reset(repo=repo)

    # Check if driver and spot came back
    resp = client.get("/drivers")
    assert resp.status_code == 200
    assert any(d["id"] == "d_persist" for d in resp.json())
    assert state.current.spots.size() > 0

def test_get_repository_memory_default():
    import os
    os.environ["MATCHWAY_STORAGE"] = "memory"
    repo = get_repository()
    assert isinstance(repo, MemoryRepository)
