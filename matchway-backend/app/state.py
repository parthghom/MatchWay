from app.engine.driver_dispatch import DriverDispatcher
from app.engine.ride_service import RideService
from app.engine.virtual_spots import VirtualSpotService
from app.engine.verification import VerificationService
from app.services.ola_maps import route_distance_km
from app.services.ocr import extract_text
from app.services.face import faces_match
from app.storage import get_repository
from app.storage.profile_repo import get_profile_repository

class AppState:
    def __init__(self, repo=None):
        self.repo = get_repository(repo)
        self.profiles = get_profile_repository()
        self.dispatcher = DriverDispatcher()
        self.rides = RideService(self.dispatcher)
        self.spots = VirtualSpotService()
        self.verification = VerificationService()
        self.ocr = extract_text
        self.face = faces_match
        self.routing = route_distance_km



        # Load from repository
        try:
            drivers = self.repo.load_drivers()
            for d in drivers:
                self.dispatcher.update_driver(d)

            spots = self.repo.load_spots()
            for sid, name, lat, lon in spots:
                self.spots.add_spot(sid, name, lat, lon)
        except Exception as e:
            print(f"Warning: Failed to load state from repo: {e}")

current = AppState()

def reset(repo=None):
    global current
    current = AppState(repo=repo)
