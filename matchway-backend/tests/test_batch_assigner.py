from app.engine.batch_assigner import BatchAssigner
from app.engine.driver_dispatch import DriverDispatcher
from app.models.driver import Driver

def test_batch_one_to_one():
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)

    rooms = [("room1", "cab", 12.0, 77.0)]
    assigner = BatchAssigner()
    matches = assigner.assign(dispatcher, rooms)

    assert len(matches) == 1
    assert matches[0] == ("room1", "d1")
    assert d1.is_busy is True

def test_batch_busy_driver():
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    d1.is_busy = True
    dispatcher.update_driver(d1)

    rooms = [("room1", "cab", 12.0, 77.0)]
    assigner = BatchAssigner()
    matches = assigner.assign(dispatcher, rooms)

    assert len(matches) == 0

def test_batch_wrong_vehicle():
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="bike", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)

    rooms = [("room1", "cab", 12.0, 77.0)]
    assigner = BatchAssigner()
    matches = assigner.assign(dispatcher, rooms)

    assert len(matches) == 0

def test_batch_out_of_radius():
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.1, longitude=77.1)
    dispatcher.update_driver(d1)

    rooms = [("room1", "cab", 12.0, 77.0)]
    assigner = BatchAssigner()
    matches = assigner.assign(dispatcher, rooms, radius_m=1000)

    assert len(matches) == 0

def test_batch_two_rooms_one_driver():
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)

    rooms = [("room1", "cab", 12.0, 77.0), ("room2", "cab", 12.0, 77.0)]
    assigner = BatchAssigner()
    matches = assigner.assign(dispatcher, rooms)

    assert len(matches) == 1

def test_batch_optimal_matching():
    # d1 can serve A and B
    # d2 can only serve A
    # Optimal: d2 -> A, d1 -> B (size 2)
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    d2 = Driver(id="d2", name="D2", vehicle_type="cab", latitude=12.001, longitude=77.0)
    dispatcher.update_driver(d1)
    dispatcher.update_driver(d2)

    # Room A is at 12.0, Room B is at 12.001
    rooms = [
        ("roomA", "cab", 12.0, 77.0),
        ("roomB", "cab", 12.001, 77.0)
    ]

    # Set radius small enough that d2 cannot reach room B, but d1 can reach both
    # Distance between 12.0 and 12.001 is ~111m.
    assigner = BatchAssigner()
    matches = assigner.assign(dispatcher, rooms, radius_m=200)

    assert len(matches) == 2
    # Check that d2 is matched to A and d1 is matched to B
    # because if d1 took A, d2 would have nothing.
    match_map = {room: driver for room, driver in matches}
    assert match_map["roomA"] == "d2"
    assert match_map["roomB"] == "d1"
    assert d1.is_busy is True
    assert d2.is_busy is True

if __name__ == "__main__":
    test_batch_one_to_one()
    test_batch_busy_driver()
    test_batch_wrong_vehicle()
    test_batch_out_of_radius()
    test_batch_two_rooms_one_driver()
    test_batch_optimal_matching()
    print("All tests passed!")
