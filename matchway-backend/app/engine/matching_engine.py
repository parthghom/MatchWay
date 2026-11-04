# The MatchingEngine coordinates the discovery of compatible ride-share partners.
# It leverages a Trie to find riders sharing the same route corridor (prefix of stops)
# and an IntervalTree to identify riders with overlapping travel-time windows.
# Candidates from both structures are filtered by flow, vehicle type, and gender
# preferences to ensure a perfectly compatible match.

from app.engine.hash_map import HashMap
from app.engine.trie import Trie
from app.engine.interval_tree import IntervalTree
from app.models.rider import Rider
from app.models.ride_request import RideRequest

class RiderEntry:
    def __init__(self, rider, request, route, active=True):
        self.rider = rider
        self.request = request
        self.route = route
        self.active = active

class MatchingEngine:
    def __init__(self):
        # entries: rider_id -> RiderEntry
        self.entries = HashMap()
        self.trie = Trie()
        self.intervals = IntervalTree()

    def register(self, rider, request, route):
        """Registers a rider for matching."""
        entry = RiderEntry(rider, request, route)
        self.entries.put(rider.id, entry)
        self.trie.insert(route, rider.id)
        self.intervals.insert(request.time_window_start, request.time_window_end, rider.id)

    def unregister(self, rider_id):
        """Marks a rider as inactive and removes them from the Trie."""
        if not self.entries.contains(rider_id):
            return

        entry = self.entries.get(rider_id)
        entry.active = False
        # Remove from trie to stop them appearing in corridor searches
        self.trie.remove(entry.route, rider_id)

    def find_matches(self, rider_id, min_shared_stops=2):
        """Finds compatible riders based on corridor, time, flow, vehicle, and gender."""
        if not self.entries.contains(rider_id):
            raise KeyError(f"Rider {rider_id} not registered")

        me = self.entries.get(rider_id)
        me_rider = me.rider
        me_req = me.request
        me_route = me.route

        # a) Corridor: Route sharing leading stops
        # We need the first 'min_shared_stops' of the route
        prefix = me_route[:min_shared_stops]
        corridor_riders = self.trie.riders_with_prefix(prefix)

        # b) Time: Overlapping windows
        time_riders = self.intervals.overlap_search(me_req.time_window_start, me_req.time_window_end)

        # Combine and filter
        matches = []
        # We iterate through one list and check membership/constraints in the other
        # and our entries map.
        for other_id in corridor_riders:
            if other_id == rider_id:
                continue

            # Check if they are also in the time_riders list
            in_time = False
            for tr_id in time_riders:
                if tr_id == other_id:
                    in_time = True
                    break

            if not in_time:
                continue

            # Check entry exists and is active
            if not self.entries.contains(other_id):
                continue
            other = self.entries.get(other_id)
            if not other.active:
                continue

            # c) Flow and Vehicle Type
            if other.request.flow != me_req.flow:
                continue
            if other.request.vehicle_type != me_req.vehicle_type:
                continue

            # d) Gender preferences (must work both ways)
            other_rider = other.rider

            # Check if me is compatible with other
            if me_rider.preference == "male_only" and other_rider.gender == "female":
                continue
            if me_rider.preference == "female_only" and other_rider.gender == "male":
                continue

            # Check if other is compatible with me
            if other_rider.preference == "male_only" and me_rider.gender == "female":
                continue
            if other_rider.preference == "female_only" and me_rider.gender == "male":
                continue

            matches.append(other_rider)

        # Sort results by compatibility_score, highest first (Insertion Sort)
        for i in range(1, len(matches)):
            key_rider = matches[i]
            j = i - 1
            while j >= 0 and matches[j].compatibility_score < key_rider.compatibility_score:
                matches[j + 1] = matches[j]
                j -= 1
            matches[j + 1] = key_rider

        # Return only IDs
        return [r.id for r in matches]
