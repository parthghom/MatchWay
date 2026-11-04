# VirtualRooms facilitate the grouping of riders who are traveling to the same
# destination, using the same vehicle type, and whose travel-time windows overlap.
# It ensures that gender preferences and vehicle capacities are strictly respected,
# creating small "virtual" groups that can be matched with a single driver.

from app.engine.hash_map import HashMap
from app.models.rider import Rider
from app.models.ride_request import RideRequest
from app.models.constants import VEHICLE_CAPACITY

class VirtualRoom:
    def __init__(self, room_id, vehicle_type):
        self.room_id = room_id
        self.vehicle_type = vehicle_type
        self.capacity = VEHICLE_CAPACITY[vehicle_type]
        self.members = [] # List of (rider, request) pairs
        self.closed = False

    def is_full(self):
        return len(self.members) >= self.capacity

    def can_join(self, rider, request):
        if self.closed:
            return False
        # a) Capacity check
        if self.is_full():
            return False

        # b) Time window check
        # New combined window: [max(starts), min(ends)]
        current_max_start = request.time_window_start
        current_min_end = request.time_window_end

        for m_rider, m_req in self.members:
            if m_req.time_window_start > current_max_start:
                current_max_start = m_req.time_window_start
            if m_req.time_window_end < current_min_end:
                current_min_end = m_req.time_window_end

        if current_max_start > current_min_end:
            return False

        # c) Gender preferences
        # Gather all riders including the candidate
        all_riders = [m[0] for m in self.members] + [rider]

        # Determine if there are any males or females in the proposed group
        has_male = False
        has_female = False
        for r in all_riders:
            if r.gender == "male": has_male = True
            if r.gender == "female": has_female = True

        # Every rider's preference must be satisfied
        for r in all_riders:
            if r.preference == "male_only" and has_female:
                return False
            if r.preference == "female_only" and has_male:
                return False

        return True

    def add(self, rider, request):
        if not self.can_join(rider, request):
            raise ValueError("Rider cannot join this room due to constraints")
        self.members.append((rider, request))

    def remove(self, rider_id):
        for i in range(len(self.members)):
            if self.members[i][0].id == rider_id:
                self.members.pop(i)
                return True
        return False

    def rider_ids(self):
        return [m[0].id for m in self.members]

class RoomManager:
    def __init__(self):
        # Key: flow|dest|vehicle -> Value: list of VirtualRoom
        self.rooms_map = HashMap()
        self.room_counter = 0

    def assign(self, rider, request, is_blocked=None):
        key = f"{request.flow}|{request.destination}|{request.vehicle_type}"

        # Get rooms for this key or empty list
        rooms = []
        if self.rooms_map.contains(key):
            rooms = self.rooms_map.get(key)

        # Try to find an existing room that fits
        for room in rooms:
            if room.can_join(rider, request):
                if is_blocked is not None:
                    # Skip room if rider is blocked by ANY member
                    blocked = False
                    for member_rider, _ in room.members:
                        if is_blocked(rider.id, member_rider.id):
                            blocked = True
                            break
                    if blocked:
                        continue

                room.add(rider, request)
                return room

        # No room fits, create a new one
        self.room_counter += 1
        new_room = VirtualRoom(f"room_{self.room_counter}", request.vehicle_type)
        new_room.add(rider, request)

        # Update the rooms list in the HashMap
        rooms.append(new_room)
        self.rooms_map.put(key, rooms)
        return new_room

    def remove(self, rider_id, request):
        key = f"{request.flow}|{request.destination}|{request.vehicle_type}"
        if not self.rooms_map.contains(key):
            return

        rooms = self.rooms_map.get(key)
        for i in range(len(rooms)):
            room = rooms[i]
            if room.remove(rider_id):
                if len(room.members) == 0:
                    rooms.pop(i)
                    if len(rooms) == 0:
                        # Optional: we could remove the key from the map,
                        # but keeping the empty list is also fine.
                        # Let's keep it consistent.
                        self.rooms_map.put(key, rooms)
                else:
                    self.rooms_map.put(key, rooms)
                return

    def room_count(self):
        total = 0
        # Sum lengths of all lists in the HashMap
        # Since we don't have an easy way to iterate the HashMap values except keys(),
        # we'll have to be careful.
        keys = self.rooms_map.keys()
        for k in keys:
            total += len(self.rooms_map.get(k))
        return total
