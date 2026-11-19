from app.models.driver import Driver
from app.models.rider import Rider

class MemoryRepository:
    def __init__(self):
        self.drivers = {}  # id -> Driver
        self.spots = {}     # spot_id -> (name, lat, lon)
        self.riders = {}    # id -> Rider
        self.rides = {}     # ride_id -> Ride (generic object)
        self.reviews = []   # list of dicts

    def save_driver(self, driver):
        self.drivers[driver.id] = driver

    def save_spot(self, spot_id, name, latitude, longitude):
        self.spots[spot_id] = (name, latitude, longitude)

    def save_rider(self, rider):
        self.riders[rider.id] = rider

    def save_ride(self, ride):
        self.rides[ride.ride_id] = ride

    def save_review(self, ride_id, reviewer_id, target_id, stars, target_role=None):
        self.reviews.append({
            "ride_id": ride_id,
            "reviewer_id": reviewer_id,
            "target_id": target_id,
            "stars": stars,
            "target_role": target_role,
        })

    def load_reviews(self):
        """All saved reviews, oldest first. The server replays them at start-up to rebuild every EMA score."""
        return list(self.reviews)

    def load_drivers(self):
        return list(self.drivers.values())

    def load_spots(self):
        # returns list of (spot_id, name, latitude, longitude)
        return [(sid, *vals) for sid, vals in self.spots.items()]
