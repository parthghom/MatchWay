from app.engine.hash_map import HashMap

def test_hash_map_basic():
    hm = HashMap()
    assert hm.size() == 0

    hm.put("name", "Claude")
    hm.put("city", "New York")
    assert hm.size() == 2
    assert hm.get("name") == "Claude"
    assert hm.get("city") == "New York"

def test_hash_map_overwrite():
    hm = HashMap()
    hm.put("key", "value1")
    hm.put("key", "value2")
    assert hm.size() == 1
    assert hm.get("key") == "value2"

def test_hash_map_remove():
    hm = HashMap()
    hm.put("a", 1)
    hm.put("b", 2)
    assert hm.contains("a") is True
    hm.remove("a")
    assert hm.contains("a") is False
    assert hm.size() == 1

    try:
        hm.remove("a")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass

def test_hash_map_collisions():
    # We know our hash is val % capacity.
    # With capacity 8, 0 and 8 will collide.
    hm = HashMap()
    hm.put(0, "zero")
    hm.put(8, "eight")
    assert hm.size() == 2
    assert hm.get(0) == "zero"
    assert hm.get(8) == "eight"

def test_hash_map_resize():
    hm = HashMap()
    # Initial capacity 8, threshold 8 * 0.75 = 6
    for i in range(100):
        hm.put(i, f"val{i}")

    assert hm.size() == 100
    # Verify all values are still there
    for i in range(100):
        assert hm.get(i) == f"val{i}"

    # Verify capacity increased
    assert hm.capacity > 8

def test_hash_map_keys():
    hm = HashMap()
    keys = ["k1", "k2", "k3"]
    for k in keys:
        hm.put(k, True)

    result_keys = hm.keys()
    assert len(result_keys) == 3
    for k in keys:
        assert k in result_keys

if __name__ == "__main__":
    test_hash_map_basic()
    test_hash_map_overwrite()
    test_hash_map_remove()
    test_hash_map_collisions()
    test_hash_map_resize()
    test_hash_map_keys()
    print("All tests passed!")
