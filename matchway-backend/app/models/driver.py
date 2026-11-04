from pydantic import BaseModel
from typing import Literal

class Driver(BaseModel):
    id: str
    name: str
    vehicle_type: Literal["cab", "auto", "bike"]
    is_busy: bool = False
    latitude: float
    longitude: float
