from app.engine.fare import vehicle_fare, exact_fare, approximate_fare_range, split_payment
import pytest

def test_fare_calculation():
    # Cab: 50 + 14 * 10 = 190.0
    assert vehicle_fare("cab", 10) == 190.0
    # Auto: 30 + 10 * 5 = 80.0
    assert vehicle_fare("auto", 5) == 80.0

    with pytest.raises(ValueError):
        vehicle_fare("truck", 10)
    with pytest.raises(ValueError):
        vehicle_fare("cab", -1)

def test_fare_sharing():
    # Cab 10km = 190.0
    # 1 rider: 190.0
    # 4 riders: 190 / 4 = 47.5
    assert exact_fare("cab", 10, 1) == 190.0
    assert exact_fare("cab", 10, 4) == 47.5

    with pytest.raises(ValueError):
        exact_fare("cab", 10, 5) # Over capacity
    with pytest.raises(ValueError):
        exact_fare("cab", 10, 0) # Under 1

def test_fare_approx_range():
    # Cab 10km = 190.0
    # Low (4 riders): 47.5
    # High (2 riders): 190 / 2 = 95.0
    low, high = approximate_fare_range("cab", 10, 2)
    assert low == 47.5
    assert high == 95.0
    assert low <= high

def test_fare_split_payment():
    # Total = 190.0, Riders = 3. Share = 190/3 = 63.33
    # 63.33 * 3 = 189.99. Remainder = 0.01.
    # First rider: 63.33 + 0.01 = 63.34
    # Others: 63.33
    rider_ids = ["r1", "r2", "r3"]
    splits = split_payment("cab", 10, rider_ids)

    assert splits[0] == ("r1", 63.34)
    assert splits[1] == ("r2", 63.33)
    assert splits[2] == ("r3", 63.33)

    total = sum(amount for _, amount in splits)
    assert total == 190.0
