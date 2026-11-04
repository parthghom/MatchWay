import random
from app.engine.min_heap import MinHeap

def test_min_heap_basic():
    mh = MinHeap()
    assert mh.is_empty() is True
    assert mh.size() == 0

    mh.push(10, "ten")
    assert mh.size() == 1
    assert mh.peek() == (10, "ten")

    mh.push(5, "five")
    assert mh.size() == 2
    assert mh.peek() == (5, "five")

    mh.push(15, "fifteen")
    assert mh.size() == 3
    assert mh.peek() == (5, "five")

    assert mh.pop() == (5, "five")
    assert mh.peek() == (10, "ten")
    assert mh.pop() == (10, "ten")
    assert mh.pop() == (15, "fifteen")
    assert mh.is_empty() is True

def test_min_heap_empty_errors():
    mh = MinHeap()
    try:
        mh.pop()
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

    try:
        mh.peek()
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

def test_min_heap_random_sorted():
    mh = MinHeap()
    nums = [random.randint(0, 1000) for _ in range(20)]
    for n in nums:
        mh.push(n, str(n))

    sorted_nums = sorted(nums)
    for expected in sorted_nums:
        priority, _ = mh.pop()
        assert priority == expected

if __name__ == "__main__":
    test_min_heap_basic()
    test_min_heap_empty_errors()
    test_min_heap_random_sorted()
    print("All tests passed!")
