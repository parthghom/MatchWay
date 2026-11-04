import os
from supabase import create_client, Client
from app.models.driver import Driver
from app.models.rider import Rider

class SupabaseRepository:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        self.client: Client = create_client(url, key)

    def save_driver(self, driver):
        data = driver.model_dump()
        self.client.table("drivers").upsert(data).execute()

    def save_spot(self, spot_id, name, latitude, longitude):
        data = {"spot_id": spot_id, "name": name, "latitude": latitude, "longitude": longitude}
        self.client.table("spots").upsert(data).execute()

    def save_rider(self, rider):
        data = rider.model_dump()
        self.client.table("riders").upsert(data).execute()

    def save_ride(self, ride):
        # ride is a Ride object from RideService
        data = {
            "ride_id": ride.ride_id,
            "room_id": ride.room_id,
            "vehicle_type": ride.vehicle_type,
            "driver_id": ride.driver_id,
            "rider_ids": ride.rider_ids,
            "km": ride.km,
            "exact_share": ride.exact_share,
            "status": ride.status
        }
        self.client.table("rides").upsert(data).execute()

    def save_review(self, ride_id, reviewer_id, target_id, stars):
        data = {
            "ride_id": ride_id,
            "reviewer_id": reviewer_id,
            "target_id": target_id,
            "stars": stars
        }
        self.client.table("reviews").insert(data).execute()

    def load_drivers(self):
        res = self.client.table("drivers").select("*").execute()
        drivers_data = res.data
        return [Driver(**d) for d in drivers_data]

    def load_spots(self):
        res = self.client.table("spots").select("*").execute()
        spots_data = res.data
        return [(d["spot_id"], d["name"], d["latitude"], d["longitude"]) for d in spots_data]
