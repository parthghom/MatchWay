# reviews.py manages the reputation of riders AND drivers with an Exponential Moving Average (EMA).
#
#     S_new = ALPHA * stars + (1 - ALPHA) * S_old          (ALPHA = 0.3)
#
# Every review from 1 to 5 stars goes through this formula, so the score is always "based on EMA".
# A newcomer starts at DEFAULT_SCORE (3.0). The latest review weighs 30 %, everything before it
# 70 %, so recent behaviour matters most but one bad day cannot wipe out a long good record.
#
# Safety rules that work next to the score (they do NOT replace it):
# - 1 star: the reviewer and the target are blocked - they are never matched together again.
# - 2 stars: the target's "unsafe" count goes up. At UNSAFE_THRESHOLD the person is flagged unsafe.
#
# Ids used here are stable identities: the user id of the person (or, when no user is known,
# the rider id). That is what lets a rating live on after one ride.

from app.engine.hash_map import HashMap

ALPHA = 0.3
DEFAULT_SCORE = 3.0
UNSAFE_THRESHOLD = 3


def ema(old_score, stars, alpha=ALPHA):
    """One EMA step."""
    return round(alpha * stars + (1 - alpha) * old_score, 4)


class ReviewService:
    def __init__(self):
        # identity -> float (EMA score)
        self.scores = HashMap()
        # identity -> int (how many reviews it received)
        self.counts = HashMap()
        # "a|b" -> True
        self.blocks = HashMap()
        # identity -> int
        self.unsafe_counts = HashMap()

    def submit_review(self, reviewer_id, target_id, stars):
        if isinstance(stars, bool) or not isinstance(stars, int) or stars < 1 or stars > 5:
            raise ValueError("Stars must be an integer between 1 and 5")
        if reviewer_id == target_id:
            raise ValueError("You cannot review yourself")

        # 1. the EMA score (always, for 1 to 5 stars)
        self.scores.put(target_id, ema(self.get_score(target_id), stars))
        self.counts.put(target_id, self.get_count(target_id) + 1)

        # 2. the safety side effects
        if stars == 1:
            self.blocks.put(f"{reviewer_id}|{target_id}", True)
        elif stars == 2:
            self.unsafe_counts.put(target_id, self.unsafe_count(target_id) + 1)

        return self.get_score(target_id)

    def get_score(self, identity):
        if self.scores.contains(identity):
            return self.scores.get(identity)
        return DEFAULT_SCORE

    def get_count(self, identity):
        if self.counts.contains(identity):
            return self.counts.get(identity)
        return 0

    def summary(self, identity):
        """What the profile shows: the score (1 decimal) and how many reviews it is built from."""
        return {"score": round(self.get_score(identity), 1), "count": self.get_count(identity)}

    def is_blocked(self, a, b):
        # Blocked if a blocked b OR b blocked a
        return self.blocks.contains(f"{a}|{b}") or self.blocks.contains(f"{b}|{a}")

    def unsafe_count(self, identity):
        if self.unsafe_counts.contains(identity):
            return self.unsafe_counts.get(identity)
        return 0

    def is_unsafe(self, identity):
        return self.unsafe_count(identity) >= UNSAFE_THRESHOLD
