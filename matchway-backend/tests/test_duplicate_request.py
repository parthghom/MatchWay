from fastapi.testclient import TestClient
from app.main import app
from app.state import current, reset
from app.models.rider import Rider
from app.models.ride_request import RideRequest
from app.models.driver import Driver
from app.engine.driver_dispatch import DriverDispatcher
from app.engine.ride_service import RideService

def test_duplicate_request_raises_value_error():
    reset()
    dispatcher = DriverDispatcher()
    ride_service = RideService(dispatcher)

    rider = Rider(id="r1", name="Rider 1", gender="male", preference="mix")
    request = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route = ["Campus", "Mall"]

    # First request
    ride_service.request_ride(rider, request, route, 12.9, 77.5, 10.0)

    # Second request with same rider id should raise ValueError
    try:
        ride_service.request_ride(rider, request, route, 12.9, 77.5, 10.0)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Rider already has an active request"

def test_rider_can_request_again_after_completion():
    reset()
    dispatcher = DriverDispatcher()
    # Setup driver
    driver = Driver(id="d1", name="Driver 1", vehicle_type="cab", latitude=12.9, longitude=77.5)
    dispatcher.update_driver(driver)

    ride_service = RideService(dispatcher)

    rider = Rider(id="r1", name="Rider 1", gender="male", preference="mix")
    request = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route = ["Campus", "Mall"]

    # 1. Request ride
    res = ride_service.request_ride(rider, request, route, 12.9, 77.5, 10.0)

    # 2. Confirm ride (assign driver)
    ride = ride_service.confirm_ride(res.room_id)
    assert ride is not None

    # 3. Start ride (OTP)
    otp = ride.otp
    success = ride_service.start_ride(ride.ride_id, otp)
    assert success is True

    # 4. Complete ride
    ride_service.complete_ride(ride.ride_id)

    # 5. Request again - should now work
    try:
        ride_service.request_ride(rider, request, route, 12.9, 77.5, 10.0)
    except ValueError:
        assert False, "Rider should be able to request again after completion"

def test_api_duplicate_request_returns_400():
    reset()
    client = TestClient(app)

    payload = {
        "rider": {
            "id": "r1",
            "name": "Rider 1",
            "gender": "male",
            "preference": "mix"
        },
        "request": {
            "id": "req1",
            "rider_id": "r1",
            "flow": "campus_to_destination",
            "destination": "Mall",
            "vehicle_type": "cab",
            "time_window_start": 100,
            "time_window_end": 200
        },
        "route": ["Campus", "Mall"],
        "pickup_lat": 12.9,
        "pickup_lon": 77.5,
        "km": 10.0
    }

    # First request
    resp1 = client.post("/rides/request", json=payload)
    assert resp1.status_code == 200

    # Second request with same rider_id
    resp2 = client.post("/rides/request", json=payload)
    assert resp2.status_code == 400
