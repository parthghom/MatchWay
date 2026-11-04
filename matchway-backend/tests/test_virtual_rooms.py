from app.engine.virtual_rooms import VirtualRoom, RoomManager
from app.models.rider import Rider
from app.models.ride_request import RideRequest

def test_virtual_rooms_time_overlap():
    rm = RoomManager()
    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)

    r2 = Rider(id="r2", name="B", gender="male", preference="mix")
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=150, time_window_end=250)

    room1 = rm.assign(r1, req1)
    room2 = rm.assign(r2, req2)
    assert room1 == room2
    assert len(room1.rider_ids()) == 2

    # Non-overlapping time
    r3 = Rider(id="r3", name="C", gender="male", preference="mix")
    req3 = RideRequest(id="req3", rider_id="r3", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=300, time_window_end=400)
    room3 = rm.assign(r3, req3)
    assert room3 != room1
    assert rm.room_count() == 2

def test_virtual_rooms_capacity():
    rm = RoomManager()
    # Cab capacity 4
    for i in range(5):
        r = Rider(id=f"r{i}", name=f"N{i}", gender="male", preference="mix")
        req = RideRequest(id=f"req{i}", rider_id=f"r{i}", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)
        rm.assign(r, req)

    assert rm.room_count() == 2 # 4 in one, 1 in second

    # Bike capacity 1
    rm_bike = RoomManager()
    r_b1 = Rider(id="b1", name="X", gender="male", preference="mix")
    req_b1 = RideRequest(id="reqb1", rider_id="b1", flow="campus_to_destination", destination="Mall", vehicle_type="bike", time_window_start=100, time_window_end=200)
    r_b2 = Rider(id="b2", name="Y", gender="male", preference="mix")
    req_b2 = RideRequest(id="reqb2", rider_id="b2", flow="campus_to_destination", destination="Mall", vehicle_type="bike", time_window_start=100, time_window_end=200)

    rm_bike.assign(r_b1, req_b1)
    rm_bike.assign(r_b2, req_b2)
    assert rm_bike.room_count() == 2

def test_virtual_rooms_gender():
    rm = RoomManager()

    # Male only rider
    r_male = Rider(id="m1", name="M", gender="male", preference="male_only")
    req_male = RideRequest(id="req_m1", rider_id="m1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)

    # Female rider
    r_female = Rider(id="f1", name="F", gender="female", preference="mix")
    req_female = RideRequest(id="req_f1", rider_id="f1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)

    rm.assign(r_male, req_male)
    rm.assign(r_female, req_female)

    assert rm.room_count() == 2 # Should be in different rooms

    # Mix rider can join mixed
    rm_mix = RoomManager()
    r_mix = Rider(id="mix1", name="Mix", gender="male", preference="mix")
    req_mix = RideRequest(id="req_mix", rider_id="mix1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)

    r_f = Rider(id="f2", name="F2", gender="female", preference="mix")
    req_f = RideRequest(id="req_f2", rider_id="f2", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)

    rm_mix.assign(r_mix, req_mix)
    rm_mix.assign(r_f, req_f)
    assert rm_mix.room_count() == 1

def test_virtual_rooms_destinations():
    rm = RoomManager()
    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)

    r2 = Rider(id="r2", name="B", gender="male", preference="mix")
    req2 = RideRequest(id="req2", rider_id="r2", flow="campus_to_destination", destination="Airport", vehicle_type="cab", time_window_start=100, time_window_end=200)

    rm.assign(r1, req1)
    rm.assign(r2, req2)
    assert rm.room_count() == 2

def test_virtual_rooms_removal():
    rm = RoomManager()
    r1 = Rider(id="r1", name="A", gender="male", preference="mix")
    req1 = RideRequest(id="req1", rider_id="r1", flow="campus_to_destination", destination="Mall", vehicle_type="cab", time_window_start=100, time_window_end=200)

    rm.assign(r1, req1)
    assert rm.room_count() == 1

    rm.remove("r1", req1)
    assert rm.room_count() == 0

if __name__ == "__main__":
    test_virtual_rooms_time_overlap()
    test_virtual_rooms_capacity()
    test_virtual_rooms_gender()
    test_virtual_rooms_destinations()
    test_virtual_rooms_removal()
    print("All tests passed!")
