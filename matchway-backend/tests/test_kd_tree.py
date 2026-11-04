import random
import math
from app.engine.kd_tree import KDTree, haversine_m

def test_kd_tree_radius():
    kt = KDTree()
    # Reference point: 12.9716, 77.5946 (Bangalore)
    ref_lat, ref_lon = 12.9716, 77.5946

    # 1. Point inside 200m (approx 0.001 deg lat is ~111m)
    # Move ~100m North
    kt.insert(ref_lat + 0.0009, ref_lon, "inside")
    # 2. Point 1km away (~0.009 deg lat)
    kt.insert(ref_lat + 0.01, ref_lon, "far")

    results = kt.radius_search(ref_lat, ref_lon, 200)
    # Only "inside" should be here
    assert len(results) == 1
    assert results[0][1] == "inside"

def test_kd_tree_empty():
    kt = KDTree()
    assert kt.radius_search(12.0, 77.0, 1000) == []

def test_kd_tree_nearest():
    kt = KDTree()
    ref_lat, ref_lon = 12.9716, 77.5946

    kt.insert(ref_lat + 0.001, ref_lon, "near")    # ~111m
    kt.insert(ref_lat + 0.01, ref_lon, "mid")     # ~1.1km
    kt.insert(ref_lat + 0.1, ref_lon, "far")      # ~11km

    dist, item = kt.nearest(ref_lat, ref_lon)
    assert item == "near"

def test_kd_tree_random_brute_force():
    kt = KDTree()
    points = []
    # Base location
    base_lat, base_lon = 12.9716, 77.5946

    # Insert 200 random points within a few km
    for i in range(200):
        # random offset roughly +/- 0.02 degrees (~2km)
        lat = base_lat + (random.random() - 0.5) * 0.04
        lon = base_lon + (random.random() - 0.5) * 0.04
        item = f"p{i}"
        kt.insert(lat, lon, item)
        points.append((lat, lon, item))

    radius = 500
    # KDTree search
    kd_results = kt.radius_search(base_lat, base_lon, radius)

    # Brute force search
    brute_results = []
    for lat, lon, item in points:
        d = haversine_m(base_lat, base_lon, lat, lon)
        if d <= radius:
            brute_results.append((d, item))

    # Sort brute force results by distance for comparison
    # Since we can't use sorted(), we'll use a simple sort or just compare sets of items
    brute_items = {item for d, item in brute_results}
    kd_items = {item for d, item in kd_results}

    assert brute_items == kd_items
    assert len(kd_results) == len(brute_results)

if __name__ == "__main__":
    test_kd_tree_radius()
    test_kd_tree_empty()
    test_kd_tree_nearest()
    test_kd_tree_random_brute_force()
    print("All tests passed!")
