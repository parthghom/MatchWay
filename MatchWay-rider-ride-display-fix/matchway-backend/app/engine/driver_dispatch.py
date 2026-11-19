# DriverDispatcher manages the allocation of drivers to ride requests.
# It follows two primary dispatching rules:
# 1. FIFO at Spots: If drivers are already waiting at the pickup spot, they are
#    assigned on a first-in-first-out (FIFO) basis using a Queue.
# 2. Nearest Driver: If no driver is at the spot, the system identifies all free
#    drivers of the required vehicle type within a radius using a KD-Tree,
#    then selects the best one using a MinHeap. "Best" = close AND well rated:
#    distance is reduced by a bonus for a high EMA rating (see RATING_METRES_PER_STAR).
#    Drivers rated under MIN_DRIVER_SCORE are not offered rides.

from app.engine.hash_map import HashMap
from app.engine.queue import Queue
from app.engine.min_heap import MinHeap
from app.engine.kd_tree import KDTree, haversine_m
from app.models.driver import Driver

# Driver rating in the nearest-driver choice:
# every rating point above/below the default 3.0 is worth this many metres, so a 5.0 driver that is
# 1.2 km away beats a 3.0 driver that is 200 m away, while a far-away driver still never wins.
RATING_METRES_PER_STAR = 600
DEFAULT_RATING = 3.0
# a driver whose EMA rating fell under this is not offered rides any more
MIN_DRIVER_SCORE = 2.0


class DriverDispatcher:
    def __init__(self):
        # rating_of(driver_id) -> EMA score. RideService plugs its ReviewService in here.
        # While it is None every driver counts the same and only the distance matters.
        self.rating_of = None
        # drivers: driver_id -> Driver
        self.drivers = HashMap()
        # spot_queues: "spot_id|vehicle_type" -> Queue
        self.spot_queues = HashMap()

    def update_driver(self, driver):
        """Stores or replaces the driver state."""
        self.drivers.put(driver.id, driver)

    def arrive_at_spot(self, spot_id, driver_id):
        """Enqueues a driver at a specific pickup spot."""
        if not self.drivers.contains(driver_id):
            raise KeyError(f"Driver {driver_id} is unknown")

        driver = self.drivers.get(driver_id)
        if driver.is_busy:
            return

        key = f"{spot_id}|{driver.vehicle_type}"
        if not self.spot_queues.contains(key):
            self.spot_queues.put(key, Queue())

        queue = self.spot_queues.get(key)
        queue.enqueue(driver_id)

    def set_location(self, driver_id, name, vehicle_type, lat, lon):
        """A driver app reports its live position. A new driver is added; a known one keeps is_busy."""
        if self.drivers.contains(driver_id):
            driver = self.drivers.get(driver_id)
            driver.latitude = lat
            driver.longitude = lon
            driver.name = name or driver.name
            driver.vehicle_type = vehicle_type
        else:
            driver = Driver(id=driver_id, name=name, vehicle_type=vehicle_type, latitude=lat, longitude=lon)
        self.drivers.put(driver_id, driver)
        return driver

    def go_offline(self, driver_id):
        """Takes the driver out, so no new rides are offered to him."""
        if self.drivers.contains(driver_id):
            self.drivers.remove(driver_id)

    def _rating(self, driver_id):
        return self.rating_of(driver_id) if self.rating_of is not None else DEFAULT_RATING

    def find_driver(self, spot_id, lat, lon, vehicle_type, search_radius_m=3000, exclude=None):
        """Finds the best available driver using FIFO or Nearest-Neighbor.
        `exclude` is a list of driver ids that must not be picked (they declined this ride)."""
        exclude = exclude or []

        # 1. FIRST IN FIRST ASSIGN
        key = f"{spot_id}|{vehicle_type}"
        if self.spot_queues.contains(key):
            queue = self.spot_queues.get(key)
            while not queue.is_empty():
                driver_id = queue.dequeue()
                if self.drivers.contains(driver_id) and driver_id not in exclude:
                    driver = self.drivers.get(driver_id)
                    if not driver.is_busy and self._rating(driver_id) >= MIN_DRIVER_SCORE:
                        driver.is_busy = True
                        self.drivers.put(driver_id, driver)
                        return driver

        # 2. NEAREST FREE DRIVER
        # Build KDTree from all free drivers of this vehicle type
        kd_tree = KDTree()
        all_driver_ids = self.drivers.keys()
        for d_id in all_driver_ids:
            d = self.drivers.get(d_id)
            if (not d.is_busy and d.vehicle_type == vehicle_type and d_id not in exclude
                    and self._rating(d_id) >= MIN_DRIVER_SCORE):
                kd_tree.insert(d.latitude, d.longitude, d_id)

        if kd_tree.size() == 0:
            return None

        # Search within radius
        nearby = kd_tree.radius_search(lat, lon, search_radius_m)
        if not nearby:
            return None

        # MinHeap on "distance minus rating bonus": the best mix of close and well-rated comes first.
        # (With no ratings every bonus is 0, so this is just the nearest driver.)
        heap = MinHeap()
        for dist, d_id in nearby:
            bonus = RATING_METRES_PER_STAR * (self._rating(d_id) - DEFAULT_RATING)
            heap.push(dist - bonus, d_id)

        # Pop the best
        _, best_driver_id = heap.pop()
        driver = self.drivers.get(best_driver_id)
        driver.is_busy = True
        self.drivers.put(best_driver_id, driver)
        return driver

    def count_nearby(self, lat, lon, vehicle_type, start_m=2000, step_m=1000, max_m=10000):
        """Counts free drivers of this vehicle type around a point.
        Looks within 2 km first; if there are none it widens by 1 km at a time,
        up to 10 km. Returns (count, radius_m that was used)."""
        kd_tree = KDTree()
        for d_id in self.drivers.keys():
            d = self.drivers.get(d_id)
            if not d.is_busy and d.vehicle_type == vehicle_type and self._rating(d_id) >= MIN_DRIVER_SCORE:
                kd_tree.insert(d.latitude, d.longitude, d_id)

        if kd_tree.size() == 0:
            return 0, max_m

        radius = start_m
        while radius <= max_m:
            found = kd_tree.radius_search(lat, lon, radius)
            if len(found) > 0:
                return len(found), radius
            radius += step_m
        return 0, max_m

    def release_driver(self, driver_id):
        """Marks a driver as available."""
        if self.drivers.contains(driver_id):
            driver = self.drivers.get(driver_id)
            driver.is_busy = False
            self.drivers.put(driver_id, driver)
