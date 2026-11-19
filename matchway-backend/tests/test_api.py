import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import state
from app.engine.fare import vehicle_fare

client = TestClient(app)

def confirm_and_accept(client, room_id):
    """A driver is offered the ride and accepts it; returns the confirm data the riders see."""
    from app import state
    first = client.post("/rides/confirm", json={"room_id": room_id}).json()
    assert first["confirmed"] is False and first.get("offered") is True      # waiting for the driver
    ride = state.current.rides.ride_for_room(room_id)
    assert client.post("/rides/driver/accept", json={"ride_id": ride.ride_id, "driver_id": ride.driver_id}).status_code == 200
    return client.post("/rides/confirm", json={"room_id": room_id}).json()


@pytest.fixture(autouse=True)

def setup_state():
    state.reset()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_spots_nearest():
    # POST a driver and a spot
    client.post("/drivers", json={
        "id": "d1", "name": "Driver 1", "vehicle_type": "cab",
        "latitude": 12.9716, "longitude": 77.5946
    })
    client.post("/spots", json={
        "spot_id": "S1", "name": "Spot 1", "latitude": 12.9716, "longitude": 77.5946
    })

    # GET /spots/nearest
    response = client.get("/spots/nearest?lat=12.9717&lon=77.5947")
    assert response.status_code == 200
    data = response.json()
    assert data["spot_id"] == "S1"
    assert data["walk_to_save"] is False

def test_spots_nearest_empty():
    response = client.get("/spots/nearest?lat=12.9716&lon=77.5946")
    assert response.status_code == 400

def test_duplicate_spot():
    client.post("/spots", json={
        "spot_id": "S1", "name": "Spot 1", "latitude": 12.9716, "longitude": 77.5946
    })
    response = client.post("/spots", json={
        "spot_id": "S1", "name": "Spot 2", "latitude": 12.9720, "longitude": 77.5950
    })
    assert response.status_code == 400

def test_full_ride_flow():
    # 1. Post driver d1
    client.post("/drivers", json={
        "id": "d1", "name": "Driver 1", "vehicle_type": "cab",
        "latitude": 12.9716, "longitude": 77.5946
    })

    # 2. Request rides for r1 and r2
    r1_data = {
        "rider": {"id": "r1", "name": "Rider 1", "gender": "female", "preference": "mix", "compatibility_score": 3.0},
        "request": {
            "id": "req1", "rider_id": "r1", "flow": "campus_to_destination",
            "destination": "Mall", "vehicle_type": "cab",
            "time_window_start": 600, "time_window_end": 660
        },
        "route": ["Gate", "Road", "Mall"],
        "pickup_lat": 12.9716, "pickup_lon": 77.5946, "km": 5.0
    }
    r2_data = {
        "rider": {"id": "r2", "name": "Rider 2", "gender": "female", "preference": "mix", "compatibility_score": 3.0},
        "request": {
            "id": "req2", "rider_id": "r2", "flow": "campus_to_destination",
            "destination": "Mall", "vehicle_type": "cab",
            "time_window_start": 600, "time_window_end": 660
        },
        "route": ["Gate", "Road", "Mall"],
        "pickup_lat": 12.9716, "pickup_lon": 77.5946, "km": 5.0
    }

    resp1 = client.post("/rides/request", json=r1_data)
    resp2 = client.post("/rides/request", json=r2_data)

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    data1 = resp1.json()
    data2 = resp2.json()

    assert data1["room_id"] == data2["room_id"]
    assert data1["fare_low"] <= data1["fare_high"]

    # 3. Confirm the room
    confirm_data = confirm_and_accept(client, data1["room_id"])
    assert confirm_data["confirmed"] is True
    assert len(confirm_data["otp"]) == 4
    assert confirm_data["status"] == "confirmed"

    ride_id = confirm_data["ride_id"]
    otp = confirm_data["otp"]

    # 4. Start with OTP
    start_resp = client.post("/rides/start", json={"ride_id": ride_id, "otp": otp})
    assert start_resp.status_code == 200

    # 5. Complete
    complete_resp = client.post("/rides/complete", json={"ride_id": ride_id})
    assert complete_resp.status_code == 200
    complete_data = complete_resp.json()

    # Check payments
    total_paid = sum(p["amount"] for p in complete_data["payments"])
    assert round(total_paid, 2) == round(vehicle_fare("cab", 5.0), 2)

    # 6. Review
    review_resp = client.post("/rides/review", json={
        "ride_id": ride_id, "reviewer_id": "r1", "target_id": "r2", "stars": 5
    })
    assert review_resp.status_code == 200
    assert review_resp.json()["target_score"] == 3.6 # 3.0 + (5-3)/2 = 4.0? Wait, formula is usually current + (new-current)/N.
    # If target score was 3.0, one 5-star review: (3*0 + 5)/1 = 5?
    # No, target_score is derived from the ride_service.reviews.get_score(target_id).
    # I'll check the exact expected value in the prompt (3.6).
    # If the system has a baseline, it might be 3.6.

def test_wrong_otp():
    # Set up a ride
    client.post("/drivers", json={
        "id": "d1", "name": "Driver 1", "vehicle_type": "cab",
        "latitude": 12.9716, "longitude": 77.5946
    })
    r_data = {
        "rider": {"id": "r1", "name": "Rider 1", "gender": "female", "preference": "mix", "compatibility_score": 3.0},
        "request": {
            "id": "req1", "rider_id": "r1", "flow": "campus_to_destination",
            "destination": "Mall", "vehicle_type": "cab",
            "time_window_start": 600, "time_window_end": 660
        },
        "route": ["Gate", "Road", "Mall"],
        "pickup_lat": 12.9716, "pickup_lon": 77.5946, "km": 5.0
    }
    resp = client.post("/rides/request", json=r_data)
    room_id = resp.json()["room_id"]
    confirm_data = confirm_and_accept(client, room_id)
    ride_id = confirm_data["ride_id"]

    response = client.post("/rides/start", json={"ride_id": ride_id, "otp": "0000"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Wrong OTP"

def test_unknown_room():
    response = client.post("/rides/confirm", json={"room_id": "unknown"})
    assert response.status_code == 404

def test_no_drivers():
    # No drivers added
    response = client.post("/rides/confirm", json={"room_id": "room1"})
    # Since confirm_ride raises KeyError if room doesn't exist, we need a room.
    # Let's request a ride first.
    r_data = {
        "rider": {"id": "r1", "name": "Rider 1", "gender": "female", "preference": "mix", "compatibility_score": 3.0},
        "request": {
            "id": "req1", "rider_id": "r1", "flow": "campus_to_destination",
            "destination": "Mall", "vehicle_type": "cab",
            "time_window_start": 600, "time_window_end": 660
        },
        "route": ["Gate", "Road", "Mall"],
        "pickup_lat": 12.9716, "pickup_lon": "77.5946", "km": 5.0
    }
    # Mock the room creation
    resp = client.post("/rides/request", json=r_data)
    room_id = resp.json()["room_id"]

    # Confirm with no drivers
    response = client.post("/rides/confirm", json={"room_id": room_id})
    assert response.status_code == 200
    assert response.json()["confirmed"] is False

def test_invalid_preference():
    # Male rider with preference "female_only"
    response = client.post("/rides/request", json={
        "rider": {
            "id": "r1", "name": "Rider 1", "gender": "male", "preference": "female_only"
        },
        "request": {
            "id": "req1", "rider_id": "r1", "flow": "campus_to_destination",
            "destination": "Mall", "vehicle_type": "cab",
            "time_window_start": 600, "time_window_end": 660
        },
        "route": ["Gate", "Road", "Mall"],
        "pickup_lat": 12.9716, "pickup_lon": 77.5946, "km": 5.0
    })
    assert response.status_code == 422

def test_unknown_ride_review():
    response = client.post("/rides/review", json={
        "ride_id": "unknown", "reviewer_id": "r1", "target_id": "r2", "stars": 5
    })
    assert response.status_code == 404


def test_drivers_nearby_spots_and_cancel_api():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    client.post("/drivers", json={"id": "dn1", "name": "N", "vehicle_type": "auto", "latitude": 18.5204, "longitude": 73.8567})
    res = client.get("/drivers/nearby", params={"lat": 18.5204, "lon": 73.8567, "vehicle_type": "auto"})
    assert res.status_code == 200 and res.json() == {"count": 1, "radius_km": 2}
    assert client.get("/drivers/nearby", params={"lat": 1, "lon": 1, "vehicle_type": "plane"}).status_code == 400

    client.post("/spots", json={"spot_id": "sx", "name": "Some College", "latitude": 18.5, "longitude": 73.8})
    assert any(s["spot_id"] == "sx" for s in client.get("/spots").json())

    assert client.post("/rides/cancel", json={"rider_id": "nobody"}).status_code == 404


def test_room_continue_and_confirm_twice_api():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    client.post("/drivers", json={"id": "dg1", "name": "G", "vehicle_type": "auto", "latitude": 18.5, "longitude": 73.8})

    def book(i):
        return client.post("/rides/request", json={
            "rider": {"id": f"gr{i}", "name": f"G{i}", "gender": "male", "preference": "mix"},
            "request": {"id": f"gq{i}", "rider_id": f"gr{i}", "flow": "campus_to_destination", "destination": "GroupMall",
                        "vehicle_type": "auto", "time_window_start": 600, "time_window_end": 660},
            "route": ["A", "GroupMall"], "pickup_lat": 18.5, "pickup_lon": 73.8, "km": 5, "user_id": f"u{i}"})

    room = book(1).json()["room_id"]
    assert book(2).json()["room_id"] == room
    st = client.get(f"/rooms/{room}").json()
    assert [m["user_id"] for m in st["members"]] == ["u1", "u2"]
    assert client.post("/rooms/continue", json={"rider_id": "gr1"}).json()["ready"] is False
    assert client.post("/rooms/continue", json={"rider_id": "gr2"}).json()["ready"] is True

    first = confirm_and_accept(client, room)
    second = client.post("/rides/confirm", json={"room_id": room}).json()   # the other rider asks too
    assert first["confirmed"] and second["ride_id"] == first["ride_id"]
    assert client.get("/rooms/nope").status_code == 404
