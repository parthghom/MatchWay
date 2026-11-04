from fastapi import APIRouter, Depends, HTTPException, Body
from app import state
from app.auth import get_current_user, AuthUser
from app.engine import onboarding
from app.storage.profile_repo import get_setting
from datetime import date
import base64

router = APIRouter()

def validate_phone(phone):
    phone = phone.replace(" ", "")
    if len(phone) != 10:
        return False
    if phone[0] not in "6789":
        return False
    return True

def validate_dob(dob_str, role):
    try:
        dob = date.fromisoformat(dob_str)
        today = date.today()
        if dob > today:
            return False

        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        min_age = 16 if role == "student" else 18
        return age >= min_age
    except ValueError:
        return False

@router.get("/profile/me")
async def get_me(user: AuthUser = Depends(get_current_user)):
    profile = state.current.profiles.get_profile(user.id)
    if not profile:
        return {"exists": False, "next_step": "role"}

    docs = state.current.profiles.list_documents(user.id)
    vehicle = state.current.profiles.get_vehicle(user.id)

    # Determine next step
    has_details = profile.get("full_name") is not None
    doc_types_done = [d["doc_type"] for d in docs]
    has_vehicle = vehicle is not None

    step = onboarding.next_step(
        profile["role"],
        has_details,
        doc_types_done,
        has_vehicle
    )

    # Build profile status
    doc_statuses = [d["status"] for d in docs]
    status = onboarding.profile_status(step, doc_statuses)

    # Remove storage_path from docs if present
    sanitized_docs = []
    for d in docs:
        sanitized_docs.append({
            "doc_type": d["doc_type"],
            "status": d["status"],
            "doc_number": d.get("doc_number")
        })

    return {
        "exists": True,
        "profile": {**profile, "status": status},
        "documents": sanitized_docs,
        "vehicle": vehicle,
        "next_step": step
    }

@router.post("/profile/role")
async def set_role(role: str = Body(..., embed=True), user: AuthUser = Depends(get_current_user)):
    if role not in ["student", "driver"]:
        raise HTTPException(status_code=422, detail="Role must be student or driver")

    if not onboarding.email_allowed_for_role(user.email, role):
        if role == "student":
            raise HTTPException(status_code=403, detail="Students must sign in with their college email")
        else:
            raise HTTPException(status_code=403, detail="Email not allowed for this role")

    profile = state.current.profiles.get_profile(user.id)
    if profile:
        if profile["role"] == role:
            return profile
        else:
            raise HTTPException(status_code=409, detail="Profile already exists with a different role")

    new_profile = state.current.profiles.upsert_profile(user.id, {
        "email": user.email,
        "role": role,
        "status": "incomplete"
    })
    return new_profile

@router.post("/profile/details")
async def set_details(
    details: dict = Body(...),
    user: AuthUser = Depends(get_current_user)
):
    profile = state.current.profiles.get_profile(user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    full_name = details.get("full_name", "")
    phone = details.get("phone", "")
    gender = details.get("gender", "")
    dob = details.get("date_of_birth", "")

    if not (2 <= len(full_name) <= 60):
        raise HTTPException(status_code=400, detail="Full name must be between 2 and 60 characters")

    if not validate_phone(phone):
        raise HTTPException(status_code=400, detail="Phone must be 10 digits and start with 6, 7, 8 or 9")

    if gender not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be male or female")

    if not validate_dob(dob, profile["role"]):
        raise HTTPException(status_code=400, detail="Invalid date of birth or age requirement not met")

    updated_profile = state.current.profiles.upsert_profile(user.id, {
        "full_name": full_name,
        "phone": phone,
        "gender": gender,
        "date_of_birth": dob
    })
    return updated_profile

@router.post("/profile/document")
async def upload_document(
    doc_type: str = Body(..., embed=True),
    image_base64: str = Body(..., embed=True),
    doc_number: str = Body(None, embed=True),
    user: AuthUser = Depends(get_current_user)
):
    profile = state.current.profiles.get_profile(user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    role = profile["role"]
    if doc_type not in onboarding.docs_for_role(role):
        raise HTTPException(status_code=400, detail="This document is not needed for your role")

    if not profile.get("full_name"):
        raise HTTPException(status_code=400, detail="Complete your details first")

    if doc_type in ["rc", "vehicle_photo"]:
        if not state.current.profiles.get_vehicle(user.id):
            raise HTTPException(status_code=400, detail="Add your vehicle details first")

    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image")

    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image is too large")

    # Check JPEG or PNG
    if not (image_bytes.startswith(b"\xff\xd8\xff") or image_bytes.startswith(b"\x89\x50\x4e\x47")):
        raise HTTPException(status_code=400, detail="Invalid image")

    # Handle doc_number
    clean_num = None
    if doc_type == "aadhaar":
        if doc_number is not None:
            raise HTTPException(status_code=400, detail="The Aadhaar number is not collected, upload the photo only")
    elif doc_type == "pan":
        if not doc_number:
            raise HTTPException(status_code=400, detail="PAN number is required")
        try:
            clean_num = onboarding.clean_pan(doc_number)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif doc_type == "licence":
        if not doc_number:
            raise HTTPException(status_code=400, detail="Licence number is required")
        try:
            clean_num = onboarding.clean_licence(doc_number)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif doc_type == "college_id":
        if doc_number:
            try:
                clean_num = onboarding.clean_college_id(doc_number)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    # Determine status
    auto_approve = get_setting("DEMO_AUTO_APPROVE")
    status = "approved" if auto_approve and auto_approve.lower() == "true" else "pending"

    state.current.profiles.save_document(user.id, doc_type, image_bytes, clean_num, status)

    # Update profile status
    docs = state.current.profiles.list_documents(user.id)
    doc_statuses = [d["status"] for d in docs]

    # Re-calculate next step to pass to profile_status
    has_details = profile.get("full_name") is not None
    doc_types_done = [d["doc_type"] for d in docs]
    has_vehicle = state.current.profiles.get_vehicle(user.id) is not None
    step = onboarding.next_step(role, has_details, doc_types_done, has_vehicle)

    new_status = onboarding.profile_status(step, doc_statuses)
    state.current.profiles.upsert_profile(user.id, {"status": new_status})

    return {"doc_type": doc_type, "status": status, "next_step": step}

@router.post("/profile/vehicle")
async def set_vehicle(
    vehicle_type: str = Body(..., embed=True),
    plate_number: str = Body(..., embed=True),
    user: AuthUser = Depends(get_current_user)
):
    profile = state.current.profiles.get_profile(user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile["role"] == "student":
        raise HTTPException(status_code=403, detail="Only drivers add vehicles")

    # Must upload aadhaar, pan and licence first
    docs = state.current.profiles.list_documents(user.id)
    doc_types_done = [d["doc_type"] for d in docs]

    required_docs = ["aadhaar", "pan", "licence"]
    for rd in required_docs:
        if rd not in doc_types_done:
            raise HTTPException(status_code=400, detail="Upload your personal documents first")

    if vehicle_type not in ["cab", "auto", "bike"]:
        raise HTTPException(status_code=400, detail="Vehicle type must be cab, auto or bike")

    try:
        clean_plate = onboarding.clean_plate(plate_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if state.current.profiles.plate_taken(clean_plate, user.id):
        raise HTTPException(status_code=409, detail="This vehicle number is already registered")

    state.current.profiles.upsert_vehicle(user.id, vehicle_type, clean_plate)

    # Return next_step
    has_details = profile.get("full_name") is not None
    doc_types_done = [d["doc_type"] for d in docs]
    has_vehicle = True
    step = onboarding.next_step(profile["role"], has_details, doc_types_done, has_vehicle)

    return {"vehicle_type": vehicle_type, "plate_number": clean_plate, "next_step": step}
