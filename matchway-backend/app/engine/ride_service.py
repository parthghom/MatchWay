# RideService is the central orchestrator for the MatchWay system.
# The lifecycle follows this order:
# 1. request: Rider enters system -> placed in VirtualRoom -> matches found.
# 2. room: Compatible riders grouped by destination, vehicle, and time window.
# 3. matches: Potential partners found via Trie and IntervalTree.
# 4. confirm: Room closed -> driver dispatched via DriverDispatcher.
# 5. driver dispatch: Nearest free driver assigned to a spot.
# 6. OTP: Verification code generated for the ride.
# 7. start: Ride begins after OTP verification.
# 8. complete and pay: Ride ends -> driver released -> fares split and paid.
# 9. review: Riders rate each other and the driver using EMA.

from app.engine.hash_map import HashMap
from app.engine.virtual_rooms import RoomManager
from app.engine.matching_engine import MatchingEngine
from app.engine.driver_dispatch import DriverDispatcher
from app.engine.reviews import ReviewService
from app.engine.otp import OTPService
from app.engine.fare import approximate_fare_range, exact_fare, split_payment


class RequestResult:
    def __init__(self, room_id, matches, fare_range):
        self.room_id = room_id
        self.matches = matches
        self.fare_range = fare_range

class Ride:
    def __init__(self, ride_id, room_id, vehicle_type, driver_id, rider_ids, km, exact_share, otp):
        self.ride_id = ride_id
        self.room_id = room_id
        self.vehicle_type = vehicle_type
        self.driver_id = driver_id
        self.rider_ids = rider_ids
        self.km = km
        self.exact_share = exact_share
        self.otp = otp
        self.status = "confirmed"

class RiderRecord:
    def __init__(self, rider, request, pickup_lat, pickup_lon, km):
        self.rider = rider
        self.request = request
        self.pickup_lat = pickup_lat
        self.pickup_lon = pickup_lon
        self.km = km

class RideService:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.room_manager = RoomManager()
        self.engine = MatchingEngine()
        self.reviews = ReviewService()
        self.otp_service = OTPService()

        self.rooms_by_id = HashMap() # room_id -> VirtualRoom
        self.riders = HashMap() # rider_id -> RiderRecord
        self.rides = HashMap() # ride_id -> Ride
        self.ride_of_room = HashMap() # room_id -> ride_id
        self.ride_counter = 0

    def request_ride(self, rider, request, route, pickup_lat, pickup_lon, km):
        if self.engine.entries.contains(rider.id) and self.engine.entries.get(rider.id).active is True:
            raise ValueError("Rider already has an active request")
        # 1. Store rider record
        self.riders.put(rider.id, RiderRecord(rider, request, pickup_lat, pickup_lon, km))

        # 2. Register in MatchingEngine
        self.engine.register(rider, request, route)

        # 3. Assign to room
        room = self.room_manager.assign(rider, request, is_blocked=self.reviews.is_blocked)
        self.rooms_by_id.put(room.room_id, room)

        # 4. Find compatible matches
        all_matches = self.engine.find_matches(rider.id, min_shared_stops=2)
        # Filter matches based on blocking
        filtered_matches = []
        for mid in all_matches:
            if not self.reviews.is_blocked(rider.id, mid):
                filtered_matches.append(mid)

        # 5. Fare range
        fare_range = approximate_fare_range(request.vehicle_type, km, len(room.members))

        return RequestResult(room.room_id, filtered_matches, fare_range)

    def confirm_ride(self, room_id):
        if not self.rooms_by_id.contains(room_id):
            raise KeyError(f"Room {room_id} not found")

        room = self.rooms_by_id.get(room_id)
        if self.ride_of_room.contains(room_id):
            raise ValueError(f"Room {room_id} already has a ride")

        # Ride metrics: largest km, first rider's location
        max_km = 0.0
        first_member = room.members[0]

        # Use riders record for location
        for m_rider, m_req in room.members:
            record = self.riders.get(m_rider.id)
            if record.km > max_km:
                max_km = record.km

        # Correct pickup coords from the first member's record
        first_record = self.riders.get(first_member[0].id)
        lat, lon = first_record.pickup_lat, first_record.pickup_lon
        spot_id = first_member[1].pickup_spot or "campus"

        # Dispatch driver
        driver = self.dispatcher.find_driver(spot_id, lat, lon, room.vehicle_type)

        if driver is None:
            return None

        # Mark room closed
        room.closed = True

        # Create Ride
        self.ride_counter += 1
        ride_id = f"ride_{self.ride_counter}"

        num_riders = len(room.members)
        share = exact_fare(room.vehicle_type, max_km, num_riders)

        # Generate OTP
        otp = self.otp_service.generate(ride_id)

        rider_ids = [m[0].id for m in room.members]
        ride = Ride(ride_id, room_id, room.vehicle_type, driver.id, rider_ids, max_km, share, otp)

        # Save ride
        self.rides.put(ride_id, ride)
        self.ride_of_room.put(room_id, ride_id)

        return ride

    def start_ride(self, ride_id, otp):
        if not self.rides.contains(ride_id):
            raise KeyError(f"Ride {ride_id} unknown")

        ride = self.rides.get(ride_id)
        if ride.status != "confirmed":
            raise ValueError(f"Ride {ride_id} status is {ride.status}, expected confirmed")

        if not self.otp_service.verify(ride_id, otp):
            return False

        ride.status = "in_progress"
        return True

    def complete_ride(self, ride_id):
        if not self.rides.contains(ride_id):
            raise KeyError(f"Ride {ride_id} unknown")

        ride = self.rides.get(ride_id)
        if ride.status != "in_progress":
            raise ValueError(f"Ride {ride_id} status is {ride.status}, expected in_progress")

        ride.status = "completed"

        # Release driver
        self.dispatcher.release_driver(ride.driver_id)

        # Unregister riders
        for rider_id in ride.rider_ids:
            self.engine.unregister(rider_id)
            # Remove rider request from room manager
            # We need to find the request for this rider in the Riders map
            record = self.riders.get(rider_id)
            if record:
                self.room_manager.remove(rider_id, record.request)

        return split_payment(ride.vehicle_type, ride.km, ride.rider_ids)

    def submit_review(self, ride_id, reviewer_id, target_id, stars):
        if not self.rides.contains(ride_id):
            raise KeyError(f"Ride {ride_id} unknown")

        ride = self.rides.get(ride_id)
        if ride.status != "completed":
            raise ValueError(f"Ride {ride_id} is not completed")

        if reviewer_id not in ride.rider_ids:
            raise ValueError(f"Reviewer {reviewer_id} was not on ride {ride_id}")

        is_other_rider = target_id in ride.rider_ids and target_id != reviewer_id
        is_driver = target_id == ride.driver_id
        if not (is_other_rider or is_driver):
            raise ValueError(f"Target {target_id} was not on ride {ride_id}")

        # Track reviews to prevent duplicates: ride_id | reviewer_id | target_id
        review_key = f"{ride_id}|{reviewer_id}|{target_id}"
        if not hasattr(self, 'review_tracker'):
            self.review_tracker = HashMap()

        if self.review_tracker.contains(review_key):
            raise ValueError(f"Reviewer {reviewer_id} already reviewed target {target_id} for ride {ride_id}")

        self.reviews.submit_review(reviewer_id, target_id, stars)
        self.review_tracker.put(review_key, True)

        if is_other_rider:
            record = self.riders.get(target_id)
            if record:
                # Update compatibility_score on the Rider object
                record.rider.compatibility_score = self.reviews.get_score(target_id)
