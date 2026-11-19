from supabase import create_client, Client
from app.storage.profile_repo import get_setting
from app.models.driver import Driver
from app.models.rider import Rider

class SupabaseRepository:
    def __init__(self):
        url = get_setting("SUPABASE_URL")
        # the server's own key (it bypasses row-level security, which protects trip_history)
        key = get_setting("SUPABASE_SERVICE_KEY") or get_setting("SUPABASE_KEY")
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

    def save_review(self, ride_id, reviewer_id, target_id, stars, target_role=None):
        data = {
            "ride_id": ride_id,
            "reviewer_id": reviewer_id,
            "target_id": target_id,
            "stars": stars
        }
        try:
            self.client.table("reviews").insert({**data, "target_role": target_role}).execute()
        except Exception:
            # the table has no target_role column yet (see supabase_reviews.sql): save the basics
            self.client.table("reviews").insert(data).execute()

    def load_reviews(self):
        """All saved reviews, oldest first (so replaying them gives the same EMA scores as before)."""
        try:
            res = self.client.table("reviews").select("*").order("created_at").execute()
        except Exception:
            res = self.client.table("reviews").select("*").execute()
        return res.data

    def save_trip(self, role, user_id, trip):
        data = {"role": role, "user_id": user_id, "trip_id": trip["id"], "trip": trip}
        self.client.table("trip_history").upsert(data, on_conflict="role,user_id,trip_id").execute()

    def load_trips(self):
        """Every saved trip, oldest first, so pushing them onto the stacks in order leaves the newest on top."""
        try:
            res = self.client.table("trip_history").select("*").order("created_at").execute()
        except Exception:
            res = self.client.table("trip_history").select("*").execute()
        return [{"role": r["role"], "user_id": r["user_id"], "trip": r["trip"]} for r in res.data]

    def load_drivers(self):
        res = self.client.table("drivers").select("*").execute()
        drivers_data = res.data
        return [Driver(**d) for d in drivers_data]

    def load_spots(self):
        res = self.client.table("spots").select("*").execute()
        spots_data = res.data
        return [(d["spot_id"], d["name"], d["latitude"], d["longitude"]) for d in spots_data]
