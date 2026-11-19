from fastapi import APIRouter, Depends, Header, HTTPException
from app import state
from app.auth import get_current_user
from app.api.schemas import (
    SpotRequest, SpotResponse, RideRequestPayload, RideRequestResponse,
    ConfirmRequest, CancelRequest, ContinueRequest, ConfirmResponse, StartRideRequest, StartRideResponse,
    CompleteRideRequest, CompleteRideResponse, ReviewRequest, ReviewResponse,
    DriverLocationRequest, DriverOfflineRequest, DriverAnswerRequest,
    VerifyEmailRequest, VerifyImageRequest, VerifySelfieRequest, VerifyResponse, UserVerifyStatus, FareEstimateResponse
)
from app.models.driver import Driver
from app.engine.fare import distance_km, approximate_fare_range, vehicle_fare
from app.models.constants import VEHICLE_CAPACITY

import base64
import time
from app.engine.ride_service import OFFER_SECONDS
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

@router.get("/drivers/nearby")
async def drivers_nearby(lat: float, lon: float, vehicle_type: str):
    """How many free drivers are around a point: 2 km first, then +1 km up to 10 km."""
    if vehicle_type not in ("cab", "auto", "bike"):
        raise HTTPException(status_code=400, detail="vehicle_type must be cab, auto or bike")
    count, radius_m = state.current.dispatcher.count_nearby(lat, lon, vehicle_type)
    return {"count": count, "radius_km": radius_m // 1000}

@router.get("/spots")
async def list_spots():
    return [
        {"spot_id": s.spot_id, "name": s.name, "latitude": s.latitude, "longitude": s.longitude}
        for s in state.current.spots.all_spots()
    ]

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
            payload.pickup_lat, payload.pickup_lon, payload.km,
            payload.pickup_name, payload.drop_lat, payload.drop_lon, payload.drop_name,
            user_id=payload.user_id
        )
        if payload.user_id:
            state.current.rides.set_rider_user(payload.rider.id, payload.user_id)
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

@router.get("/rooms/{room_id}")
async def room_status(room_id: str):
    try:
        return state.current.rides.room_status(room_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/rooms/continue")
async def room_continue(payload: ContinueRequest):
    try:
        return state.current.rides.vote_continue(payload.rider_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/rides/cancel")
async def cancel_ride(payload: CancelRequest):
    try:
        state.current.rides.cancel_request(payload.rider_id)
        return {"cancelled": True}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rides/confirm")
async def confirm_ride(payload: ConfirmRequest):
    """Called every few seconds by the waiting riders. A driver is offered the ride; the answer
    is confirmed=True only after he accepts (then the OTP is shown to the riders)."""
    try:
        svc = state.current.rides
        result = svc.request_driver(payload.room_id)
        if result is None:
            ride = svc.ride_for_room(payload.room_id)
            if ride is not None and ride.status == "offered":
                return {"confirmed": False, "offered": True, "message": "Waiting for the driver to accept"}
            return {"confirmed": False, "offered": False, "message": "No driver available"}

        try:
            state.current.repo.save_ride(result)
        except Exception as e:
            print(f"Warning: Storage error: {e}")

        return _ride_for_rider(result) | {"confirmed": True}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def _ride_for_rider(ride):
    svc = state.current.rides
    return {
        "ride_id": ride.ride_id,
        "driver_id": ride.driver_id,
        "driver_name": ride.driver_name,
        "driver_rating": svc.rating_summary(svc.identity(ride.driver_id)),
        "vehicle_type": ride.vehicle_type,
        "riders": ride.riders,
        "rider_ids": ride.rider_ids,
        "exact_share": ride.exact_share,
        "otp": ride.otp,
        "status": ride.status,
        "payments": [{"rider_id": r, "amount": a} for r, a in (ride.payments or [])] if ride.payments else None,
    }

@router.get("/rides/{ride_id}")
async def ride_status(ride_id: str):
    """What the riders poll after the driver accepted: confirmed -> in_progress -> completed."""
    svc = state.current.rides
    if not svc.rides.contains(ride_id):
        raise HTTPException(status_code=404, detail=f"Ride {ride_id} unknown")
    return _ride_for_rider(svc.rides.get(ride_id))

# ---- driver side -----------------------------------------------------------
@router.post("/drivers/location")
async def driver_location(payload: DriverLocationRequest):
    """The driver app calls this every few seconds: it keeps him on the map and available for offers."""
    if payload.vehicle_type not in VEHICLE_CAPACITY:
        raise HTTPException(status_code=400, detail="vehicle_type must be cab, auto or bike")
    d = state.current.dispatcher.set_location(
        payload.driver_id, payload.name, payload.vehicle_type, payload.latitude, payload.longitude)
    return {"driver_id": d.id, "is_busy": d.is_busy}

@router.post("/drivers/offline")
async def driver_offline(payload: DriverOfflineRequest):
    if state.current.rides.ride_of_driver(payload.driver_id) is not None:
        raise HTTPException(status_code=400, detail="Finish your current ride first")
    state.current.dispatcher.go_offline(payload.driver_id)
    return {"offline": True}

@router.get("/drivers/{driver_id}/ride")
async def driver_current_ride(driver_id: str):
    """The ride this driver should be looking at (offer, trip to pickup, or trip to drop), or null."""
    svc = state.current.rides
    ride = svc.ride_of_driver(driver_id)
    if ride is None:
        return None
    room = svc.rooms_by_id.get(ride.room_id)
    names = [m[0].name for m in room.members]
    left = None
    if ride.status == "offered":
        left = max(0, int(OFFER_SECONDS - (time.time() - ride.offered_at)))
    return {
        "ride_id": ride.ride_id,
        "status": ride.status,
        "vehicle_type": ride.vehicle_type,
        "pickup": ride.pickup,
        "drop": ride.drop,
        "km": ride.km,
        "riders": len(ride.rider_ids),
        "rider_names": names,
        "total_fare": vehicle_fare(ride.vehicle_type, ride.km),
        "fare_each": ride.exact_share,
        "seconds_left": left,
    }

@router.post("/rides/driver/accept")
async def driver_accept(payload: DriverAnswerRequest):
    try:
        ride = state.current.rides.driver_accept(payload.ride_id, payload.driver_id)
        try:
            state.current.repo.save_ride(ride)
        except Exception as e:
            print(f"Warning: Storage error: {e}")
        return {"ride_id": ride.ride_id, "status": ride.status}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rides/driver/reject")
async def driver_reject(payload: DriverAnswerRequest):
    try:
        state.current.rides.driver_reject(payload.ride_id, payload.driver_id)
        return {"rejected": True}
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

        # keep the finished trip (it is already on the history stacks) so it survives a restart
        for role, user_id, trip in state.current.rides.rides.get(payload.ride_id).new_history:
            try:
                state.current.repo.save_trip(role, user_id, trip)
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
async def submit_review(payload: ReviewRequest, authorization: str = Header(None)):
    """A rider rates the driver or a co-passenger (1-5 stars) once the ride is completed.
    The star goes into the target's EMA rating, which is saved and shown on his profile."""
    svc = state.current.rides
    # a logged-in rider may only review as himself
    if svc.user_of_rider.contains(payload.reviewer_id):
        user = await get_current_user(authorization)
        if user.id != svc.user_of_rider.get(payload.reviewer_id):
            raise HTTPException(status_code=403, detail="You can only review as yourself")
    try:
        result = svc.submit_review(payload.ride_id, payload.reviewer_id, payload.target_id, payload.stars)

        try:
            # saved against the PEOPLE (user ids), so the rating survives restarts and later rides
            state.current.repo.save_review(
                payload.ride_id, result["reviewer_identity"], result["target_identity"],
                payload.stars, result["role"])
            target_record = svc.riders.get(payload.target_id)
            if target_record:
                state.current.repo.save_rider(target_record.rider)
        except Exception as e:
            print(f"Warning: Storage error: {e}")
        try:
            # the stars you gave are part of that ride in your history
            if result["history_trip"] is not None:
                state.current.repo.save_trip("rider", result["history_user"], result["history_trip"])
        except Exception as e:
            print(f"Warning: Storage error: {e}")

        return {"ok": True, "target_score": result["score"], "target_count": result["count"], "role": result["role"]}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history/{role}/{user_id}")
async def trip_history(role: str, user_id: str, limit: int = 50):
    """Finished trips of a rider or a driver, newest first. We read them straight off that
    person's Stack: the top of the stack is the latest trip."""
    if role not in ("rider", "driver"):
        raise HTTPException(status_code=404, detail="role must be rider or driver")
    return {"trips": state.current.rides.history.get(role, user_id, max(1, min(limit, 50)))}

@router.get("/ratings/me")
async def my_rating(user=Depends(get_current_user)):
    """The signed-in rider's or driver's EMA rating, for the profile page."""
    return state.current.rides.rating_summary(user.id)

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


@router.get("/fare/options")
async def fare_options(km: float):
    """Fare for every vehicle over `km`: solo price and the shared range."""
    if km < 0:
        raise HTTPException(status_code=400, detail="Distance cannot be negative")
    out = []
    for vehicle in ("bike", "auto", "cab"):
        low, high = approximate_fare_range(vehicle, km, 1)
        out.append({
            "vehicle_type": vehicle,
            "capacity": VEHICLE_CAPACITY[vehicle],
            "full_fare": vehicle_fare(vehicle, km),
            "fare_low": low,
            "fare_high": high,
        })
    return out
