from app.engine.queue import Queue

def test_queue_basic():
    q = Queue()
    assert q.is_empty() is True
    assert q.size() == 0

    q.enqueue(1)
    assert q.is_empty() is False
    assert q.size() == 1
    assert q.peek() == 1

    q.enqueue(2)
    assert q.size() == 2
    assert q.peek() == 1

    assert q.dequeue() == 1
    assert q.size() == 1
    assert q.peek() == 2

    assert q.dequeue() == 2
    assert q.is_empty() is True
    assert q.size() == 0

def test_queue_empty_errors():
    q = Queue()
    try:
        q.dequeue()
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

    try:
        q.peek()
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

if __name__ == "__main__":
    test_queue_basic()
    test_queue_empty_errors()
    print("All tests passed!")
