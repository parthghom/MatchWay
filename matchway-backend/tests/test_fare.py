from app.engine.fare import vehicle_fare, exact_fare, approximate_fare_range, split_payment
import pytest

def test_fare_calculation():
    # Cab: 40 + 20 * 10 = 240.0
    assert vehicle_fare("cab", 10) == 240.0
    # Auto: 25 + 15 * 5 = 100.0
    assert vehicle_fare("auto", 5) == 100.0
    # Bike: 15 + 10 * 5 = 65.0
    assert vehicle_fare("bike", 5) == 65.0

    with pytest.raises(ValueError):
        vehicle_fare("truck", 10)
    with pytest.raises(ValueError):
        vehicle_fare("cab", -1)

def test_fare_sharing():
    # Cab 10km = 240.0
    # 1 rider: 240.0
    # 4 riders: 240 / 4 = 60.0
    assert exact_fare("cab", 10, 1) == 240.0
    assert exact_fare("cab", 10, 4) == 60.0

    with pytest.raises(ValueError):
        exact_fare("cab", 10, 5) # Over capacity
    with pytest.raises(ValueError):
        exact_fare("cab", 10, 0) # Under 1

def test_fare_approx_range():
    # Cab 10km = 240.0
    # Low (4 riders): 60.0
    # High (2 riders): 240 / 2 = 120.0
    low, high = approximate_fare_range("cab", 10, 2)
    assert low == 60.0
    assert high == 120.0
    assert low <= high

def test_fare_split_payment():
    # Total = 240.0, Riders = 3. Share = 240/3 = 80.0 (no remainder)
    rider_ids = ["r1", "r2", "r3"]
    splits = split_payment("cab", 10, rider_ids)

    assert splits == [("r1", 80.0), ("r2", 80.0), ("r3", 80.0)]

    # 8km auto = 25 + 15*8 = 145. 145/3 = 48.33 -> 48.33*3 = 144.99, first rider absorbs 0.01
    uneven = split_payment("auto", 8, ["a", "b", "c"])
    assert uneven == [("a", 48.34), ("b", 48.33), ("c", 48.33)]
    assert round(sum(x for _, x in uneven), 2) == 145.0

    total = sum(amount for _, amount in splits)
    assert total == 240.0


def test_fare_options_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app
    res = TestClient(app).get("/fare/options", params={"km": 10})
    assert res.status_code == 200
    by = {o["vehicle_type"]: o for o in res.json()}
    assert set(by) == {"bike", "auto", "cab"}
    assert by["bike"]["full_fare"] == 115.0 and by["bike"]["capacity"] == 1
    assert by["cab"]["fare_low"] < by["cab"]["fare_high"] == by["cab"]["full_fare"]
    assert TestClient(app).get("/fare/options", params={"km": -1}).status_code == 400
