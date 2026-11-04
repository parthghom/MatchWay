# This file contains the rules for user verification.
# The OCR text and face matching results are provided as input from external services.
# This service manages the state of which verification steps have been successfully passed.

import re
from app.engine.hash_map import HashMap

ALLOWED_EMAIL_DOMAINS = ["college.edu", "college.edu.in"]
PIN_PATTERN = r"\b\d{10}\b"
DL_PATTERN = r"\b[A-Z]{2}[ -]?\d{2}[ -]?\d{4}[ -]?\d{7}\b"
RC_PATTERN = r"\b[A-Z]{2}[ -]?\d{2}[ -]?[A-Z]{1,3}[ -]?\d{4}\b"
REQUIRED_STUDENT_STEPS = ["email", "id_card", "selfie"]
REQUIRED_DRIVER_STEPS = ["licence", "vehicle", "selfie"]

class VerificationService:
    def __init__(self):
        # user_id -> list of passed step names
        self.user_progress = HashMap()

    def _record_step(self, user_id, step):
        try:
            steps = self.user_progress.get(user_id)
        except KeyError:
            steps = []

        # Avoid duplicates
        is_duplicate = False
        for s in steps:
            if s == step:
                is_duplicate = True
                break

        if not is_duplicate:
            steps.append(step)
            self.user_progress.put(user_id, steps)

    def verify_email(self, user_id, email):
        if email.count("@") != 1:
            return {"passed": False, "steps": self.passed_steps(user_id)}

        _, domain = email.split("@")
        if domain.lower() in ALLOWED_EMAIL_DOMAINS:
            self._record_step(user_id, "email")

        return {"passed": domain.lower() in ALLOWED_EMAIL_DOMAINS, "steps": self.passed_steps(user_id)}

    def extract_pin(self, ocr_text):
        match = re.search(PIN_PATTERN, ocr_text)
        return match.group(0) if match else None

    def verify_id_card(self, user_id, ocr_text, current_year):
        pin = self.extract_pin(ocr_text)
        if not pin:
            return {"passed": False, "steps": self.passed_steps(user_id)}

        # Expiry check
        keywords = ["valid till", "valid until", "valid upto", "expiry", "expires"]
        text_lower = ocr_text.lower()

        for kw in keywords:
            idx = text_lower.find(kw)
            if idx != -1:
                lookahead_start = idx + len(kw)
                lookahead_end = lookahead_start + 12
                segment = ocr_text[lookahead_start:lookahead_end]

                year_match = re.search(r"\b(\d{4})\b", segment)
                if year_match:
                    year = int(year_match.group(1))
                    if year < current_year:
                        return {"passed": False, "steps": self.passed_steps(user_id)}
                    break

        self._record_step(user_id, "id_card")
        return {"passed": True, "steps": self.passed_steps(user_id)}

    def verify_licence(self, user_id, ocr_text):
        passed = bool(re.search(DL_PATTERN, ocr_text.upper()))
        if passed:
            self._record_step(user_id, "licence")
        return {"passed": passed, "steps": self.passed_steps(user_id)}

    def verify_vehicle(self, user_id, ocr_text):
        passed = bool(re.search(RC_PATTERN, ocr_text.upper()))
        if passed:
            self._record_step(user_id, "vehicle")
        return {"passed": passed, "steps": self.passed_steps(user_id)}

    def verify_selfie(self, user_id, face_matched):
        passed = bool(face_matched)
        if passed:
            self._record_step(user_id, "selfie")
        return {"passed": passed, "steps": self.passed_steps(user_id)}

    def passed_steps(self, user_id):
        try:
            steps = self.user_progress.get(user_id)
            return steps
        except KeyError:
            return []

    def is_verified_student(self, user_id):
        passed = self.passed_steps(user_id)
        for step in REQUIRED_STUDENT_STEPS:
            found = False
            for p in passed:
                if p == step:
                    found = True
                    break
            if not found:
                return False
        return True

    def is_verified_driver(self, user_id):
        passed = self.passed_steps(user_id)
        for step in REQUIRED_DRIVER_STEPS:
            found = False
            for p in passed:
                if p == step:
                    found = True
                    break
            if not found:
                return False
        return True

    def get_status(self, user_id):
        return {
            "user_id": user_id,
            "steps": self.passed_steps(user_id),
            "student_verified": self.is_verified_student(user_id),
            "driver_verified": self.is_verified_driver(user_id)
        }

    def reset(self, user_id):
        self.user_progress.put(user_id, [])
