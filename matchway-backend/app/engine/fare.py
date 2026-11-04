# fare.py handles the calculation of ride costs based on vehicle type,
# travel distance, and the number of riders sharing the vehicle.

import math
from app.engine.kd_tree import haversine_m
from app.models.constants import VEHICLE_CAPACITY

# Configuration for fares
BASE_FARE = {"cab": 50.0, "auto": 30.0, "bike": 20.0}
PER_KM = {"cab": 14.0, "auto": 10.0, "bike": 7.0}

def distance_km(lat1, lon1, lat2, lon2):
    """Returns the distance between two points in kilometers."""
    return haversine_m(lat1, lon1, lat2, lon2) / 1000.0

def vehicle_fare(vehicle_type, km):
    """Calculates the total cost for a vehicle over a given distance."""
    if vehicle_type not in BASE_FARE:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")
    if km < 0:
        raise ValueError("Distance cannot be negative")

    total = BASE_FARE[vehicle_type] + (PER_KM[vehicle_type] * km)
    return round(total, 2)

def approximate_fare_range(vehicle_type, km, riders=1):
    """Returns a (low, high) tuple for the estimated share per rider."""
    if vehicle_type not in VEHICLE_CAPACITY:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")
    full_cap = VEHICLE_CAPACITY[vehicle_type]

    # Low: exact share if vehicle is full
    low = exact_fare(vehicle_type, km, full_cap)
    # High: exact share with current number of riders
    high = exact_fare(vehicle_type, km, riders)

    return (low, high)

def exact_fare(vehicle_type, km, riders):
    """Returns the fare share for a single rider."""
    if riders < 1:
        raise ValueError("Riders must be at least 1")
    if vehicle_type not in VEHICLE_CAPACITY or riders > VEHICLE_CAPACITY[vehicle_type]:
        raise ValueError(f"Riders exceed capacity for {vehicle_type}")

    total = vehicle_fare(vehicle_type, km)
    return round(total / riders, 2)

def split_payment(vehicle_type, km, rider_ids):
    """Divides the total fare among riders, handling rounding remainders."""
    num_riders = len(rider_ids)
    total_fare = vehicle_fare(vehicle_type, km)
    share = exact_fare(vehicle_type, km, num_riders)

    # Calculate total allocated so far
    allocated = round(share * num_riders, 2)
    remainder = round(total_fare - allocated, 2)

    results = []
    for i, r_id in enumerate(rider_ids):
        amount = share
        if i == 0:
            amount = round(amount + remainder, 2)
        results.append((r_id, amount))

    return results
