# reviews.py manages rider reputation using an Exponential Moving Average (EMA).
# EMA formula: S_new = ALPHA * stars + (1 - ALPHA) * S_old.
# By using a constant ALPHA (0.3), the system gives more weight to the most recent
# review while still retaining memory of past behavior.
#
# Review Logic:
# - 1 Star: Trigger a block between the reviewer and target. Score unchanged.
# - 2 Stars: Increment the target's "unsafe" count. Score unchanged.
# - 3-5 Stars: Update the target's reputation score using EMA.

from app.engine.hash_map import HashMap

ALPHA = 0.3
DEFAULT_SCORE = 3.0
UNSAFE_THRESHOLD = 3

class ReviewService:
    def __init__(self):
        # rider_id -> float
        self.scores = HashMap()
        # "a|b" -> True
        self.blocks = HashMap()
        # rider_id -> int
        self.unsafe_counts = HashMap()

    def submit_review(self, reviewer_id, target_id, stars):
        if not isinstance(stars, int) or stars < 1 or stars > 5:
            raise ValueError("Stars must be an integer between 1 and 5")
        if reviewer_id == target_id:
            raise ValueError("You cannot review yourself")

        if stars == 1:
            self.blocks.put(f"{reviewer_id}|{target_id}", True)
        elif stars == 2:
            count = self.unsafe_counts.get(target_id) if self.unsafe_counts.contains(target_id) else 0
            self.unsafe_counts.put(target_id, count + 1)
        else:
            # EMA update for 3, 4, 5 stars
            old_score = self.scores.get(target_id) if self.scores.contains(target_id) else DEFAULT_SCORE
            new_score = round(ALPHA * stars + (1 - ALPHA) * old_score, 4)
            self.scores.put(target_id, new_score)

    def get_score(self, rider_id):
        if self.scores.contains(rider_id):
            return self.scores.get(rider_id)
        return DEFAULT_SCORE

    def is_blocked(self, a, b):
        # Blocked if a blocked b OR b blocked a
        return self.blocks.contains(f"{a}|{b}") or self.blocks.contains(f"{b}|{a}")

    def unsafe_count(self, rider_id):
        if self.unsafe_counts.contains(rider_id):
            return self.unsafe_counts.get(rider_id)
        return 0

    def is_unsafe(self, rider_id):
        return self.unsafe_count(rider_id) >= UNSAFE_THRESHOLD
