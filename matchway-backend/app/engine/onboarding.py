# Onboarding logic for user roles and document verification
# Pure functions using only lists and tuples. No dicts or sets.

ALLOWED_EMAIL_DOMAINS = ["college.edu.in","vit.edu"]
STUDENT_DOCS = ["college_id", "selfie"]
DRIVER_DOCS = ["aadhaar", "pan", "licence"]
VEHICLE_DOCS = ["rc", "vehicle_photo"]

def email_allowed_for_role(email, role):
    if role == "student":
        if email.count("@") != 1:
            return False
        parts = email.split("@")
        domain = parts[1].lower()
        # Check if domain is in ALLOWED_EMAIL_DOMAINS
        for d in ALLOWED_EMAIL_DOMAINS:
            if domain == d:
                return True
        return False
    elif role == "driver":
        if email.count("@") != 1:
            return False
        parts = email.split("@")
        domain = parts[1]
        if "." in domain:
            return True
        return False
    else:
        raise ValueError(f"Unknown role: {role}")

def docs_for_role(role):
    if role == "student":
        return STUDENT_DOCS
    elif role == "driver":
        return DRIVER_DOCS + VEHICLE_DOCS
    else:
        raise ValueError(f"Unknown role: {role}")

def next_step(role, has_details, doc_types_done, has_vehicle):
    if role == "student":
        if not has_details:
            return "details"
        # Check for student docs
        for doc in STUDENT_DOCS:
            if doc not in doc_types_done:
                return doc
        return "done"
    elif role == "driver":
        if not has_details:
            return "details"
        # Check for driver docs
        for doc in DRIVER_DOCS:
            if doc not in doc_types_done:
                return doc
        if not has_vehicle:
            return "vehicle"
        # Check for vehicle docs
        for doc in VEHICLE_DOCS:
            if doc not in doc_types_done:
                return doc
        return "done"
    else:
        raise ValueError(f"Unknown role: {role}")

def clean_pan(text):
    import re
    text = text.strip().upper()
    if not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", text):
        raise ValueError("Enter a valid PAN, like ABCDE1234F")
    return text

def clean_licence(text):
    import re
    text = text.strip().upper()
    if not re.fullmatch(r"[A-Z]{2}[ -]?[0-9]{2}[ -]?[0-9]{4}[ -]?[0-9]{7}", text):
        raise ValueError("Enter a valid driving licence number")
    return text

def clean_plate(text):
    import re
    text = text.upper().replace(" ", "").replace("-", "")
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}", text):
        raise ValueError("Enter a valid vehicle number, like MH12AB1234")
    return text

def clean_college_id(text):
    text = text.strip()
    if not (4 <= len(text) <= 20) or not text.isalnum():
        raise ValueError("College ID must be 4 to 20 letters or digits")
    return text

def profile_status(next_step_value, doc_statuses):
    if next_step_value != "done":
        return "incomplete"

    all_approved = True
    for status in doc_statuses:
        if status == "rejected":
            return "rejected"
        if status != "approved":
            all_approved = False

    return "approved" if all_approved else "pending"
