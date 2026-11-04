from app.engine.matching_engine import MatchingEngine
from app.models.rider import Rider
from app.models.ride_request import RideRequest

def test_matching_engine_basic():
    me = MatchingEngine()

    # Rider 1 (Reference)
    r1 = Rider(id="r1", name="A", gender="male", preference="mix", compatibility_score=3.0)
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]
    me.register(r1, req1, route1)

    # Rider 2: Perfect match
    r2 = Rider(id="r2", name="B", gender="male", preference="mix", compatibility_score=4.0)
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=150, time_window_end=250)
    route2 = ["Stop1", "Stop2", "Stop4"]
    me.register(r2, req2, route2)

    # Rider 3: Different route (only 1 stop shared)
    r3 = Rider(id="r3", name="C", gender="male", preference="mix", compatibility_score=5.0)
    req3 = RideRequest(id="req3", rider_id="r3", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route3 = ["Stop1", "StopX", "StopY"]
    me.register(r3, req3, route3)

    # Rider 4: Non-overlapping time
    r4 = Rider(id="r4", name="D", gender="male", preference="mix", compatibility_score=5.0)
    req4 = RideRequest(id="req4", rider_id="r4", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=300, time_window_end=400)
    route4 = ["Stop1", "Stop2", "StopZ"]
    me.register(r4, req4, route4)

    matches = me.find_matches("r1")
    assert "r2" in matches
    assert "r3" not in matches
    assert "r4" not in matches
    assert len(matches) == 1

def test_matching_engine_gender():
    me = MatchingEngine()
    r1 = Rider(id="r1", name="A", gender="male", preference="male_only", compatibility_score=3.0)
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]
    me.register(r1, req1, route1)

    # Rider 2: Female, mix preference (rejected by r1)
    r2 = Rider(id="r2", name="B", gender="female", preference="mix", compatibility_score=4.0)
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route2 = ["Stop1", "Stop2", "Stop4"]
    me.register(r2, req2, route2)

    matches = me.find_matches("r1")
    assert "r2" not in matches

def test_matching_engine_filters():
    me = MatchingEngine()
    r1 = Rider(id="r1", name="A", gender="male", preference="mix", compatibility_score=3.0)
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]
    me.register(r1, req1, route1)

    # Different vehicle
    r2 = Rider(id="r2", name="B", gender="male", preference="mix", compatibility_score=4.0)
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="bike", time_window_start=100, time_window_end=200)
    route2 = ["Stop1", "Stop2", "Stop4"]
    me.register(r2, req2, route2)

    # Different flow
    r3 = Rider(id="r3", name="C", gender="male", preference="mix", compatibility_score=4.0)
    req3 = RideRequest(id="req3", rider_id="r3", flow="pickup_to_campus", destination="Mall", pickup_spot="Gate1", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route3 = ["Stop1", "Stop2", "Stop4"]
    me.register(r3, req3, route3)

    matches = me.find_matches("r1")
    assert "r2" not in matches
    assert "r3" not in matches

def test_matching_engine_inactive():
    me = MatchingEngine()
    r1 = Rider(id="r1", name="A", gender="male", preference="mix", compatibility_score=3.0)
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]
    me.register(r1, req1, route1)

    r2 = Rider(id="r2", name="B", gender="male", preference="mix", compatibility_score=4.0)
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route2 = ["Stop1", "Stop2", "Stop4"]
    me.register(r2, req2, route2)

    me.unregister("r2")
    matches = me.find_matches("r1")
    assert "r2" not in matches

def test_matching_engine_sorting():
    me = MatchingEngine()
    r1 = Rider(id="r1", name="A", gender="male", preference="mix", compatibility_score=3.0)
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]
    me.register(r1, req1, route1)

    # High score
    r2 = Rider(id="r2", name="B", gender="male", preference="mix", compatibility_score=5.0)
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route2 = ["Stop1", "Stop2", "Stop4"]
    me.register(r2, req2, route2)

    # Low score
    r3 = Rider(id="r3", name="C", gender="male", preference="mix", compatibility_score=2.0)
    req3 = RideRequest(id="req3", rider_id="r3", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route3 = ["Stop1", "Stop2", "Stop5"]
    me.register(r3, req3, route3)

def test_matching_engine_sorting_fixed():
    me = MatchingEngine()
    r1 = Rider(id="r1", name="A", gender="male", preference="mix", compatibility_score=3.0)
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route1 = ["Stop1", "Stop2", "Stop3"]
    me.register(r1, req1, route1)

    r2 = Rider(id="r2", name="B", gender="male", preference="mix", compatibility_score=5.0)
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route2 = ["Stop1", "Stop2", "Stop4"]
    me.register(r2, req2, route2)

    r3 = Rider(id="r3", name="C", gender="male", preference="mix", compatibility_score=2.0)
    req3 = RideRequest(id="req3", rider_id="r3", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
    route3 = ["Stop1", "Stop2", "Stop5"]
    me.register(r3, req3, route3)

    matches = me.find_matches("r1")
    assert matches == ["r2", "r3"]

def test_matching_engine_unknown_rider():
    me = MatchingEngine()
    try:
        me.find_matches("unknown")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass

if __name__ == "__main__":
    test_matching_engine_basic()
    test_matching_engine_gender()
    test_matching_engine_filters()
    test_matching_engine_inactive()
    test_matching_engine_sorting_fixed()
    test_matching_engine_unknown_rider()
    print("All tests passed!")
