# Pickup happens at fixed virtual spots so riders gather in one place.
# A KD-tree finds the closest spot quickly, and "walk to save" tells a rider
# when the nearest spot is far enough that walking to it (or a better one)
# is the better option.

import math
from app.engine.hash_map import HashMap
from app.engine.kd_tree import KDTree

WALK_SPEED_M_PER_MIN = 80
FAR_THRESHOLD_M = 300

class Spot:
    def __init__(self, spot_id, name, latitude, longitude):
        self.spot_id = spot_id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

class SpotSuggestion:
    def __init__(self, spot, distance_m):
        self.spot = spot
        self.distance_m = round(distance_m, 1)
        self.walk_minutes = math.ceil(self.distance_m / WALK_SPEED_M_PER_MIN)
        self.walk_to_save = self.distance_m > FAR_THRESHOLD_M

class VirtualSpotService:
    def __init__(self):
        self._spots = HashMap()
        self._kd_tree = KDTree()

    def add_spot(self, spot_id, name, latitude, longitude):
        if self._spots.contains(spot_id):
            raise ValueError(f"Spot ID {spot_id} already exists")

        spot = Spot(spot_id, name, latitude, longitude)
        self._spots.put(spot_id, spot)
        self._kd_tree.insert(latitude, longitude, spot_id)

    def nearest_spot(self, lat, lon):
        if self._kd_tree.size() == 0:
            raise ValueError("No spots available")

        dist, spot_id = self._kd_tree.nearest(lat, lon)
        spot = self._spots.get(spot_id)
        return SpotSuggestion(spot, dist)

    def spots_within(self, lat, lon, radius_m):
        results = self._kd_tree.radius_search(lat, lon, radius_m)

        suggestions = []
        for dist, spot_id in results:
            spot = self._spots.get(spot_id)
            suggestions.append(SpotSuggestion(spot, dist))

        return suggestions

    def size(self):
        return self._spots.size()
