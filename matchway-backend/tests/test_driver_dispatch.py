from app.engine.driver_dispatch import DriverDispatcher
from app.models.driver import Driver

def test_dispatch_fifo():
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    d2 = Driver(id="d2", name="D2", vehicle_type="cab", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)
    dispatcher.update_driver(d2)

    dispatcher.arrive_at_spot("spotA", "d1")
    dispatcher.arrive_at_spot("spotA", "d2")

    # d1 should be assigned first
    assigned = dispatcher.find_driver("spotA", 12.0, 77.0, "cab")
    assert assigned.id == "d1"

def test_dispatch_skip_busy():
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    d2 = Driver(id="d2", name="D2", vehicle_type="cab", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)
    dispatcher.update_driver(d2)

    d1.is_busy = True
    dispatcher.update_driver(d1)

    dispatcher.arrive_at_spot("spotA", "d1")
    dispatcher.arrive_at_spot("spotA", "d2")

    # d1 is busy, should skip to d2
    assigned = dispatcher.find_driver("spotA", 12.0, 77.0, "cab")
    assert assigned.id == "d2"

def test_dispatch_nearest():
    dispatcher = DriverDispatcher()
    # Ref: 12.9716, 77.5946
    lat, lon = 12.9716, 77.5946

    # Near (approx 100m)
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=lat + 0.0009, longitude=lon)
    # Mid (approx 1km)
    d2 = Driver(id="d2", name="D2", vehicle_type="cab", latitude=lat + 0.009, longitude=lon)
    # Far (approx 10km)
    d3 = Driver(id="d3", name="D3", vehicle_type="cab", latitude=lat + 0.09, longitude=lon)

    dispatcher.update_driver(d1)
    dispatcher.update_driver(d2)
    dispatcher.update_driver(d3)

    # No queue, should find nearest
    assigned = dispatcher.find_driver("spotA", lat, lon, "cab")
    assert assigned.id == "d1"

def test_dispatch_wrong_vehicle():
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="bike", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)

    # Requesting cab, should ignore bike
    assigned = dispatcher.find_driver("spotA", 12.0, 77.0, "cab")
    assert assigned is None

def test_dispatch_out_of_radius():
    dispatcher = DriverDispatcher()
    # Driver is 10km away
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0 + 0.1, longitude=77.0)
    dispatcher.update_driver(d1)

    # Search radius 3km
    assigned = dispatcher.find_driver("spotA", 12.0, 77.0, "cab", search_radius_m=3000)
    assert assigned is None

def test_dispatch_none_available():
    dispatcher = DriverDispatcher()
    # No drivers at all
    assigned = dispatcher.find_driver("spotA", 12.0, 77.0, "cab")
    assert assigned is None

def test_dispatch_release():
    dispatcher = DriverDispatcher()
    d1 = Driver(id="d1", name="D1", vehicle_type="cab", latitude=12.0, longitude=77.0)
    dispatcher.update_driver(d1)

    # Assign d1
    assigned = dispatcher.find_driver("spotA", 12.0, 77.0, "cab")
    assert assigned.id == "d1"
    assert assigned.is_busy is True

    # Try to assign again
    assigned2 = dispatcher.find_driver("spotA", 12.0, 77.0, "cab")
    assert assigned2 is None

    # Release d1
    dispatcher.release_driver("d1")
    assert d1.is_busy is False

    # Assign again
    assigned3 = dispatcher.find_driver("spotA", 12.0, 77.0, "cab")
    assert assigned3.id == "d1"

if __name__ == "__main__":
    test_dispatch_fifo()
    test_dispatch_skip_busy()
    test_dispatch_nearest()
    test_dispatch_wrong_vehicle()
    test_dispatch_out_of_radius()
    test_dispatch_none_available()
    test_dispatch_release()
    print("All tests passed!")
