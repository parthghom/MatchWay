from pydantic import BaseModel, model_validator
from typing import Literal, Optional

class RideRequest(BaseModel):
    id: str
    rider_id: str
    flow: Literal["campus_to_destination", "pickup_to_campus"]
    destination: str
    pickup_spot: Optional[str] = None
    vehicle_type: Literal["cab", "auto", "bike"]
    time_window_start: int
    time_window_end: int
    approx_fare: Optional[float] = None

    @model_validator(mode="after")
    def validate_request(self):
        if self.time_window_start > self.time_window_end:
            raise ValueError("time_window_start must be <= time_window_end")

        if self.flow == "pickup_to_campus" and not self.pickup_spot:
            raise ValueError("pickup_spot is required when flow is pickup_to_campus")

        return self
