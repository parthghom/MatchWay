# otp.py provides a simple one-time password service for ride verification,
# using a custom HashMap to store and verify codes for specific ride IDs.

import random
from app.engine.hash_map import HashMap

class OTPService:
    def __init__(self):
        # stores ride_id -> code (str)
        self.codes = HashMap()

    def generate(self, ride_id):
        """Creates a 4-digit zero-padded OTP and stores it."""
        code = str(random.randint(0, 9999)).zfill(4)
        self.codes.put(ride_id, code)
        return code

    def verify(self, ride_id, code):
        """Verifies the code, then deletes it if it matches."""
        if not self.codes.contains(ride_id):
            return False

        stored_code = self.codes.get(ride_id)
        if stored_code == code:
            # Delete code after successful verification
            # HashMap has no remove-on-missing, but we check contains first.
            # Our HashMap has a remove() method.
            self.codes.remove(ride_id)
            return True

        return False
