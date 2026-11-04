import random
from app.engine.interval_tree import IntervalTree

def test_interval_tree_basic():
    it = IntervalTree()
    # Empty tree search
    assert it.overlap_search(10, 20) == []

    # Overlapping intervals
    it.insert(10, 20, "i1")
    it.insert(15, 25, "i2")
    it.insert(30, 40, "i3")

    # Search [12, 18] -> should find i1 and i2
    res = it.overlap_search(12, 18)
    assert "i1" in res
    assert "i2" in res
    assert "i3" not in res
    assert len(res) == 2

def test_interval_tree_touching():
    it = IntervalTree()
    it.insert(10, 20, "i1")
    # Touching endpoints count as overlap
    assert "i1" in it.overlap_search(20, 30)
    assert "i1" in it.overlap_search(0, 10)

def test_interval_tree_errors():
    it = IntervalTree()
    try:
        it.insert(20, 10, "error")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

def test_interval_tree_random_brute_force():
    it = IntervalTree()
    intervals = []
    for i in range(200):
        s = random.randint(0, 1000)
        e = s + random.randint(0, 100)
        item = f"item{i}"
        it.insert(s, e, item)
        intervals.append((s, e, item))

    # Test a random query interval
    q_start = random.randint(0, 1000)
    q_end = q_start + random.randint(0, 100)

    # Interval Tree search
    it_res = sorted(it.overlap_search(q_start, q_end))

    # Brute force search
    brute_res = []
    for s, e, item in intervals:
        if s <= q_end and q_start <= e:
            brute_res.append(item)
    brute_res = sorted(brute_res)

    assert it_res == brute_res

if __name__ == "__main__":
    test_interval_tree_basic()
    test_interval_tree_touching()
    test_interval_tree_errors()
    test_interval_tree_random_brute_force()
    print("All tests passed!")
