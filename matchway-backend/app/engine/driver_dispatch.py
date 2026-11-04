# DriverDispatcher manages the allocation of drivers to ride requests.
# It follows two primary dispatching rules:
# 1. FIFO at Spots: If drivers are already waiting at the pickup spot, they are
#    assigned on a first-in-first-out (FIFO) basis using a Queue.
# 2. Nearest Driver: If no driver is at the spot, the system identifies all free
#    drivers of the required vehicle type within a radius using a KD-Tree,
#    then selects the closest one using a MinHeap.

from app.engine.hash_map import HashMap
from app.engine.queue import Queue
from app.engine.min_heap import MinHeap
from app.engine.kd_tree import KDTree, haversine_m
from app.models.driver import Driver

class DriverDispatcher:
    def __init__(self):
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

    def find_driver(self, spot_id, lat, lon, vehicle_type, search_radius_m=3000):
        """Finds the best available driver using FIFO or Nearest-Neighbor."""

        # 1. FIRST IN FIRST ASSIGN
        key = f"{spot_id}|{vehicle_type}"
        if self.spot_queues.contains(key):
            queue = self.spot_queues.get(key)
            while not queue.is_empty():
                driver_id = queue.dequeue()
                if self.drivers.contains(driver_id):
                    driver = self.drivers.get(driver_id)
                    if not driver.is_busy:
                        driver.is_busy = True
                        self.drivers.put(driver_id, driver)
                        return driver

        # 2. NEAREST FREE DRIVER
        # Build KDTree from all free drivers of this vehicle type
        kd_tree = KDTree()
        all_driver_ids = self.drivers.keys()
        for d_id in all_driver_ids:
            d = self.drivers.get(d_id)
            if not d.is_busy and d.vehicle_type == vehicle_type:
                kd_tree.insert(d.latitude, d.longitude, d_id)

        if kd_tree.size() == 0:
            return None

        # Search within radius
        nearby = kd_tree.radius_search(lat, lon, search_radius_m)
        if not nearby:
            return None

        # Use MinHeap to find the absolute nearest (though radius_search already sorts)
        heap = MinHeap()
        for dist, d_id in nearby:
            heap.push(dist, d_id)

        # Pop the nearest
        _, best_driver_id = heap.pop()
        driver = self.drivers.get(best_driver_id)
        driver.is_busy = True
        self.drivers.put(best_driver_id, driver)
        return driver

    def release_driver(self, driver_id):
        """Marks a driver as available."""
        if self.drivers.contains(driver_id):
            driver = self.drivers.get(driver_id)
            driver.is_busy = False
            self.drivers.put(driver_id, driver)
