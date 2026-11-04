from pydantic import BaseModel
from typing import List, Optional
from app.models.driver import Driver
from app.models.rider import Rider
from app.models.ride_request import RideRequest

class SpotRequest(BaseModel):
    spot_id: str
    name: str
    latitude: float
    longitude: float

class SpotResponse(BaseModel):
    spot_id: str
    name: str
    distance_m: float
    walk_minutes: int
    walk_to_save: bool

class RideRequestPayload(BaseModel):
    rider: Rider
    request: RideRequest
    route: List[str]
    pickup_lat: float
    pickup_lon: float
    km: float

class RideRequestResponse(BaseModel):
    room_id: str
    matches: List[str]
    fare_low: float
    fare_high: float

class ConfirmRequest(BaseModel):
    room_id: str

class ConfirmResponse(BaseModel):
    confirmed: bool
    ride_id: Optional[str] = None
    driver_id: Optional[str] = None
    rider_ids: Optional[List[str]] = None
    exact_share: Optional[float] = None
    otp: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None

class StartRideRequest(BaseModel):
    ride_id: str
    otp: str

class StartRideResponse(BaseModel):
    ride_id: str
    status: str

class CompleteRideRequest(BaseModel):
    ride_id: str

class CompleteRideResponse(BaseModel):
    ride_id: str
    status: str
    payments: List[Payment]

class Payment(BaseModel):
    rider_id: str
    amount: float

class ReviewRequest(BaseModel):
    ride_id: str
    reviewer_id: str
    target_id: str
    stars: int

class ReviewResponse(BaseModel):
    ok: bool
    target_score: float

class VerifyEmailRequest(BaseModel):
    user_id: str
    email: str

class VerifyImageRequest(BaseModel):
    user_id: str
    image_base64: str

class VerifySelfieRequest(BaseModel):
    user_id: str
    id_image_base64: str
    selfie_base64: str

class VerifyResponse(BaseModel):
    passed: bool
    steps: List[str]

class UserVerifyStatus(BaseModel):
    user_id: str
    steps: List[str]
    student_verified: bool
    driver_verified: bool

class FareEstimateResponse(BaseModel):
    km: float
    minutes: Optional[float]
    source: str
    fare_low: float
    fare_high: float
