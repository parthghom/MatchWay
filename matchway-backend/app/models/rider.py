from pydantic import BaseModel, field_validator
from typing import Literal

class Rider(BaseModel):
    id: str
    name: str
    gender: Literal["male", "female"]
    preference: Literal["male_only", "female_only", "mix"]
    compatibility_score: float = 3.0

    @field_validator("preference")
    @classmethod
    def validate_preference(cls, v, info):
        gender = info.data.get("gender")
        if gender == "male" and v == "female_only":
            raise ValueError("Male riders cannot choose female_only preference")
        if gender == "female" and v == "male_only":
            raise ValueError("Female riders cannot choose male_only preference")
        return v
