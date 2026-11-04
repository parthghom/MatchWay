from fastapi import APIRouter, HTTPException
from app import state
from app.api.schemas import (
    SpotRequest, SpotResponse, RideRequestPayload, RideRequestResponse,
    ConfirmRequest, ConfirmResponse, StartRideRequest, StartRideResponse,
    CompleteRideRequest, CompleteRideResponse, ReviewRequest, ReviewResponse,
    VerifyEmailRequest, VerifyImageRequest, VerifySelfieRequest, VerifyResponse, UserVerifyStatus, FareEstimateResponse
)
from app.models.driver import Driver
from app.engine.fare import distance_km, approximate_fare_range

import base64
import datetime
import binascii

router = APIRouter()

@router.post("/drivers")
async def create_driver(driver: Driver):
    try:
        state.current.dispatcher.update_driver(driver)
        try:
            state.current.repo.save_driver(driver)
        except Exception as e:
            print(f"Warning: Storage error: {e}")
        return driver
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/drivers")
async def list_drivers():
    drivers = []
    for d_id in state.current.dispatcher.drivers.keys():
        d = state.current.dispatcher.drivers.get(d_id)
        drivers.append(d)
    return drivers

@router.post("/spots")
async def create_spot(spot: SpotRequest):
    try:
        state.current.spots.add_spot(spot.spot_id, spot.name, spot.latitude, spot.longitude)
        try:
            state.current.repo.save_spot(spot.spot_id, spot.name, spot.latitude, spot.longitude)
        except Exception as e:
            print(f"Warning: Storage error: {e}")
        return spot
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/spots/nearest")
async def get_nearest_spot(lat: float, lon: float):
    try:
        suggestion = state.current.spots.nearest_spot(lat, lon)
        return {
            "spot_id": suggestion.spot.spot_id,
            "name": suggestion.spot.name,
            "distance_m": suggestion.distance_m,
            "walk_minutes": suggestion.walk_minutes,
            "walk_to_save": suggestion.walk_to_save
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rides/request")
async def request_ride(payload: RideRequestPayload):
    try:
        result = state.current.rides.request_ride(
            payload.rider, payload.request, payload.route,
            payload.pickup_lat, payload.pickup_lon, payload.km
        )
        try:
            state.current.repo.save_rider(payload.rider)
        except Exception as e:
            print(f"Warning: Storage error: {e}")
        return {
            "room_id": result.room_id,
            "matches": result.matches,
            "fare_low": result.fare_range[0],
            "fare_high": result.fare_range[1]
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rides/confirm")
async def confirm_ride(payload: ConfirmRequest):
    try:
        result = state.current.rides.confirm_ride(payload.room_id)
        if result is None:
            return {
                "confirmed": False,
                "message": "No driver available"
            }

        try:
            ride = state.current.rides.rides.get(result.ride_id)
            state.current.repo.save_ride(ride)
        except Exception as e:
            print(f"Warning: Storage error: {e}")

        return {
            "confirmed": True,
            "ride_id": result.ride_id,
            "driver_id": result.driver_id,
            "rider_ids": result.rider_ids,
            "exact_share": result.exact_share,
            "otp": result.otp,
            "status": result.status
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rides/start")
async def start_ride(payload: StartRideRequest):
    try:
        success = state.current.rides.start_ride(payload.ride_id, payload.otp)
        if not success:
            raise HTTPException(status_code=400, detail="Wrong OTP")

        try:
            ride = state.current.rides.rides.get(payload.ride_id)
            state.current.repo.save_ride(ride)
        except Exception as e:
            print(f"Warning: Storage error: {e}")

        return {"ride_id": payload.ride_id, "status": "in_progress"}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rides/complete")
async def complete_ride(payload: CompleteRideRequest):
    try:
        payments_list = state.current.rides.complete_ride(payload.ride_id)

        try:
            ride = state.current.rides.rides.get(payload.ride_id)
            state.current.repo.save_ride(ride)
        except Exception as e:
            print(f"Warning: Storage error: {e}")

        payments = [{"rider_id": r_id, "amount": amt} for r_id, amt in payments_list]
        return {
            "ride_id": payload.ride_id,
            "status": "completed",
            "payments": payments
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rides/review")
async def submit_review(payload: ReviewRequest):
    try:
        state.current.rides.submit_review(payload.ride_id, payload.reviewer_id, payload.target_id, payload.stars)

        try:
            state.current.repo.save_review(payload.ride_id, payload.reviewer_id, payload.target_id, payload.stars)
            target_record = state.current.rides.riders.get(payload.target_id)
            if target_record:
                state.current.repo.save_rider(target_record.rider)
        except Exception as e:
            print(f"Warning: Storage error: {e}")

        target_score = state.current.rides.reviews.get_score(payload.target_id)
        return {"ok": True, "target_score": target_score}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/email")
async def verify_email(payload: VerifyEmailRequest):
    try:
        result = state.current.verification.verify_email(payload.user_id, payload.email)
        return {"passed": result["passed"], "steps": result["steps"]}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/id-card")
async def verify_id_card(payload: VerifyImageRequest):
    try:
        image_bytes = base64.b64decode(payload.image_base64)
        text = state.current.ocr(image_bytes)
        result = state.current.verification.verify_id_card(payload.user_id, text, datetime.date.today().year)
        return {"passed": result["passed"], "steps": result["steps"]}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        if isinstance(e, binascii.Error) or "Incorrect padding" in str(e):
            raise HTTPException(status_code=400, detail="Invalid base64")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/licence")
async def verify_licence(payload: VerifyImageRequest):
    try:
        image_bytes = base64.b64decode(payload.image_base64)
        text = state.current.ocr(image_bytes)
        result = state.current.verification.verify_licence(payload.user_id, text)
        return {"passed": result["passed"], "steps": result["steps"]}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        if isinstance(e, binascii.Error) or "Incorrect padding" in str(e):
            raise HTTPException(status_code=400, detail="Invalid base64")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/vehicle")
async def verify_vehicle(payload: VerifyImageRequest):
    try:
        image_bytes = base64.b64decode(payload.image_base64)
        text = state.current.ocr(image_bytes)
        result = state.current.verification.verify_vehicle(payload.user_id, text)
        return {"passed": result["passed"], "steps": result["steps"]}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        if isinstance(e, binascii.Error) or "Incorrect padding" in str(e):
            raise HTTPException(status_code=400, detail="Invalid base64")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/selfie")
async def verify_selfie(payload: VerifySelfieRequest):
    try:
        id_bytes = base64.b64decode(payload.id_image_base64)
        selfie_bytes = base64.b64decode(payload.selfie_base64)
        match = state.current.face(id_bytes, selfie_bytes)
        result = state.current.verification.verify_selfie(payload.user_id, match)
        return {"passed": result["passed"], "steps": result["steps"]}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        if isinstance(e, binascii.Error) or "Incorrect padding" in str(e):
            raise HTTPException(status_code=400, detail="Invalid base64")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verify/{user_id}")
async def get_verification_status(user_id: str):
    try:
        status = state.current.verification.get_status(user_id)
        return {
            "user_id": status["user_id"],
            "steps": status["steps"],
            "student_verified": status["student_verified"],
            "driver_verified": status["driver_verified"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/fare/estimate")
async def estimate_fare(
    vehicle_type: str,
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    riders: int = 1
):
    try:
        try:
            km, minutes = state.current.routing(origin_lat, origin_lon, dest_lat, dest_lon)
            source = "ola_maps"
        except Exception:
            km = distance_km(origin_lat, origin_lon, dest_lat, dest_lon)
            minutes = None
            source = "straight_line"

        fare_low, fare_high = approximate_fare_range(vehicle_type, km, riders)

        return FareEstimateResponse(
            km=km,
            minutes=minutes,
            source=source,
            fare_low=fare_low,
            fare_high=fare_high
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
