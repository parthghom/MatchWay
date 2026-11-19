# Completed trips, newest first, one Stack per person.
# A HashMap finds the person's Stack ("rider:<user_id>" or "driver:<user_id>") in O(1),
# the Stack keeps the newest trip on top, and a second HashMap remembers which trips were
# already written so finishing a ride twice can not add it twice.

import datetime

from app.engine.hash_map import HashMap
from app.engine.stack import Stack

MAX_TRIPS = 50   # per person; older ones fall off the bottom


class TripHistory:
    def __init__(self):
        self.stacks = HashMap()   # "role:user_id" -> Stack of trips
        self.seen = HashMap()     # "role:user_id:trip_id" -> True

    def record(self, role, user_id, trip):
        """Puts a finished trip on top of this person's stack. trip needs an "id"."""
        if not user_id:
            return False
        who = f"{role}:{user_id}"
        mark = f"{who}:{trip['id']}"
        if self.seen.contains(mark):
            return False
        self.seen.put(mark, True)
        if not self.stacks.contains(who):
            self.stacks.put(who, Stack())
        stack = self.stacks.get(who)
        stack.push(trip)
        stack.trim(MAX_TRIPS)
        return True

    def get(self, role, user_id, limit=MAX_TRIPS):
        """This person's trips, newest first."""
        who = f"{role}:{user_id}"
        if not self.stacks.contains(who):
            return []
        return self.stacks.get(who).to_list(limit)


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
