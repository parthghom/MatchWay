# RideService is the central orchestrator for the MatchWay system.
# The lifecycle follows this order:
# 1. request: Rider enters system -> placed in VirtualRoom -> matches found.
# 2. room: Compatible riders grouped by destination, vehicle, and time window.
# 3. matches: Potential partners found via Trie and IntervalTree.
# 4. confirm: Room closed -> driver dispatched via DriverDispatcher.
# 5. driver dispatch: Nearest free driver is OFFERED the ride (30 s to accept).
#    Reject or no answer -> the next nearest driver gets it.
# 6. OTP: When the driver accepts, a 4-digit code is made and shown to the riders.
# 7. start: The driver types the OTP at the pickup, then the ride begins.
# 8. complete and pay: Ride ends -> driver released -> fares split and paid.
# 9. review: Riders rate the driver and every co-passenger (1-5 stars). Each review updates the
#    target's EMA rating. Ratings belong to the PERSON (user id), so they live on across rides, show
#    on the profile, and steer matching: riders are grouped with similarly well-rated riders, and
#    well-rated drivers are preferred when a driver is chosen.

import math
import time

from app.engine.hash_map import HashMap
from app.engine.virtual_rooms import RoomManager
from app.engine.matching_engine import MatchingEngine
from app.engine.driver_dispatch import DriverDispatcher
from app.engine.reviews import ReviewService
from app.engine.otp import OTPService
from app.engine.fare import approximate_fare_range, exact_fare, split_payment


GROUP_ACCEPT_SECONDS = 15   # everybody in a full group must accept within this time
OFFER_SECONDS = 30          # a driver has this long to accept an offered ride
DECLINE_COOLDOWN = 60       # a driver who declined is not offered the same ride again for this long
MAX_RATING_GAP = 1.5        # riders whose ratings are further apart than this are not put in one room


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
        self.status = "confirmed"      # offered -> confirmed (driver accepted) -> in_progress -> completed
        self.driver_name = ""
        self.pickup = None             # {"name", "lat", "lon"}
        self.drop = None
        self.offered_at = None
        self.payments = None           # filled when the ride completes
        self.riders = []               # [{"rider_id", "name"}]: who was on board (kept after the room is gone)

class RiderRecord:
    def __init__(self, rider, request, pickup_lat, pickup_lon, km,
                 pickup_name=None, drop_lat=None, drop_lon=None, drop_name=None):
        self.pickup_name = pickup_name
        self.drop_lat = drop_lat
        self.drop_lon = drop_lon
        self.drop_name = drop_name
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
        # the dispatcher asks us for a driver's rating, so well-rated drivers are preferred
        self.dispatcher.rating_of = self.reviews.get_score

        self.rooms_by_id = HashMap() # room_id -> VirtualRoom
        self.riders = HashMap() # rider_id -> RiderRecord
        self.rides = HashMap() # ride_id -> Ride
        self.ride_of_room = HashMap() # room_id -> ride_id
        self.ride_counter = 0

        # group agreement ("continue with N")
        self.user_of_rider = HashMap()   # rider_id -> user_id (for profile pictures)
        self.votes = HashMap()           # rider_id -> the group ("r1,r2") they said continue to
        self.full_since = HashMap()      # room_id -> time the room became full
        self.declined = HashMap()        # "room_id|driver_id" -> time the driver declined
        self.review_tracker = HashMap()  # "ride|reviewer|target" -> True (one review per pair per ride)

    # ---- identity and ratings ----------------------------------------------
    def identity(self, rider_id):
        """Ratings belong to the person, not to one request. A rider id like "r1731..." is new for
        every booking, so we use the user id behind it (a driver id already is a user id)."""
        if self.user_of_rider.contains(rider_id):
            return self.user_of_rider.get(rider_id)
        return rider_id

    def rating_of(self, rider_id):
        return self.reviews.get_score(self.identity(rider_id))

    def _blocked(self, a, b):
        return self.reviews.is_blocked(self.identity(a), self.identity(b))

    def rating_summary(self, identity):
        return self.reviews.summary(identity)

    def request_ride(self, rider, request, route, pickup_lat, pickup_lon, km,
                     pickup_name=None, drop_lat=None, drop_lon=None, drop_name=None, user_id=None):
        if self.engine.entries.contains(rider.id) and self.engine.entries.get(rider.id).active is True:
            raise ValueError("Rider already has an active request")
        if user_id:
            self.user_of_rider.put(rider.id, user_id)
        # the rating comes from the server's record, never from what the phone says
        rider.compatibility_score = self.rating_of(rider.id)
        # 1. Store rider record
        self.riders.put(rider.id, RiderRecord(
            rider, request, pickup_lat, pickup_lon, km, pickup_name, drop_lat, drop_lon, drop_name))

        # 2. Register in MatchingEngine
        self.engine.register(rider, request, route)

        # 3. Assign to room
        room = self.room_manager.assign(
            rider, request, is_blocked=self._blocked, score_of=self.rating_of, max_gap=MAX_RATING_GAP)
        self.rooms_by_id.put(room.room_id, room)

        # 4. Find compatible matches
        all_matches = self.engine.find_matches(rider.id, min_shared_stops=2)
        # Filter matches based on blocking
        filtered_matches = []
        for mid in all_matches:
            if not self._blocked(rider.id, mid):
                filtered_matches.append(mid)

        # 5. Fare range
        fare_range = approximate_fare_range(request.vehicle_type, km, len(room.members))

        return RequestResult(room.room_id, filtered_matches, fare_range)

    def cancel_request(self, rider_id):
        """Takes a rider out of matching and out of their room (before a driver is assigned)."""
        if not self.riders.contains(rider_id):
            raise KeyError(f"Rider {rider_id} has no request")
        record = self.riders.get(rider_id)

        for room_id in self.rooms_by_id.keys():
            room = self.rooms_by_id.get(room_id)
            if rider_id in room.rider_ids() and self.ride_of_room.contains(room_id):
                offered = self.rides.get(self.ride_of_room.get(room_id))
                if offered.status != "offered":
                    raise ValueError("A driver is already assigned, so this ride can no longer be cancelled here")
                self._drop_offer(offered)      # still only an offer: take it back from the driver

        self.engine.unregister(rider_id)
        self.room_manager.remove(rider_id, record.request)
        self.riders.remove(rider_id)
        if self.votes.contains(rider_id):
            self.votes.remove(rider_id)

    def set_rider_user(self, rider_id, user_id):
        self.user_of_rider.put(rider_id, user_id)

    def room_of(self, rider_id):
        for room_id in self.rooms_by_id.keys():
            room = self.rooms_by_id.get(room_id)
            if rider_id in room.rider_ids():
                return room
        return None

    def ride_for_room(self, room_id):
        if self.ride_of_room.contains(room_id):
            return self.rides.get(self.ride_of_room.get(room_id))
        return None

    def _group_key(self, room):
        return ",".join(sorted(room.rider_ids()))

    def room_status(self, room_id, now=None):
        """Who is in the room, who has accepted, and the 15 s timer when the room is full."""
        if not self.rooms_by_id.contains(room_id):
            raise KeyError(f"Room {room_id} not found")
        now = time.time() if now is None else now
        room = self.rooms_by_id.get(room_id)
        ids = room.rider_ids()

        seconds_left = None
        if room.is_full() and not room.closed:
            if not self.full_since.contains(room_id):
                self.full_since.put(room_id, now)
            elapsed = now - self.full_since.get(room_id)
            if elapsed >= GROUP_ACCEPT_SECONDS:
                # time is up: everybody must accept again in a fresh 15 s
                for rid in ids:
                    if self.votes.contains(rid):
                        self.votes.remove(rid)
                self.full_since.put(room_id, now)
                elapsed = 0
            seconds_left = math.ceil(GROUP_ACCEPT_SECONDS - elapsed)
        elif self.full_since.contains(room_id):
            self.full_since.remove(room_id)

        key = self._group_key(room)
        accepted = [rid for rid in ids if self.votes.contains(rid) and self.votes.get(rid) == key]
        ride = self.ride_for_room(room_id)
        members = []
        for m_rider, _ in room.members:
            user_id = self.user_of_rider.get(m_rider.id) if self.user_of_rider.contains(m_rider.id) else None
            members.append({"rider_id": m_rider.id, "name": m_rider.name, "user_id": user_id,
                            "rating": round(self.rating_of(m_rider.id), 1)})
        # exact share for the riders now in the room: full vehicle fare / riders (longest trip sets the total)
        max_km = 0.0
        for m_rider, _ in room.members:
            record = self.riders.get(m_rider.id)
            if record.km > max_km:
                max_km = record.km
        exact_share = exact_fare(room.vehicle_type, max_km, len(room.members))
        return {
            "room_id": room_id,
            "exact_share": exact_share,
            "vehicle_type": room.vehicle_type,
            "capacity": room.capacity,
            "members": members,
            "accepted": accepted,
            "ready": room.closed,           # everyone agreed (or a driver was already found)
            "seconds_left": seconds_left,
            "ride_id": ride.ride_id if ride else None,
        }

    def vote_continue(self, rider_id, now=None):
        """A rider says "continue with this group". When every member has said it, the room closes."""
        room = self.room_of(rider_id)
        if room is None:
            raise KeyError(f"Rider {rider_id} is not in a room")
        if not room.closed:
            self.room_status(room.room_id, now)   # keeps the timer up to date first
            self.votes.put(rider_id, self._group_key(room))
            key = self._group_key(room)
            everyone = True
            for rid in room.rider_ids():
                if not (self.votes.contains(rid) and self.votes.get(rid) == key):
                    everyone = False
            if everyone:
                room.closed = True               # nobody else can join now
        return self.room_status(room.room_id, now)

    # ---- driver offer -------------------------------------------------------
    def _ride_facts(self, room):
        """Longest trip, first rider's pickup, and the drop of the rider who travels furthest."""
        max_km = 0.0
        far = None
        for m_rider, _ in room.members:
            record = self.riders.get(m_rider.id)
            if record.km > max_km or far is None:
                max_km = record.km
                far = record
        first = self.riders.get(room.members[0][0].id)
        pickup = {"name": first.pickup_name or "Pickup", "lat": first.pickup_lat, "lon": first.pickup_lon}
        drop = None
        if far.drop_lat is not None:
            drop = {"name": far.drop_name or "Drop", "lat": far.drop_lat, "lon": far.drop_lon}
        return max_km, first, pickup, drop

    def _make_ride(self, room, driver, status):
        max_km, first, pickup, drop = self._ride_facts(room)
        self.ride_counter += 1
        ride_id = f"ride_{self.ride_counter}"
        num_riders = len(room.members)
        share = exact_fare(room.vehicle_type, max_km, num_riders)
        otp = self.otp_service.generate(ride_id) if status == "confirmed" else None
        rider_ids = [m[0].id for m in room.members]
        ride = Ride(ride_id, room.room_id, room.vehicle_type, driver.id, rider_ids, max_km, share, otp)
        ride.status = status
        ride.driver_name = driver.name
        ride.pickup = pickup
        ride.drop = drop
        ride.riders = [{"rider_id": m[0].id, "name": m[0].name} for m in room.members]
        return ride

    def _store_ride(self, ride):
        self.rides.put(ride.ride_id, ride)
        self.ride_of_room.put(ride.room_id, ride.ride_id)

    def _drop_offer(self, ride, declined_by=None, now=None):
        """Takes an offered ride back. The driver is freed (and remembered if he declined)."""
        self.dispatcher.release_driver(ride.driver_id)
        if declined_by is not None:
            t = time.time() if now is None else now
            self.declined.put(f"{ride.room_id}|{declined_by}", t)
        self.rides.remove(ride.ride_id)
        self.ride_of_room.remove(ride.room_id)

    def _declined_drivers(self, room_id, now):
        out = []
        for key in self.declined.keys():
            rid, _, did = key.partition("|")
            if rid == room_id and now - self.declined.get(key) < DECLINE_COOLDOWN:
                out.append(did)
        return out

    def request_driver(self, room_id, now=None):
        """Called again and again while the riders wait. Returns the Ride once a driver accepted,
        otherwise None (see ride_for_room(...).status == "offered" to know if someone is deciding)."""
        if not self.rooms_by_id.contains(room_id):
            raise KeyError(f"Room {room_id} not found")
        now = time.time() if now is None else now
        room = self.rooms_by_id.get(room_id)

        ride = self.ride_for_room(room_id)
        if ride is not None and ride.status == "offered" and now - ride.offered_at >= OFFER_SECONDS:
            self._drop_offer(ride, declined_by=ride.driver_id, now=now)   # no answer counts as a decline
            ride = None
        if ride is not None:
            return ride if ride.status != "offered" else None

        first = self.riders.get(room.members[0][0].id)
        spot_id = room.members[0][1].pickup_spot or "campus"
        driver = self.dispatcher.find_driver(
            spot_id, first.pickup_lat, first.pickup_lon, room.vehicle_type,
            exclude=self._declined_drivers(room_id, now))
        if driver is None:
            return None

        room.closed = True
        ride = self._make_ride(room, driver, "offered")
        ride.offered_at = now
        self._store_ride(ride)
        return None

    def driver_accept(self, ride_id, driver_id, now=None):
        ride = self._ride_of_driver(ride_id, driver_id)
        now = time.time() if now is None else now
        if ride.status != "offered":
            raise ValueError("This ride is not waiting for an answer")
        if now - ride.offered_at >= OFFER_SECONDS:
            raise ValueError("This offer has expired")
        ride.otp = self.otp_service.generate(ride_id)
        ride.status = "confirmed"
        return ride

    def driver_reject(self, ride_id, driver_id, now=None):
        ride = self._ride_of_driver(ride_id, driver_id)
        if ride.status != "offered":
            raise ValueError("This ride is not waiting for an answer")
        self._drop_offer(ride, declined_by=driver_id, now=now)

    def _ride_of_driver(self, ride_id, driver_id):
        if not self.rides.contains(ride_id):
            raise KeyError(f"Ride {ride_id} unknown")
        ride = self.rides.get(ride_id)
        if ride.driver_id != driver_id:
            raise ValueError("This ride belongs to another driver")
        return ride

    def ride_of_driver(self, driver_id, now=None):
        """The ride a driver is dealing with right now (offered, accepted or on the road), or None."""
        now = time.time() if now is None else now
        for ride_id in self.rides.keys():
            ride = self.rides.get(ride_id)
            if ride.driver_id != driver_id or ride.status == "completed":
                continue
            if ride.status == "offered" and now - ride.offered_at >= OFFER_SECONDS:
                self._drop_offer(ride, declined_by=driver_id, now=now)
                continue
            return ride
        return None

    def confirm_ride(self, room_id):
        """Gives the room a driver straight away, with no accept step (the old behaviour)."""
        if not self.rooms_by_id.contains(room_id):
            raise KeyError(f"Room {room_id} not found")

        room = self.rooms_by_id.get(room_id)
        if self.ride_of_room.contains(room_id):
            raise ValueError(f"Room {room_id} already has a ride")

        first = self.riders.get(room.members[0][0].id)
        spot_id = room.members[0][1].pickup_spot or "campus"
        driver = self.dispatcher.find_driver(spot_id, first.pickup_lat, first.pickup_lon, room.vehicle_type)
        if driver is None:
            return None

        room.closed = True
        ride = self._make_ride(room, driver, "confirmed")
        self._store_ride(ride)
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

        ride.payments = split_payment(ride.vehicle_type, ride.km, ride.rider_ids)
        return ride.payments

    def submit_review(self, ride_id, reviewer_id, target_id, stars):
        """A rider rates the driver or one co-passenger after the ride.
        Returns {"role": "driver" | "rider", "target_identity", "reviewer_identity", "score", "count"}."""
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

        # one review per reviewer and target for each ride
        review_key = f"{ride_id}|{reviewer_id}|{target_id}"
        if self.review_tracker.contains(review_key):
            raise ValueError(f"Reviewer {reviewer_id} already reviewed target {target_id} for ride {ride_id}")

        reviewer_identity = self.identity(reviewer_id)
        target_identity = self.identity(target_id)
        self.reviews.submit_review(reviewer_identity, target_identity, stars)
        self.review_tracker.put(review_key, True)

        if is_other_rider:
            record = self.riders.get(target_id)
            if record:
                # keep the Rider object (used to sort matches) in step with the EMA score
                record.rider.compatibility_score = self.reviews.get_score(target_identity)

        summary = self.reviews.summary(target_identity)
        return {
            "role": "driver" if is_driver else "rider",
            "reviewer_identity": reviewer_identity,
            "target_identity": target_identity,
            "score": self.reviews.get_score(target_identity),
            "count": summary["count"],
        }
